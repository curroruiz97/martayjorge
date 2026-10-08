"""
adornos.py · sprite de adornos a pluma (stroke = currentColor).

Símbolos: floritura, floritura-corta, corazon, ramita.
Cada trazo es <path class="l" pathLength="1"> para poder animarlo como las ilustraciones.
"""
import math
from pluma import Lienzo, arco_pts, fnum

ATTRS = 'fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"'


def _simbolo(sid, vb, L, ancho, extra=""):
    o = ['<symbol id="%s" viewBox="%s" %s stroke-width="%s">' % (sid, vb, ATTRS, ancho)]
    for d in L.datos():
        o.append('<path class="l" pathLength="1" d="%s"/>' % d)
    if extra:
        o.append(extra)
    o.append("</symbol>")
    return "\n".join(o)


def _punto(x, y, r):
    return '<circle cx="%s" cy="%s" r="%s" fill="currentColor" stroke="none"/>' % (fnum(x), fnum(y), fnum(r))


def floritura():
    """Onda fina simétrica respecto al centro con un rombo y un punto (como la de la invitación)."""
    L = Lienzo(160, 32, semilla=31, temblor=0.5, escala_pasado=0.3)
    izq = [(4.0, 16.4), (14.0, 12.6), (26.0, 10.2), (40.0, 12.1), (54.0, 18.4), (64.5, 21.6), (72.5, 20.0), (80.0, 16.0)]
    der = [(160 - x, 32 - y) for (x, y) in reversed(izq)]
    L.curva(izq + der[1:], peso="d", tramo=10.0, pasado=(0, 0.2), hueco=(0, 1e9))
    L.linea((80.2, 3.6), (73.6, 16.0), (79.8, 28.6), (86.4, 16.2), (80.2, 3.6), (79.2, 2.4), peso="d",
            pasado=(0, 0.2))
    return _simbolo("floritura", "0 0 160 32", L, "1.4", _punto(80.0, 16.0, 1.8))


def floritura_corta():
    L = Lienzo(96, 24, semilla=32, temblor=0.5, escala_pasado=0.3)
    izq = [(4.0, 12.2), (12.0, 9.6), (21.0, 9.0), (31.0, 12.6), (38.5, 14.6), (43.5, 13.8), (48.0, 12.0)]
    der = [(96 - x, 24 - y) for (x, y) in reversed(izq)]
    L.curva(izq + der[1:], peso="d", tramo=8.0, pasado=(0, 0.2), hueco=(0, 1e9))
    L.linea((48.1, 4.2), (43.6, 12.0), (47.9, 19.8), (52.4, 12.1), (48.1, 4.2), (47.4, 3.2), peso="d",
            pasado=(0, 0.2))
    return _simbolo("floritura-corta", "0 0 96 24", L, "1.3", _punto(48.0, 12.0, 1.4))


def corazon():
    """Corazón a pluma: dos trazos que se cruzan un poco en la punta, y un repaso parcial."""
    L = Lienzo(48, 44, semilla=33, temblor=0.6, escala_pasado=0.5)
    izq = [(24.5, 40.5), (15.0, 31.5), (6.5, 22.0), (4.6, 13.0), (8.4, 6.4), (15.2, 4.6), (21.0, 7.8), (24.0, 13.6)]
    der = [(23.8, 13.4), (27.4, 7.2), (33.4, 4.4), (40.0, 6.6), (43.4, 13.4), (41.4, 22.6), (33.4, 31.4), (23.0, 41.6)]
    L.curva(izq, peso="d", pasado=(0, 0.6), tramo=7.0, hueco=(0, 1e9))
    L.curva(der, peso="d", pasado=(0, 0.6), tramo=7.0, hueco=(0, 1e9))
    # repaso: segunda pasada más fina en el lóbulo izquierdo
    L.curva([(7.6, 21.0), (6.0, 13.6), (9.4, 7.8), (15.0, 6.0)], peso="s", pasado=(0, 0.2), tramo=6.0)
    return _simbolo("corazon", "0 0 48 44", L, "1.8")


def ramita():
    """Ramita de olivo: tallo curvo, hojas lanceoladas alternas con nervio y dos aceitunas."""
    L = Lienzo(120, 48, semilla=34, temblor=0.5, escala_pasado=0.4)
    rng = L.rng
    tallo = [(5.0, 37.0), (30.0, 31.0), (58.0, 26.5), (86.0, 22.0), (113.0, 14.0)]
    L.curva(tallo, peso="d", pasado=(0, 0.6), tramo=14.0, hueco=(0, 1e9))

    def en_tallo(t):
        # interpolación lineal simple sobre los puntos del tallo
        k = min(len(tallo) - 2, int(t * (len(tallo) - 1)))
        u = t * (len(tallo) - 1) - k
        a, b = tallo[k], tallo[k + 1]
        return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), math.atan2(b[1] - a[1], b[0] - a[0])
    hojas = [(0.14, 1, 16), (0.24, -1, 17), (0.36, 1, 18), (0.47, -1, 18), (0.58, 1, 17), (0.69, -1, 16),
             (0.79, 1, 14), (0.88, -1, 12), (0.97, 1, 9)]
    for t, lado, lg in hojas:
        (bx, by), ang = en_tallo(t)
        a = ang - lado * math.radians(42 + rng.uniform(-6, 6))
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux
        anchoh = lg * 0.2
        base = (bx + ux * 1.5, by + uy * 1.5)
        punta = (bx + ux * (lg + 1.5), by + uy * (lg + 1.5))
        m1 = (bx + ux * (lg * 0.5) + nx * anchoh, by + uy * (lg * 0.5) + ny * anchoh)
        m2 = (bx + ux * (lg * 0.5) - nx * anchoh, by + uy * (lg * 0.5) - ny * anchoh)
        # hoja en un trazo: base -> lado 1 -> punta -> lado 2 -> base
        L.trazo([base, m1, punta, m2, (base[0] + ux * 0.4, base[1] + uy * 0.4)], peso="d", suave=True,
                pasado=(0, 0.3), tramo=5.0, hueco=(0, 1e9))
        if lg >= 14:
            L.linea(base, (bx + ux * (lg * 0.78), by + uy * (lg * 0.78)), peso="s", pasado=(0, 0.2))
    # aceitunas
    for t, lado in ((0.42, 1), (0.63, -1)):
        (bx, by), ang = en_tallo(t)
        cx, cy = bx + 3.5, by + lado * 6.5
        L.linea((bx, by), (cx - 0.5, cy - lado * 2.8), peso="s", pasado=(0, 0.2))
        L.circulo(cx, cy, 2.9, ry=3.6, peso="d", solape=20)
    return _simbolo("ramita", "0 0 120 48", L, "1.4")


def sprite():
    o = ['<svg xmlns="http://www.w3.org/2000/svg" style="display:none">']
    o += [floritura(), floritura_corta(), corazon(), ramita()]
    o.append("</svg>")
    return "\n".join(o) + "\n"
