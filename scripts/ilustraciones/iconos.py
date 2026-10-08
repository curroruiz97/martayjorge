"""
iconos.py · sprite de iconos a mano alzada (rejilla 48x48, stroke=currentColor, trazo 2).

Ids: coche, autocar, cama, pin, regalo, maleta, copiar, check, flecha-abajo,
     corazon, avion, anillos.
Temblor muy contenido para que sigan leyéndose nítidos a 20-32 px.
"""
import math
from pluma import Lienzo, arco_pts

ATTRS = ('viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" '
         'stroke-linecap="round" stroke-linejoin="round"')


def _L(semilla):
    L = Lienzo(48, 48, semilla=semilla, temblor=0.32, escala_pasado=0.35)
    L.HUECO = {"c": (0.0, 1e9), "d": (0.0, 1e9), "s": (0.0, 1e9)}
    return L


def _sim(sid, L):
    o = ['<symbol id="%s" %s>' % (sid, ATTRS)]
    for d in L.datos():
        o.append('<path d="%s"/>' % d)
    o.append("</symbol>")
    return "\n".join(o)


def redondeado(x0, y0, x1, y1, r, n=3):
    """Rectángulo con esquinas redondeadas como polilínea cerrada."""
    pts = []
    pts += arco_pts(x1 - r, y0 + r, r, r, 90, 0, n=n)
    pts += arco_pts(x1 - r, y1 - r, r, r, 0, -90, n=n)
    pts += arco_pts(x0 + r, y1 - r, r, r, -90, -180, n=n)
    pts += arco_pts(x0 + r, y0 + r, r, r, 180, 90, n=n)
    return pts + [pts[0]]


def coche():
    L = _L(41)
    cuerpo = [(9.2, 32.0), (5.0, 32.0), (5.2, 26.0), (7.4, 23.6), (12.5, 22.6), (17.2, 15.4), (30.5, 15.2),
              (36.4, 22.4), (41.2, 23.6), (43.2, 26.4), (43.0, 32.0), (39.0, 32.0)]
    L.trazo(cuerpo, peso="d", suave=False)
    L.linea((19.4, 32.0), (28.6, 32.0), peso="d")
    L.circulo(14.3, 32.3, 4.4, peso="d", solape=12)
    L.circulo(33.9, 32.3, 4.4, peso="d", solape=12)
    L.linea((14.0, 22.4), (35.2, 22.3), peso="d")
    L.linea((24.4, 16.2), (24.2, 22.0), peso="d")
    return _sim("coche", L)


def autocar():
    L = _L(42)
    L.trazo(redondeado(4.5, 11.5, 43.5, 35.0, 3.2), peso="d", suave=False)
    L.linea((5.0, 22.8), (43.0, 22.6), peso="d")
    for x in (13.5, 22.5, 31.5):
        L.linea((x, 12.2), (x + 0.1, 22.4), peso="d")
    L.linea((37.6, 23.2), (37.6, 34.4), peso="d")
    L.circulo(13.0, 35.5, 3.6, peso="d", solape=10)
    L.circulo(33.0, 35.5, 3.6, peso="d", solape=10)
    L.linea((5.2, 29.5), (8.5, 29.5), peso="d")
    return _sim("autocar", L)


def cama():
    L = _L(43)
    L.linea((6.0, 39.5), (6.0, 13.0), peso="d")
    L.linea((42.0, 39.5), (42.0, 23.5), peso="d")
    L.linea((6.2, 33.2), (41.8, 33.2), peso="d")
    L.linea((6.2, 27.0), (41.8, 27.0), peso="d")
    L.trazo(redondeado(9.5, 19.5, 20.5, 26.4, 2.6), peso="d", suave=False)
    L.curva([(22.0, 26.6), (24.0, 22.2), (30.0, 21.0), (41.6, 21.6)], peso="d")
    return _sim("cama", L)


def pin():
    L = _L(44)
    gota = [(24.0, 43.0)]
    gota += [(18.6, 34.6), (14.0, 27.4)] + arco_pts(24.0, 19.0, 11.0, 11.0, 212, -32, n=12)[1:-1] + \
            [(34.0, 27.4), (29.4, 34.6), (24.2, 43.2)]
    L.trazo(gota, peso="d", suave=True, pasado=(0, 0.4))
    L.circulo(24.0, 19.0, 4.3, peso="d", solape=10)
    return _sim("pin", L)


