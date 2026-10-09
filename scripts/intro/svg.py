"""Etapa 4: composición + cronología + SVG de «Marta y Jorge» escritos a pluma.

Salida: nombres.svg.html (fragmento <svg> listo para incrustar) y nombres.json con la duración total.
La composición (tamaños, desplazamientos y cajas) se calcula con las medidas reales de la tinta de cada palabra,
así que sirve para cualquier tipografía: basta con ajustar las constantes de «Composición».
"""
import json
import math
import pickle
import sys

VELOCIDAD = float(sys.argv[1]) if len(sys.argv) > 1 else 10000.0  # unidades/s de la punta de la pluma
GAP_TRAZO = 0.02
GAP_LETRA = 0.02
GAP_PALABRA = 0.10
DUR_MIN = 0.08

# ---- Composición (unidades de fuente, em = 1000; en el SVG la «y» va hacia abajo) ----
import os
def _e(n, d): return float(os.environ.get(n, d))
ESCALA_Y = _e("ESCALA_Y", 0.6)   # tamaño de la «y» respecto a las palabras
ROT_Y = _e("ROT_Y", -8)           # grados
SANGRIA_J = _e("SANGRIA_J", 120)  # «Jorge» queda alineado a la derecha de «Marta», recogido esta cantidad
X_Y = _e("X_Y", 420)              # centro de la «y» respecto al centro de «Marta»
HUECO_1 = _e("HUECO_1", 70)       # aire entre la base de «Marta» y lo más alto de la «y»
HUECO_2 = _e("HUECO_2", -120)       # aire entre lo más bajo de la «y» y lo más alto de «Jorge»
MARGEN = _e("MARGEN", 40)         # margen de la caja de dibujo alrededor de la tinta


def largo(poly):
    return sum(math.dist(poly[i], poly[i + 1]) for i in range(len(poly) - 1))


def pdata(poly):
    s = "M%d %d" % (round(poly[0][0]), round(poly[0][1]))
    for p in poly[1:]:
        s += "L%d %d" % (round(p[0]), round(p[1]))
    return s


def tinta(G, palabra):
    xs, ys = [], []
    for g in G[palabra]["glifos"]:
        for c in g["contornos"]:
            for (x, y) in c:
                xs.append(g["x"] + x); ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)   # y hacia arriba


