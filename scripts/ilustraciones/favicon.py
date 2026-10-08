"""
favicon.py · favicon 64x64: lazo en forma de corazón (el de la ruta) con su avioncito.

Trazo grueso para que se lea a 16 px. Tinta #2b2a28 sobre transparente; en modo
oscuro del navegador cambia a crema para no desaparecer sobre la pestaña oscura.
"""
from pluma import TINTA, trazado, fnum

CREMA = "#f5f0e4"


def svg():
    # lazo: entra desde abajo a la izquierda, dibuja el corazón y sale hacia arriba a la derecha
    pts = [(5.0, 55.0), (14.0, 53.5), (24.0, 50.0), (31.0, 45.0),        # entrada hacia la punta
           (38.0, 38.0), (45.5, 28.0), (47.5, 18.5), (43.5, 11.0), (36.0, 9.5), (31.0, 14.0),
           (29.0, 20.0),                                                   # hendidura (pico)
           (26.5, 13.5), (20.5, 9.0), (13.0, 10.5), (9.0, 18.0), (11.5, 28.0), (19.0, 38.0),
           (31.0, 45.0),                                                   # punta (salida)
           (41.0, 50.5), (50.0, 51.5)]
    d = trazado(pts, {10})
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">']
    o.append('<style>.t{stroke:%s}.f{fill:%s}@media (prefers-color-scheme:dark){.t{stroke:%s}.f{fill:%s}}</style>'
             % (TINTA, TINTA, CREMA, CREMA))
    o.append('<path class="t" fill="none" stroke-width="4.6" stroke-linecap="round" stroke-linejoin="round" d="%s"/>' % d)
    # avioncito al final del lazo (triángulo relleno: a 16 px solo se distingue como una punta)
    o.append('<path class="f" d="M62 49.5L50.6 44.4L53.2 51.2L50.8 57.4Z"/>')
    o.append("</svg>")
    return "\n".join(o) + "\n"
