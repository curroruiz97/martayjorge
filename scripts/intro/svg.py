"""Etapa 4: composición + cronología + SVG de «Marta y Jorge» escritos a pluma.

Salida: nombres.svg.html (fragmento <svg> listo para incrustar) y nombres.json con la duración total.
La composición (tamaños, desplazamientos y cajas) se calcula con las medidas reales de la tinta de cada palabra,
así que sirve para cualquier tipografía: basta con ajustar las constantes de «Composición».
"""
import json
import math
import pickle
import sys

VELOCIDAD = float(sys.argv[1]) if len(sys.argv) > 1 else 11000.0   # unidades/s de la punta de la pluma
GAP_TRAZO = 0.03
GAP_LETRA = 0.045
GAP_PALABRA = 0.12
DUR_MIN = 0.08

# ---- Composición: una sola línea «MARTA   Y   JORGE», con las palabras muy separadas (como en la referencia) ----
# (unidades de fuente, em = 1024; cada constante se puede cambiar con una variable de entorno del mismo nombre)
import os
def _e(n, d): return float(os.environ.get(n, d))
TRACK = _e("TRACK", 55)              # espacio añadido entre letras (la letra de referencia va algo abierta)
GAP_PAL = _e("GAP_PAL", 330)         # hueco entre palabras
ESCALA_Y = _e("ESCALA_Y", 1.0)       # tamaño de la «Y» respecto a las palabras
MARGEN = _e("MARGEN", 40)            # margen de la caja de dibujo alrededor de la tinta


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
    orden = ("Marta", "y", "Jorge")
    escala = {"Marta": 1.0, "y": ESCALA_Y, "Jorge": 1.0}
    caja = {k: tinta(G, k) for k in orden}                    # (x0, x1, y0, y1) con la y hacia arriba
    ancho_tinta = {k: (caja[k][1] - caja[k][0]) * escala[k] + TRACK * (len(P[k]) - 1) * escala[k] for k in orden}

    # x donde empieza la tinta de cada palabra (a la izquierda del todo = 0); luego se centra el conjunto
    x_ini, cursor_x = {}, 0.0
    for k in orden:
        x_ini[k] = cursor_x
        cursor_x += ancho_tinta[k] + GAP_PAL
    total_ancho = cursor_x - GAP_PAL
    desp = -total_ancho / 2

    defs, cuerpo, detalle = [], [], []
    cursor = 0.0
    cid = 0
    extremos = {"x0": 1e9, "x1": -1e9, "y0": 1e9, "y1": -1e9}
    for palabra in orden:
        sc = escala[palabra]
        x0 = caja[palabra][0]
        tx = desp + x_ini[palabra] - x0 * sc                   # la tinta de la palabra arranca en x_ini
        cls = {"Marta": "marta", "y": "y", "Jorge": "jorge"}[palabra]
        cuerpo.append('<g class="pal pal--%s" transform="translate(%.0f 0) scale(%s %s)">' % (cls, tx, sc, -sc))
        for i, g in enumerate(P[palabra]):
            cid += 1
            cp = "cp%d" % cid
            defs.append('<path id="g%d" d="%s"/><clipPath id="%s"><use href="#g%d"/></clipPath>' % (cid, g["d"], cp, cid))
            cuerpo.append('<g transform="translate(%d 0)">' % (g["x"] + TRACK * i))
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
    # caja de dibujo = la tinta de toda la línea (alto de las tres palabras) + margen
    y_arriba = max(caja[k][3] * escala[k] for k in orden)
    y_abajo = min(caja[k][2] * escala[k] for k in orden)
    xmin = desp - MARGEN
    xmax = desp + total_ancho + MARGEN
    ymin = -y_arriba - MARGEN                                  # en el SVG la y va hacia abajo
    ymax = -y_abajo + MARGEN
    vb = (round(xmin), round(ymin), round(xmax - xmin), round(ymax - ymin))
    svg = ('<svg class="nombres__svg" viewBox="%d %d %d %d" aria-hidden="true" focusable="false">'
           "<defs>%s</defs>%s</svg>") % (vb + ("".join(defs), "".join(cuerpo)))
    open("nombres.svg.html", "w", encoding="utf-8").write(svg)
    json.dump({"total": round(total, 2), "velocidad": VELOCIDAD, "viewBox": vb, "relacion_alto_ancho": round(vb[3] / vb[2], 4), "strokes": detalle}, open("nombres.json", "w"), indent=1)
    print("SVG %.1f KB · viewBox %s · alto/ancho %.3f · duración de escritura %.2fs · trazos %d" % (len(svg.encode()) / 1024, vb, vb[3] / vb[2], total, len(detalle)))


if __name__ == "__main__":
    main()
