"""Etapa 1: glifos de «Marta», «y», «Jorge» en Caveat 700 -> contornos (unidades de fuente),
máscara raster y esqueleto. Salida: pickle con todo + imagen de depuración."""
import pickle
import sys

import numpy as np
import uharfbuzz as hb
from fontTools.pens.basePen import decomposeQuadraticSegment
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw
from skimage.morphology import skeletonize

TTF = "caveat700.ttf"
ESC = 0.6  # píxeles por unidad de fuente para el raster (em = 600 px)
PAD = 40   # margen del raster en px

font = TTFont(TTF)
gs = font.getGlyphSet()
order = font.getGlyphOrder()

blob = hb.Blob.from_file_path(TTF)
hbfont = hb.Font(hb.Face(blob))


def shape(texto):
    buf = hb.Buffer()
    buf.add_str(texto)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, {"kern": True, "liga": False})
    out = []
    x = 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append({"gid": info.codepoint, "name": order[info.codepoint], "x": x + pos.x_offset, "y": pos.y_offset, "adv": pos.x_advance})
        x += pos.x_advance
    return out, x


def contornos(glyphname):
    """Lista de contornos (listas de puntos en unidades de fuente, y hacia arriba) y path SVG (y hacia arriba)."""
    rec = DecomposingRecordingPen(gs)
    gs[glyphname].draw(rec)
    cs, cur, pen = [], [], (0, 0)
    for op, args in rec.value:
        if op == "moveTo":
            cur = [args[0]]; pen = args[0]
        elif op == "lineTo":
            cur.append(args[0]); pen = args[0]
        elif op == "qCurveTo":
            pts = list(args)
            if pts[-1] is None:  # contorno cerrado sin punto on-curve
                pts = pts[:-1]
            for cp, p in decomposeQuadraticSegment(pts):
                p0 = cur[-1]
                for i in range(1, 11):
                    t = i / 10
                    cur.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cp[0] + t * t * p[0],
                                (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cp[1] + t * t * p[1]))
        elif op == "curveTo":
            p0 = cur[-1]; c1, c2, p = args
            for i in range(1, 15):
                t = i / 14
                a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
                cur.append((a * p0[0] + b * c1[0] + c * c2[0] + d * p[0], a * p0[1] + b * c1[1] + c * c2[1] + d * p[1]))
        elif op in ("closePath", "endPath"):
            if cur:
                cs.append(cur)
            cur = []
    sp = SVGPathPen(gs, ntos=lambda v: ("%.1f" % v).rstrip("0").rstrip("."))
    gs[glyphname].draw(sp)
    return cs, sp.getCommands()


def rasterizar(cs):
    xs = [p[0] for c in cs for p in c]; ys = [p[1] for c in cs for p in c]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w = int((x1 - x0) * ESC) + 2 * PAD; h = int((y1 - y0) * ESC) + 2 * PAD
    total = None
    for c in cs:
        m = Image.new("1", (w, h), 0)
        ImageDraw.Draw(m).polygon([((px - x0) * ESC + PAD, (y1 - py) * ESC + PAD) for px, py in c], fill=1)
        total = m if total is None else ImageChops.logical_xor(total, m)
    arr = np.ascontiguousarray(np.array(total.convert("L")) > 0)
    # origen: (unidades) -> (px): px = (u - x0)*ESC + PAD ; py = (y1 - u)*ESC + PAD
    return arr, (x0, y1)


def main():
    res = {}
    for palabra in ("Marta", "y", "Jorge"):
        glifos, ancho = shape(palabra)
        lista = []
        for g in glifos:
            cs, d = contornos(g["name"])
            arr, org = rasterizar(cs)
            sk = skeletonize(arr)
            dist_max = None
            lista.append({**g, "contornos": cs, "d": d, "mask": arr, "skel": sk, "org": org})
            print(palabra, g["name"], "x=%d adv=%d" % (g["x"], g["adv"]), "raster", arr.shape, "esqueleto px:", int(sk.sum()))
        res[palabra] = {"glifos": lista, "ancho": ancho}
    pickle.dump(res, open("glifos.pkl", "wb"))
    # imagen de depuración: máscara en gris + esqueleto en rojo
    filas = []
    for palabra, v in res.items():
        for g in v["glifos"]:
            m = g["mask"]; s = g["skel"]
            rgb = np.zeros(m.shape + (3,), dtype=np.uint8) + 255
            rgb[m] = (205, 205, 205)
            rgb[s] = (200, 30, 30)
            filas.append(Image.fromarray(rgb))
    H = max(i.height for i in filas)
    W = sum(i.width for i in filas) + 10 * len(filas)
    sheet = Image.new("RGB", (W, H), (255, 255, 255))
    x = 0
    for i in filas:
        sheet.paste(i, (x, 0)); x += i.width + 10
    sheet.save("debug_esqueletos.png")
    print("hoja", sheet.size)


main()
