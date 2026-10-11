"""
rutas.py · ruta discontinua que serpentea entre la iglesia y el Palomar + avioncito de papel.
(La V1 llevaba un lazo en forma de corazón y una versión horizontal: siguen en la etiqueta git v1.)

Estructura (la usa el JS de la web):
  <path id="ruta">  UN solo trazo continuo, sin subtrazos, discontinuo (stroke-dasharray).
                    Sin pathLength: getTotalLength()/getPointAtLength() en unidades del viewBox.
                    Sentido: iglesia -> palomar (izquierda -> derecha / arriba -> abajo).
  <g id="avion">    avión de papel CENTRADO EN (0,0), apuntando a +X, SIN transform.
"""
import math
import random
from pluma import TINTA, ROJO, trazado, fnum

PAPEL_CLARO = "#fbf8f1"
GUIONES = "9 6.5 7 7 10.5 6 6.5 7.5 8 6"


def _mano(pts, semilla, amp=0.6):
    """Leve temblor sobre los puntos de paso (los extremos quedan fijos)."""
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
    o = ['<g id="avion" stroke="%s" stroke-linecap="round" stroke-linejoin="round">' % ROJO]
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


def _svg(w, h, d, titulo, grosor=2.1):
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d">' % (w, h)]
    o.append('<path id="ruta" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" '
             'stroke-linejoin="round" stroke-dasharray="%s" d="%s"/>' % (ROJO, grosor, GUIONES, d))
    o.append(avion())
    o.append("</svg>")
    return "\n".join(o) + "\n"


def vertical():
    """viewBox 220 x 560. De arriba abajo: un caminito que serpentea en cuatro curvas amplias (sin corazón; V2)."""
    pts = [
        (110.0, 18.0), (140.0, 48.0), (176.0, 88.0), (182.0, 126.0), (152.0, 160.0), (88.0, 190.0),
        (44.0, 226.0), (42.0, 266.0), (86.0, 296.0), (148.0, 322.0), (182.0, 358.0), (178.0, 398.0),
        (134.0, 428.0), (72.0, 452.0), (46.0, 484.0), (68.0, 514.0), (108.0, 540.0),
    ]
    pts = _mano(pts, 11, amp=0.8)
    d = _ruta_d(pts, [])
    return _svg(220, 560, d, "Ruta de la iglesia de San Pablo al Palomar", grosor=2.3)
