"""
rutas.py · ruta discontinua con lazo en forma de corazón + avioncito de papel.

Estructura (la usa el JS de la web):
  <path id="ruta">  UN solo trazo continuo, sin subtrazos, discontinuo (stroke-dasharray).
                    Sin pathLength: getTotalLength()/getPointAtLength() en unidades del viewBox.
                    Sentido: iglesia -> palomar (izquierda -> derecha / arriba -> abajo).
  <g id="avion">    avión de papel CENTRADO EN (0,0), apuntando a +X, SIN transform.
"""
import math
import random
from pluma import TINTA, trazado, fnum

PAPEL_CLARO = "#fbf8f1"
GUIONES = "9 6.5 7 7 10.5 6 6.5 7.5 8 6"


def _mano(pts, semilla, amp=0.6):
    """Leve temblor sobre los puntos de paso (los extremos y la punta del corazón quedan fijos)."""
    rng = random.Random(semilla)
    out = []
    for i, (x, y) in enumerate(pts):
        if i in (0, len(pts) - 1):
            out.append((x, y))
        else:
            out.append((x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)))
    return out


def _ruta_d(pts, esquinas):
    return trazado(pts, set(esquinas))


def avion():
    """Avión de papel centrado en el origen, morro hacia +X (unas 30 x 18 unidades)."""
    N = (15.5, 0.0)       # morro
    A = (-14.5, -9.0)     # punta trasera del ala de arriba
    B = (-7.5, 0.6)       # pliegue central (muesca trasera)
    C = (-12.0, 8.4)      # punta trasera del ala de abajo
    K = (-5.6, 4.4)       # quilla
    f = lambda p: "%s %s" % (fnum(p[0]), fnum(p[1]))
    o = ['<g id="avion" stroke="%s" stroke-linecap="round" stroke-linejoin="round">' % TINTA]
    o.append('<path fill="%s" stroke="none" d="M%sL%sL%sL%sZ"/>' % (PAPEL_CLARO, f(N), f(A), f(B), f(C)))
    # contorno en un trazo, con un pequeño pasado en el morro
    o.append('<path fill="none" stroke-width="1.9" d="M%sL%sL%sL%sL%s"/>' % (
        f((N[0] + 0.9, N[1] - 0.25)), f(A), f(B), f(C), f((N[0] - 0.4, N[1] + 0.3))))
    # pliegue y quilla
    o.append('<path fill="none" stroke-width="1.3" d="M%sL%s"/>' % (f((N[0] - 1.0, 0.1)), f(B)))
    o.append('<path fill="none" stroke-width="1.1" d="M%sL%sL%s"/>' % (f((N[0] - 3.0, 0.9)), f(K), f(B)))
    # sombra del ala de abajo
    o.append('<path fill="none" stroke-width=".8" d="M-8.4 5.6l3.6-2.6M-4.4 4.2l3.8-2.4M-.6 2.9l3.4-1.9"/>')
    o.append("</g>")
    return "\n".join(o)


def _svg(w, h, d, titulo):
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d">' % (w, h)]
    o.append("<title>%s</title>" % titulo)
    o.append('<path id="ruta" fill="none" stroke="%s" stroke-width="2.1" stroke-linecap="round" '
             'stroke-linejoin="round" stroke-dasharray="%s" d="%s"/>' % (TINTA, GUIONES, d))
    o.append(avion())
    o.append("</svg>")
    return "\n".join(o) + "\n"


def horizontal():
    """viewBox 800 x 170. De izquierda a derecha; corazón hacia el primer tercio."""
    pts = [
        (20.0, 108.0), (62.0, 101.5), (112.0, 106.0), (164.0, 117.0), (206.0, 123.5), (238.0, 124.0),
        (258.0, 119.0),
        (271.0, 111.0),                      # punta del corazón (entrada, subiendo)
        (287.0, 97.0), (300.5, 80.0), (305.0, 63.0), (298.0, 50.5), (284.5, 47.5), (274.5, 55.0),
        (270.5, 66.0),                       # hendidura (pico)
        (266.0, 55.0), (255.0, 47.0), (241.5, 49.5), (233.5, 62.5), (237.5, 81.0), (252.0, 98.0),
        (271.0, 111.0),                      # punta (salida, bajando)
        (289.0, 126.0), (318.0, 134.5), (366.0, 133.0), (428.0, 122.0), (497.0, 113.5), (566.0, 117.0),
        (628.0, 124.5), (684.0, 119.5), (734.0, 110.0), (776.0, 104.0),
    ]
    pts = _mano(pts, 8, amp=0.5)
    pts[7] = pts[21] = (271.0, 111.0)
    d = _ruta_d(pts, [14])
    return _svg(800, 170, d, "Ruta de la iglesia de San Pablo al Palomar")


def vertical():
    """viewBox 170 x 560. De arriba abajo; corazón hacia el primer tercio."""
    pts = [
        (86.0, 18.0), (91.0, 50.0), (79.0, 88.0), (58.0, 132.0), (42.0, 176.0), (36.5, 214.0),
        (42.0, 240.0), (59.0, 252.0), (80.0, 248.5),
        (100.0, 236.0),                      # punta del corazón (entrada)
        (115.0, 222.0), (128.5, 205.0), (133.0, 188.0), (126.0, 175.5), (112.5, 172.5), (102.5, 180.0),
        (99.5, 191.0),                       # hendidura
        (95.0, 180.0), (84.0, 172.0), (70.5, 174.5), (62.5, 187.5), (66.5, 206.0), (81.0, 223.0),
        (100.0, 236.0),                      # punta (salida)
        (115.0, 251.0), (126.0, 274.0), (122.0, 308.0), (105.0, 347.0), (89.0, 390.0), (90.0, 440.0),
        (97.0, 484.0), (90.0, 516.0), (86.0, 540.0),
    ]
    pts = _mano(pts, 11, amp=0.45)
    pts[9] = pts[23] = (100.0, 236.0)
    d = _ruta_d(pts, [16])
    return _svg(170, 560, d, "Ruta de la iglesia de San Pablo al Palomar")
