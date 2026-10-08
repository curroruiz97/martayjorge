"""Etapa 4: layout + cronología + SVG de «Marta y Jorge» escritos a pluma.

Salida: nombres.svg.html (fragmento <svg> listo para incrustar) y un JSON con la duración total.
"""
import json
import math
import pickle
import sys

VELOCIDAD = float(sys.argv[1]) if len(sys.argv) > 1 else 7600.0   # unidades/s
GAP_TRAZO = 0.03
GAP_LETRA = 0.035
GAP_PALABRA = 0.14
DUR_MIN = 0.10

# Composición (unidades de fuente; y hacia abajo en el SVG final)
BASE_M = 770       # línea base de «Marta»
BASE_Y = 1120      # línea base de la «y»
BASE_J = 1840      # línea base de «Jorge»
ESCALA_Y = 0.56    # tamaño de la «y»
ROT_Y = -8
DESP_M = -110      # desplazamiento horizontal de cada línea respecto al centro
DESP_J = +110
CENTRO_Y_X = 0     # la «y» va centrada


def largo(poly):
    return sum(math.dist(poly[i], poly[i + 1]) for i in range(len(poly) - 1))


def pdata(poly):
    s = "M%d %d" % (round(poly[0][0]), round(poly[0][1]))
    for p in poly[1:]:
        s += "L%d %d" % (round(p[0]), round(p[1]))
    return s


def main():
    P = pickle.load(open("palabras.pkl", "rb"))
    G = pickle.load(open("glifos.pkl", "rb"))

    # anchos por palabra (avance total) y caja de tinta
    ancho = {k: G[k]["ancho"] for k in G}

    defs, cuerpo = [], []
    cursor = 0.0
    cid = 0
    detalle = []
    posiciones = {
        "Marta": (-ancho["Marta"] / 2 + DESP_M, BASE_M, 1.0, 0),
        "y": (-ancho["y"] * ESCALA_Y / 2 + CENTRO_Y_X, BASE_Y, ESCALA_Y, ROT_Y),
        "Jorge": (-ancho["Jorge"] / 2 + DESP_J, BASE_J, 1.0, 0),
    }
    for palabra in ("Marta", "y", "Jorge"):
        tx, ty, sc, rot = posiciones[palabra]
        cls = {"Marta": "marta", "y": "y", "Jorge": "jorge"}[palabra]
        if rot:
            # rotar alrededor del centro de la «y»
            cx, cy = tx + ancho[palabra] * sc / 2, ty - 120 * sc / ESCALA_Y * 0.45
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
    # caja de dibujo: se ajusta a ojo; unidades del layout
    vb = (-1271, 41, 2420, 2065)
    svg = ('<svg class="nombres__svg" viewBox="%d %d %d %d" aria-hidden="true" focusable="false">'
           "<defs>%s</defs>%s</svg>") % (vb + ("".join(defs), "".join(cuerpo)))
    open("nombres.svg.html", "w", encoding="utf-8").write(svg)
    json.dump({"total": round(total, 2), "velocidad": VELOCIDAD, "viewBox": vb, "strokes": detalle}, open("nombres.json", "w"), indent=1)
    print("SVG %.1f KB · duración de escritura %.2fs · trazos %d" % (len(svg.encode()) / 1024, total, len(detalle)))
    for d in detalle:
        print("  ", d)


if __name__ == "__main__":
    main()