def regalo():
    L = _L(45)
    L.trazo([(9.0, 22.4), (9.0, 42.0), (39.0, 42.0), (39.0, 22.4)], peso="d", suave=False)
    L.trazo(redondeado(6.5, 15.5, 41.5, 22.4, 1.6), peso="d", suave=False)
    L.linea((24.0, 15.8), (24.0, 41.6), peso="d")
    L.curva([(24.0, 15.4), (19.0, 9.2), (14.0, 8.4), (13.2, 12.6), (17.6, 15.2), (23.6, 15.6)], peso="d")
    L.curva([(24.4, 15.6), (30.2, 15.0), (34.6, 12.4), (33.8, 8.2), (28.8, 9.0), (24.2, 15.0)], peso="d")
    return _sim("regalo", L)


def maleta():
    L = _L(46)
    L.trazo(redondeado(7.5, 16.0, 40.5, 40.5, 3.4), peso="d", suave=False)
    L.linea((18.0, 15.8), (18.4, 10.2), (29.6, 10.2), (30.0, 15.8), peso="d")
    L.linea((15.5, 16.6), (15.5, 39.8), peso="d")
    L.linea((32.5, 16.6), (32.5, 39.8), peso="d")
    return _sim("maleta", L)


def copiar():
    L = _L(47)
    L.trazo(redondeado(10.0, 16.0, 32.0, 40.0, 3.0), peso="d", suave=False)
    L.trazo([(16.0, 12.2)] + arco_pts(19.0, 11.0, 3.0, 3.0, 180, 90, n=3)[1:] +
            [(35.0, 8.0)] + arco_pts(35.0, 11.0, 3.0, 3.0, 90, 0, n=3)[1:] + [(38.0, 29.0)] +
            arco_pts(35.0, 29.0, 3.0, 3.0, 0, -90, n=3)[1:] + [(32.4, 32.0)], peso="d", suave=False)
    return _sim("copiar", L)


def check():
    L = _L(48)
    L.linea((9.5, 25.0), (19.6, 35.0), (39.0, 13.0), peso="d")
    return _sim("check", L)


def flecha_abajo():
    L = _L(49)
    L.curva([(24.0, 7.0), (24.8, 20.0), (24.0, 39.0)], peso="d")
    L.linea((13.6, 29.0), (24.0, 39.6), (34.4, 28.8), peso="d")
    return _sim("flecha-abajo", L)


def corazon():
    L = _L(50)
    izq = [(24.4, 41.0), (14.0, 31.6), (6.4, 22.4), (5.0, 14.4), (8.8, 8.2), (15.2, 6.8), (21.0, 9.6), (24.0, 15.0)]
    der = [(23.8, 14.8), (27.2, 9.2), (33.0, 6.6), (39.4, 8.4), (43.0, 14.6), (41.4, 22.8), (33.8, 31.6), (23.4, 41.6)]
    L.curva(izq, peso="d", pasado=(0, 0.3))
    L.curva(der, peso="d", pasado=(0, 0.3))
    return _sim("corazon", L)


def avion():
    """Avión de papel (el mismo de la ruta), apuntando arriba a la derecha."""
    L = _L(51)
    a = math.radians(-28)
    ca, sa = math.cos(a), math.sin(a)

    def T(p):
        x, y = p
        return (24 + x * ca - y * sa, 25 + x * sa + y * ca)
    N, A, B, C, K = (19.0, 0.0), (-17.5, -11.0), (-9.0, 0.8), (-14.5, 10.2), (-6.6, 5.4)
    L.linea(T(N), T(A), T(B), T(C), T((N[0] - 0.4, N[1] + 0.3)), peso="d")
    L.linea(T((N[0] - 1.2, 0.1)), T(B), peso="d")
    L.linea(T((N[0] - 3.6, 1.0)), T(K), T(B), peso="d")
    return _sim("avion", L)


def anillos():
    L = _L(52)
    c1, c2, r = (18.5, 29.0), (29.5, 29.0), 10.2
    # entrelazados: cruces en (24, 20.4) y (24, 37.6). El anillo 2 pasa por detrás arriba
    # (hueco hacia 123 grados) y el anillo 1 por detrás abajo (hueco hacia -57 grados).
    L.trazo(arco_pts(c1[0], c1[1], r, r, -45, -45 + 336, n=30), peso="d", suave=True)
    L.trazo(arco_pts(c2[0], c2[1], r, r, 136, 136 + 336, n=30), peso="d", suave=True)
    # brillante sobre el primer anillo
    L.linea((15.2, 18.6), (18.5, 13.4), (21.8, 18.6), (18.5, 20.2), (15.2, 18.6), peso="d")
    return _sim("anillos", L)


def sprite():
    o = ['<svg xmlns="http://www.w3.org/2000/svg" style="display:none">']
    o += [coche(), autocar(), cama(), pin(), regalo(), maleta(), copiar(), check(), flecha_abajo(),
          corazon(), avion(), anillos()]
    o.append("</svg>")
    return "\n".join(o) + "\n"