def main():
    P = pickle.load(open("palabras.pkl", "rb"))
    G = pickle.load(open("glifos.pkl", "rb"))
    bm = tinta(G, "Marta"); by = tinta(G, "y"); bj = tinta(G, "Jorge")
    ancho_m = bm[1] - bm[0]; ancho_j = bj[1] - bj[0]

    # --- Marta: línea base en 0; centrada en x = 0 ---
    base_m = 0.0
    tx_m = -(bm[0] + bm[1]) / 2
    # --- y: reducida y girada, entre las dos líneas ---
    arriba_y = base_m + (-bm[2]) + HUECO_1             # parte alta de la tinta de la «y» (en el SVG, y hacia abajo)
    base_y = arriba_y + by[3] * ESCALA_Y               # su línea base
    abajo_y = base_y - by[2] * ESCALA_Y
    tx_y = X_Y - (by[0] + by[1]) / 2 * ESCALA_Y
    # --- Jorge: alineado a la derecha de Marta (con sangría) ---
    base_j = abajo_y + HUECO_2 + bj[3]
    der_j = ancho_m / 2 - SANGRIA_J
    tx_j = der_j - bj[1]

    posiciones = {
        "Marta": (tx_m, base_m, 1.0, 0),
        "y": (tx_y, base_y, ESCALA_Y, ROT_Y),
        "Jorge": (tx_j, base_j, 1.0, 0),
    }
    defs, cuerpo, detalle = [], [], []
    cursor = 0.0
    cid = 0
    for palabra in ("Marta", "y", "Jorge"):
        tx, ty, sc, rot = posiciones[palabra]
        cls = {"Marta": "marta", "y": "y", "Jorge": "jorge"}[palabra]
        if rot:
            # se gira alrededor del centro de la tinta de la «y»
            cx = tx + (by[0] + by[1]) / 2 * sc
            cy = ty - (by[2] + by[3]) / 2 * sc
            tr = "rotate(%s %.0f %.0f) translate(%.0f %.0f) scale(%s %s)" % (rot, cx, cy, tx, ty, sc, -sc)
        else:
            tr = "translate(%.0f %.0f) scale(1 -1)" % (tx, ty)
        cuerpo.append('<g class="pal pal--%s" transform="%s">' % (cls, tr))
        for g in P[palabra]:
            cid += 1
            cp = "cp%d" % cid
            defs.append('<path id="g%d" d="%s"/><clipPath id="%s"><use href="#g%d"/></clipPath>' % (cid, g["d"], cp, cid))
            cuerpo.append('<g transform="translate(%d 0)">' % g["x"])
            cuerpo.append('<g clip-path="url(#%s)">' % cp)
            fin_glifo = cursor
            for t in g["trazos"]:
                L = largo(t)
                dur = max(DUR_MIN, L / VELOCIDAD)
                cuerpo.append('<path class="tz" pathLength="1" stroke-width="%d" style="--d:%.2fs;--t:%.2fs" d="%s"/>' % (round(g["w"]), cursor, dur, pdata(t)))
                detalle.append((palabra, g["name"], round(cursor, 2), round(dur, 2)))
                cursor += dur + GAP_TRAZO
                fin_glifo = cursor - GAP_TRAZO
            cuerpo.append("</g>")
            cuerpo.append('<use class="rl" href="#g%d" style="--d:%.2fs"/>' % (cid, max(0, fin_glifo - 0.06)))
            cuerpo.append("</g>")
            cursor += GAP_LETRA - GAP_TRAZO
        cuerpo.append("</g>")
        cursor += GAP_PALABRA - GAP_LETRA
    total = cursor

    # caja de dibujo = tinta de las tres palabras (con la «y» girada) + margen
    def caja_y():
        c = math.cos(math.radians(ROT_Y)); s = math.sin(math.radians(ROT_Y))
        x0 = tx_y + by[0] * ESCALA_Y; x1 = tx_y + by[1] * ESCALA_Y
        y0 = base_y - by[3] * ESCALA_Y; y1 = base_y - by[2] * ESCALA_Y
        cx = tx_y + (by[0] + by[1]) / 2 * ESCALA_Y; cy = base_y - (by[2] + by[3]) / 2 * ESCALA_Y
        pts = [(x, y) for x in (x0, x1) for y in (y0, y1)]
        rot = [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]
        return min(p[0] for p in rot), max(p[0] for p in rot), min(p[1] for p in rot), max(p[1] for p in rot)
    cy_ = caja_y()
    xmin = min(tx_m + bm[0], tx_j + bj[0], cy_[0]) - MARGEN
    xmax = max(tx_m + bm[1], tx_j + bj[1], cy_[1]) + MARGEN
    ymin = min(base_m - bm[3], cy_[2], base_j - bj[3]) - MARGEN
    ymax = max(base_m - bm[2], cy_[3], base_j - bj[2]) + MARGEN
    vb = (round(xmin), round(ymin), round(xmax - xmin), round(ymax - ymin))
    svg = ('<svg class="nombres__svg" viewBox="%d %d %d %d" aria-hidden="true" focusable="false">'
           "<defs>%s</defs>%s</svg>") % (vb + ("".join(defs), "".join(cuerpo)))
    open("nombres.svg.html", "w", encoding="utf-8").write(svg)
    json.dump({"total": round(total, 2), "velocidad": VELOCIDAD, "viewBox": vb, "relacion_alto_ancho": round(vb[3] / vb[2], 4), "strokes": detalle}, open("nombres.json", "w"), indent=1)
    print("SVG %.1f KB · viewBox %s · alto/ancho %.3f · duración de escritura %.2fs · trazos %d" % (len(svg.encode()) / 1024, vb, vb[3] / vb[2], total, len(detalle)))


if __name__ == "__main__":
    main()
