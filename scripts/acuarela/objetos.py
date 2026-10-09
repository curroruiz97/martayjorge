"""Objetos de acuarela para las ilustraciones de la web (tomates, velas, flores, anillos, maleta…).

Cada función dibuja un objeto en un Lienzo, con su centro en (cx, cy) y un tamaño de referencia. Los colores salen de PAL.
Son dibujos propios (no copian los de ninguna otra web): mismas ideas —una mesa puesta, una boda, un viaje—, trazo propio.
"""
import math

from lib import TINTA, oscurece

PAL = {
    "tomate": "#d63a30", "tomate_osc": "#b3202a", "brillo": "#f7bfae",
    "hoja": "#5f8a34", "hoja_clara": "#8fae57", "hoja_osc": "#46692a",
    "naranja": "#f08a24", "naranja_clara": "#f8b85c", "amarillo": "#f2c230", "amarillo_claro": "#f7dd7e",
    "crema": "#f3e7cb", "crema_osc": "#dcc593", "rosa": "#ec8f94", "rosado": "#f2b6b0", "vino": "#d9737b",
    "turquesa": "#2f8f8a", "turquesa_osc": "#1f6a68", "verde_botella": "#44702f",
    "morado": "#5b3552", "morado_claro": "#8b5a7d", "oro": "#cfa52b", "oro_osc": "#9c7a1d",
    "marron": "#b4814a", "marron_osc": "#7c5226", "azul": "#cfe3ef", "azul_osc": "#5f9bbf", "gris": "#7d6d6a",
    "rojo": "#c3262f", "rojo_osc": "#8f1a22", "carmin": "#a3121d",
}


def _p(cx, cy, r, ang):
    return (cx + r * math.cos(ang), cy + r * math.sin(ang))


# ------------------------------------------------------------------ frutas y verduras
def tomate(L, cx, cy, r, rot=0.0):
    with L.grupo(rot, cx, cy):
        L.mancha(L.blob(cx, cy, r, r * .86, 11, .05), PAL["tomate"], .88)
        L.mancha(L.blob(cx + r * .12, cy + r * .16, r * .78, r * .62, 9, .08), PAL["tomate_osc"], .5)
        L.mancha(L.blob(cx - r * .38, cy - r * .3, r * .26, r * .17, 7, .1, -.5), PAL["brillo"], .6)
        for i in range(5):
            a = -math.pi / 2 + i * 2 * math.pi / 5 + L.jit(0, .12)
            L.mancha(L.petalo(cx, cy - r * .78, a, r * .46, r * .2), PAL["hoja"], .85)
        L.linea(L.blob(cx + L.jit(0, 3), cy + L.jit(0, 3), r * 1.02, r * .89, 11, .04), 2.0)
        L.linea(L.curva([(cx, cy - r * .8), (cx + r * .05, cy - r * 1.0), (cx + r * .14, cy - r * 1.06)]), 2.2)


def granada(L, cx, cy, r, rot=0.0):
    with L.grupo(rot, cx, cy):
        L.mancha(L.blob(cx, cy, r, r * .94, 11, .05), "#c1243a", .88)
        L.mancha(L.blob(cx + r * .15, cy + r * .2, r * .75, r * .66, 9, .08), "#8f1a2b", .5)
        L.mancha(L.blob(cx - r * .36, cy - r * .3, r * .24, r * .16, 7, .1, -.5), "#f3b0b4", .55)
        for i in range(6):
            a = -math.pi / 2 + (i - 2.5) * .5
            L.mancha(L.petalo(cx, cy - r * .86, a, r * .34, r * .15), "#a3132a", .85)
        L.linea(L.blob(cx + L.jit(0, 3), cy + L.jit(0, 3), r * 1.03, r * .96, 11, .04), 2.0)
        L.linea(L.curva([(cx - r * .2, cy - r * .85), (cx, cy - r * 1.0), (cx + r * .2, cy - r * .85)]), 2.0)


def naranja(L, cx, cy, r):
    """Rodaja de naranja."""
    L.mancha(L.blob(cx, cy, r, r * .96, 12, .03), PAL["naranja"], .9)
    L.mancha(L.blob(cx, cy, r * .85, r * .81, 12, .03), PAL["naranja_clara"], .85)
    for i in range(9):
        a = i * 2 * math.pi / 9 + .2
        L.mancha(L.petalo(cx + math.cos(a) * r * .1, cy + math.sin(a) * r * .1, a, r * .72, r * .34, jit=.06), "#f69c2e", .5)
        L.linea(L.curva([_p(cx, cy, r * .08, a), _p(cx, cy, r * .78, a + L.jit(0, .03))]), 1.2, "#b8501a", .7)
    L.linea(L.blob(cx + L.jit(0, 2), cy + L.jit(0, 2), r * 1.02, r * .98, 12, .03), 1.8)


def uvas(L, cx, cy, R, rot=0.0):
    """Racimo de uvas (R = ancho del racimo)."""
    with L.grupo(rot, cx, cy):
        filas = [(-.0, 4), (.2, 3), (.4, 3), (.6, 2), (.8, 1)]
        for k, (dy, n) in enumerate(filas):
            for j in range(n):
                x = cx + (j - (n - 1) / 2) * R * .27 + L.jit(0, R * .02)
                y = cy + dy * R * 1.1
                rr = R * .15
                L.mancha(L.blob(x, y, rr, rr, 8, .06), PAL["morado"], .88)
                L.mancha(L.blob(x - rr * .35, y - rr * .35, rr * .35, rr * .25, 6, .1), "#d9b9d0", .55)
                L.linea(L.blob(x + L.jit(0, 1.5), y + L.jit(0, 1.5), rr * 1.02, rr * 1.02, 8, .05), 1.4)
        L.mancha(L.hoja(cx, cy - R * .05, cx + R * .46, cy - R * .5, R * .34, R * .05), PAL["hoja"], .85)
        L.mancha(L.hoja(cx, cy - R * .05, cx - R * .4, cy - R * .46, R * .3, -R * .04), PAL["hoja_clara"], .85)
        L.linea(L.curva([(cx, cy - R * .05), (cx + R * .22, cy - R * .26), (cx + R * .46, cy - R * .5)]), 1.4)


def queso(L, cx, cy, R, rot=0.0):
    with L.grupo(rot, cx, cy):
        cara = [(cx - R, cy + R * .2), (cx + R, cy - R * .25), (cx + R, cy + R * .15), (cx - R, cy + R * .5)]
        top = [(cx - R, cy + R * .2), (cx + R * .1, cy - R * .5), (cx + R, cy - R * .25)]
        L.mancha(L.suave(cara, True, .25), PAL["amarillo"], .9)
        L.mancha(L.suave(top, True, .25), PAL["amarillo_claro"], .9)
        for (x, y, rr) in [(-.45, .28, .09), (.05, .12, .07), (.55, -.02, .08), (.25, .22, .05)]:
            L.mancha(L.blob(cx + x * R, cy + y * R, rr * R, rr * R * .7, 7, .1), "#d49a1c", .7)
        L.linea(L.suave(cara + [], True, .2), 1.8)
        L.linea(L.suave(top, True, .2), 1.6)


# ------------------------------------------------------------------ mesa
def vela(L, cx, cy, alto, ancho=None, color=None):
    """Vela encendida; (cx, cy) es la base."""
    ancho = ancho or alto * .17
    color = color or PAL["crema"]
    arriba = cy - alto
    d = [(cx - ancho / 2, cy), (cx - ancho / 2 + L.jit(0, 1), arriba + alto * .08), (cx, arriba), (cx + ancho / 2, arriba + alto * .08), (cx + ancho / 2, cy)]
    L.mancha(L.suave(d, True, .3), color, .92)
    L.mancha(L.suave([(cx + ancho * .1, cy), (cx + ancho * .12, arriba + alto * .1), (cx + ancho / 2, arriba + alto * .08), (cx + ancho / 2, cy)], True, .3), PAL["crema_osc"], .55)
    L.mancha(L.petalo(cx, arriba - alto * .02, -math.pi / 2, alto * .22, alto * .11), PAL["amarillo"], .95)
    L.mancha(L.petalo(cx, arriba - alto * .02, -math.pi / 2, alto * .14, alto * .06), "#e8532a", .9)
    L.linea(L.suave(d, True, .25), 1.6)
    L.linea(L.curva([(cx, arriba), (cx + 1, arriba - alto * .04)]), 1.8)


def candelero(L, cx, cy, alto, color=None):
    """Candelero turquesa; (cx, cy) es la base. Devuelve la y de la copa (donde va la vela)."""
    color = color or PAL["turquesa"]
    w = alto * .38
    L.mancha(L.blob(cx, cy - alto * .04, w / 2, alto * .06, 9, .06), color, .9)                       # pie
    L.mancha(L.suave([(cx - alto * .035, cy - alto * .05), (cx - alto * .03, cy - alto * .55), (cx + alto * .03, cy - alto * .55), (cx + alto * .035, cy - alto * .05)], True, .3), color, .9)   # tallo
    L.mancha(L.blob(cx, cy - alto * .32, alto * .075, alto * .03, 8, .08), PAL["turquesa_osc"], .85)  # nudo
    L.mancha(L.suave([(cx - alto * .13, cy - alto * .66), (cx - alto * .05, cy - alto * .55), (cx + alto * .05, cy - alto * .55), (cx + alto * .13, cy - alto * .66)], True, .3), color, .9)   # copa
    L.linea(L.curva([(cx - w / 2, cy - alto * .04), (cx, cy + alto * .02), (cx + w / 2, cy - alto * .04)]), 1.8)
    L.linea(L.curva([(cx - alto * .035, cy - alto * .05), (cx - alto * .03, cy - alto * .55)]), 1.4)
    L.linea(L.curva([(cx - alto * .13, cy - alto * .66), (cx - alto * .05, cy - alto * .55), (cx + alto * .05, cy - alto * .55), (cx + alto * .13, cy - alto * .66)]), 1.6)
    return cy - alto * .66


def copa(L, cx, cy, alto, vino=True):
    """Copa de vino; (cx, cy) es la base."""
    ancho = alto * .36
    base_y = cy
    pie_y = cy - alto * .5
    tope = cy - alto
    L.mancha(L.blob(cx, base_y - alto * .02, ancho * .42, alto * .03, 8, .05), "#dfe6e6", .5)
    if vino:
        d = [(cx - ancho * .5, tope + alto * .3), (cx - ancho * .46, pie_y - alto * .1), (cx, pie_y + alto * .03), (cx + ancho * .46, pie_y - alto * .1), (cx + ancho * .5, tope + alto * .3)]
        L.mancha(L.suave(d, True, .3), PAL["rosa"], .62)
        L.mancha(L.suave([(cx - ancho * .3, tope + alto * .36), (cx, tope + alto * .32), (cx + ancho * .3, tope + alto * .36), (cx + ancho * .2, pie_y - alto * .05), (cx, pie_y), (cx - ancho * .2, pie_y - alto * .05)], True, .3), PAL["vino"], .5)
    bowl = [(cx - ancho * .5, tope), (cx - ancho * .52, tope + alto * .22), (cx - ancho * .44, pie_y - alto * .1), (cx, pie_y + alto * .02), (cx + ancho * .44, pie_y - alto * .1), (cx + ancho * .52, tope + alto * .22), (cx + ancho * .5, tope)]
    L.linea(L.suave(bowl, False, .3), 1.8, "#6f6360")
    L.linea(L.blob(cx, tope, ancho * .5, alto * .03, 8, .03), 1.5, "#6f6360")
    L.linea(L.curva([(cx, pie_y + alto * .02), (cx + L.jit(0, 1), (pie_y + base_y) / 2), (cx, base_y - alto * .03)]), 1.8, "#6f6360")
    L.linea(L.blob(cx, base_y - alto * .02, ancho * .42, alto * .03, 8, .05), 1.6, "#6f6360")


def botella(L, cx, cy, alto, color=None, etiqueta=True):
    """Botella de vidrio verde; (cx, cy) es la base."""
    color = color or PAL["verde_botella"]
    w = alto * .22
    cuello = alto * .34
    d = [(cx - w / 2, cy), (cx - w / 2, cy - alto * .55), (cx - w * .26, cy - alto * .66), (cx - w * .15, cy - alto * .7), (cx - w * .15, cy - alto + alto * .04),
         (cx + w * .15, cy - alto + alto * .04), (cx + w * .15, cy - alto * .7), (cx + w * .26, cy - alto * .66), (cx + w / 2, cy - alto * .55), (cx + w / 2, cy)]
    L.mancha(L.suave(d, True, .18), color, .92)
    L.mancha(L.suave([(cx - w * .32, cy - alto * .05), (cx - w * .32, cy - alto * .55), (cx - w * .2, cy - alto * .62), (cx - w * .2, cy - alto * .05)], True, .3), "#9cc27a", .45)
    L.mancha(L.suave([(cx - w * .16, cy - alto), (cx + w * .16, cy - alto), (cx + w * .16, cy - alto * .94), (cx - w * .16, cy - alto * .94)], True, .1), "#5b3a22", .85)
    if etiqueta:
        L.mancha(L.suave([(cx - w * .42, cy - alto * .1), (cx - w * .42, cy - alto * .36), (cx + w * .42, cy - alto * .36), (cx + w * .42, cy - alto * .1)], True, .1), "#efe2c2", .95)
        L.linea(L.curva([(cx - w * .26, cy - alto * .27), (cx + w * .26, cy - alto * .26)]), 1.2, TINTA, .6)
        L.linea(L.curva([(cx - w * .22, cy - alto * .2), (cx + w * .22, cy - alto * .19)]), 1.2, TINTA, .6)
    L.linea(L.suave(d, True, .18), 1.8)


def plato_tarta(L, cx, cy, R):
    """Plato con tarta de nata y cerezas."""
    L.mancha(L.blob(cx, cy, R, R * .3, 12, .03), "#e6edea", .8)
    L.mancha(L.blob(cx, cy, R * .78, R * .22, 12, .03), "#f6f3ea", .8)
    L.mancha(L.suave([(cx - R * .5, cy - R * .02), (cx - R * .46, cy - R * .34), (cx + R * .46, cy - R * .36), (cx + R * .5, cy - R * .02), (cx, cy + R * .12)], True, .3), "#c9965a", .9)
    L.mancha(L.suave([(cx - R * .46, cy - R * .3), (cx, cy - R * .42), (cx + R * .46, cy - R * .32), (cx + R * .4, cy - R * .22), (cx, cy - R * .2), (cx - R * .4, cy - R * .22)], True, .3), "#f6efe0", .92)
    for x in (-.28, -.04, .22):
        L.mancha(L.blob(cx + x * R, cy - R * .42, R * .085, R * .085, 7, .06), "#c1243a", .92)
        L.mancha(L.blob(cx + x * R - R * .025, cy - R * .45, R * .025, R * .02, 5, .1), "#f7b9bd", .6)
        L.linea(L.curva([(cx + x * R, cy - R * .5), (cx + x * R + R * .05, cy - R * .62)]), 1.2)
    L.linea(L.blob(cx, cy, R * 1.01, R * .31, 12, .03), 1.6)
    L.linea(L.suave([(cx - R * .5, cy - R * .02), (cx - R * .46, cy - R * .34), (cx + R * .46, cy - R * .36), (cx + R * .5, cy - R * .02), (cx, cy + R * .12)], True, .25), 1.6)


def menu(L, cx, cy, w, h, rot=0.0, titulo="Menú"):
    with L.grupo(rot, cx, cy):
        d = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2 + L.jit(0, 2)), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2 + L.jit(0, 2))]
        L.mancha(L.suave(d, True, .08), "#f4ecd9", .95)
        L.mancha(L.suave([(cx + w * .1, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx + w * .1, cy + h / 2)], True, .08), "#ddd0b4", .45)
        L.linea(L.suave(d, True, .05), 1.5)
        L.texto(cx - w * .26, cy - h * .3, titulo, int(h * .18), -4)
        for k in range(5):
            y = cy - h * .12 + k * h * .15
            L.linea(L.curva([(cx - w * .3, y), (cx - w * .05, y + L.jit(0, 1.5)), (cx + w * .28, y + L.jit(0, 1.5))]), 1.1, TINTA, .55)


# ------------------------------------------------------------------ flores
def gerbera(L, cx, cy, r, c1=None, c2=None, rot=0.0):
    c1 = c1 or PAL["rojo"]
    c2 = c2 or PAL["naranja"]
    with L.grupo(rot, cx, cy):
        n = 16
        for i in range(n):
            a = i * 2 * math.pi / n + L.jit(0, .05)
            col = c1 if i % 2 == 0 else c2
            L.mancha(L.petalo(cx, cy, a, r * L.rng.uniform(.92, 1.08), r * .3), col, .8)
        L.mancha(L.blob(cx, cy, r * .26, r * .26, 8, .08), "#4a2a1f", .92)
        L.mancha(L.blob(cx, cy, r * .4, r * .4, 9, .08), PAL["oro"], .45)
        L.punto(cx - r * .06, cy - r * .06, r * .04, "#f2dcc0", .7)


def narciso(L, cx, cy, r, rot=0.0):
    with L.grupo(rot, cx, cy):
        for i in range(6):
            a = i * 2 * math.pi / 6 + .3
            L.mancha(L.petalo(cx, cy, a, r, r * .62, jit=.07), "#f7efd8", .9)
            L.linea(L.petalo(cx, cy, a, r, r * .62, jit=.07), 1.1, "#8a7a5a", .5)
        L.mancha(L.blob(cx, cy, r * .3, r * .3, 8, .08), PAL["naranja"], .92)
        L.mancha(L.blob(cx, cy, r * .2, r * .2, 7, .08), "#d0651a", .6)


def amapola(L, cx, cy, r, rot=0.0):
    """Flor roja sencilla de 5 pétalos redondos."""
    with L.grupo(rot, cx, cy):
        for i in range(5):
            a = i * 2 * math.pi / 5 + L.jit(0, .15)
            L.mancha(L.blob(cx + math.cos(a) * r * .5, cy + math.sin(a) * r * .5, r * .55, r * .5, 8, .08, a), PAL["rojo"], .78)
        L.mancha(L.blob(cx, cy, r * .22, r * .22, 7, .1), "#3b1a1a", .9)
        for i in range(7):
            a = i * 2 * math.pi / 7
            L.punto(cx + math.cos(a) * r * .32, cy + math.sin(a) * r * .32, r * .035, "#2a1414", .8)


def tallo(L, pts, ancho=5, color=None):
    color = color or PAL["hoja"]
    L.trazo_color(L.curva(pts), color, ancho, .88)
    L.linea(L.curva(pts), 1.2, TINTA, .55)


def hojas_tallo(L, x, y, dx, dy, ancho, color=None, curva=0.0):
    color = color or PAL["hoja"]
    L.mancha(L.hoja(x, y, x + dx, y + dy, ancho, curva), color, .85)
    L.linea(L.hoja(x, y, x + dx, y + dy, ancho, curva), 1.4)
    L.linea(L.curva([(x, y), (x + dx * .5, y + dy * .5 + curva * .5), (x + dx * .92, y + dy * .92)]), 1.0, TINTA, .45)


def tarro_flores(L, cx, cy, alto, ancho):
    """Tarro de cristal con narcisos; (cx, cy) es la base del tarro."""
    # tallos
    for k, dx in enumerate((-.3, -.05, .22)):
        tallo(L, [(cx + dx * ancho * .5, cy - alto * .1), (cx + dx * ancho * .6 + L.jit(0, 3), cy - alto * 1.0), (cx + dx * ancho * 1.5, cy - alto * 2.0)], 4)
    for (dx, dy, rr, a) in [(-.5, -2.15, .5, -.2), (.1, -2.35, .56, .1), (.9, -2.08, .46, .35)]:
        narciso(L, cx + dx * ancho, cy + dy * alto, alto * rr, a)
    hojas_tallo(L, cx - ancho * .1, cy - alto * .7, -ancho * .5, -alto * 1.0, alto * .16, PAL["hoja"], 6)
    hojas_tallo(L, cx + ancho * .1, cy - alto * .7, ancho * .55, -alto * .9, alto * .15, PAL["hoja_clara"], -6)
    # tarro
    d = [(cx - ancho / 2, cy - alto * .88), (cx - ancho / 2 - 4, cy - alto * .5), (cx - ancho / 2, cy - alto * .06), (cx + ancho / 2, cy - alto * .06), (cx + ancho / 2 + 4, cy - alto * .5), (cx + ancho / 2, cy - alto * .88)]
    L.mancha(L.suave(d, True, .15), "#cfe3e3", .38)
    L.mancha(L.suave([(cx - ancho * .38, cy - alto * .8), (cx - ancho * .38, cy - alto * .1), (cx - ancho * .25, cy - alto * .1), (cx - ancho * .25, cy - alto * .8)], True, .1), "#ffffff", .0)
    L.linea(L.suave(d, True, .12), 1.8, "#6f7f7d")
    L.linea(L.blob(cx, cy - alto * .88, ancho / 2, alto * .035, 8, .03), 1.5, "#6f7f7d")


# ------------------------------------------------------------------ guirnalda
def banderines(L, x0, x1, y, caida, n, colores=None, tam=None):
    """Guirnalda de banderines: cuerda que cuelga entre (x0, y) y (x1, y) y n banderines."""
    colores = colores or [PAL["amarillo"], PAL["amarillo_claro"], "#f0a73a", PAL["rosado"], PAL["amarillo"]]
    tam = tam or (x1 - x0) / n * .62

    def cuerda(t):
        return (x0 + (x1 - x0) * t, y + caida * 4 * t * (1 - t))

    puntos = [cuerda(i / 24) for i in range(25)]
    L.linea(L.curva(puntos), 1.7, TINTA, .75)
    for i in range(n):
        t = (i + .5) / n
        x, yy = cuerda(t)
        # pendiente de la cuerda para girar el banderín
        xa, ya = cuerda(t - .01)
        xb, yb = cuerda(t + .01)
        ang = math.atan2(yb - ya, xb - xa)
        a = tam * .5
        tri = [(x - a, yy), (x + a, yy), (x + L.jit(0, 2), yy + tam * 1.1)]
        with L.grupo(math.degrees(ang) * .9, x, yy):
            L.mancha(L.suave(tri, True, .12), colores[i % len(colores)], .9)
            L.linea(L.suave(tri, True, .06), 1.3, TINTA, .7)
    for i in range(n + 1):
        t = i / n
        x, yy = cuerda(t)
        L.punto(x, yy, 2.4, TINTA, .8)


# ------------------------------------------------------------------ boda
def anillos(L, cx, cy, r):
    """Dos alianzas de oro entrelazadas y un diamante."""
    for dx, dy, rr in [(-r * .45, r * .1, r), (r * .5, -r * .05, r * .92)]:
        L.trazo_color(L.blob(cx + dx, cy + dy, rr, rr * .96, 14, .025), PAL["oro"], r * .14, .9, rim=PAL["oro_osc"])
        L.linea(L.blob(cx + dx + L.jit(0, 2), cy + dy + L.jit(0, 2), rr * 1.07, rr * 1.03, 14, .025), 1.4, "#6b5210", .6)
        L.linea(L.blob(cx + dx + L.jit(0, 2), cy + dy + L.jit(0, 2), rr * .93, rr * .89, 14, .025), 1.2, "#6b5210", .5)
    # diamante
    dx, dy = cx + r * .72, cy - r * .68
    pts = [(dx - r * .17, dy), (dx - r * .08, dy - r * .14), (dx + r * .09, dy - r * .14), (dx + r * .18, dy), (dx, dy + r * .17)]
    L.mancha(L.suave(pts, True, .05), "#b9cdd6", .9)
    L.mancha(L.suave([(dx - r * .08, dy - r * .14), (dx + r * .09, dy - r * .14), (dx + r * .02, dy)], True, .05), "#eaf3f6", .8)
    L.linea(L.suave(pts, True, .02), 1.5, "#4a5c66")
    L.linea(L.curva([(dx - r * .17, dy), (dx + r * .18, dy)]), 1.1, "#4a5c66")
    L.linea(L.curva([(dx - r * .08, dy - r * .14), (dx, dy + r * .17), (dx + r * .09, dy - r * .14)]), 1.1, "#4a5c66")


def ramo(L, cx, cy, R):
    """Ramo de flores rojas; (cx, cy) es el atado de los tallos y R el ancho de las flores."""
    puntas = [(-.55, -1.05, .34, -.2), (-.12, -1.38, .36, .1), (.38, -1.18, .33, .3), (.72, -.82, .3, -.3), (-.78, -.62, .3, .2), (.1, -.82, .38, -.1)]
    for (dx, dy, rr, a) in puntas:
        tallo(L, [(cx, cy), (cx + dx * R * .5, cy + dy * R * .5), (cx + dx * R, cy + dy * R + R * .1)], 4)
    hojas_tallo(L, cx + R * .08, cy - R * .3, R * .95, -R * .5, R * .3, PAL["hoja_clara"], 10)
    hojas_tallo(L, cx - R * .08, cy - R * .4, -R * 1.0, -R * .3, R * .28, PAL["hoja"], -10)
    for (dx, dy, rr, a) in puntas:
        amapola(L, cx + dx * R, cy + dy * R, R * rr, a)
    # lazo
    L.mancha(L.suave([(cx - R * .14, cy - R * .12), (cx + R * .14, cy - R * .02), (cx + R * .12, cy + R * .1), (cx - R * .14, cy)], True, .1), "#d8d3cd", .9)
    L.linea(L.suave([(cx - R * .14, cy - R * .12), (cx + R * .14, cy - R * .02), (cx + R * .12, cy + R * .1), (cx - R * .14, cy)], True, .1), 1.4)
    L.linea(L.curva([(cx, cy + R * .06), (cx - R * .1, cy + R * .3)]), 1.5)
    L.linea(L.curva([(cx, cy + R * .06), (cx + R * .1, cy + R * .3)]), 1.5)


# ------------------------------------------------------------------ viaje
def maleta(L, cx, cy, w, h, rot=0.0):
    """Maleta antigua de cuero, con correas y esquineros."""
    with L.grupo(rot, cx, cy):
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
        # asa
        L.trazo_color(L.curva([(cx - w * .14, y0 + 2), (cx - w * .12, y0 - h * .16), (cx + w * .12, y0 - h * .16), (cx + w * .14, y0 + 2)]), PAL["marron_osc"], h * .045, .85)
        L.linea(L.curva([(cx - w * .14, y0 + 2), (cx - w * .12, y0 - h * .18), (cx + w * .12, y0 - h * .18), (cx + w * .14, y0 + 2)]), 1.4)
        cuerpo = [(x0, y0 + h * .06), (x0 + w * .03, y0), (x1 - w * .03, y0), (x1, y0 + h * .06), (x1, y1 - h * .06), (x1 - w * .03, y1), (x0 + w * .03, y1), (x0, y1 - h * .06)]
        L.mancha(L.suave(cuerpo, True, .08), PAL["marron"], .9)
        L.mancha(L.suave([(x0, y0 + h * .06), (x0 + w * .03, y0), (x0 + w * .3, y0), (x0 + w * .24, y1), (x0 + w * .03, y1), (x0, y1 - h * .06)], True, .08), "#d8ab6e", .55)
        L.mancha(L.suave([(x1 - w * .22, y0), (x1 - w * .03, y0), (x1, y0 + h * .06), (x1, y1 - h * .06), (x1 - w * .03, y1), (x1 - w * .22, y1)], True, .08), PAL["marron_osc"], .5)
        # correas verticales
        for fx in (.2, .8):
            L.mancha(L.suave([(x0 + w * fx - w * .04, y0), (x0 + w * fx + w * .04, y0), (x0 + w * fx + w * .04, y1), (x0 + w * fx - w * .04, y1)], True, .05), PAL["marron_osc"], .78)
            L.linea(L.curva([(x0 + w * fx - w * .04, y0), (x0 + w * fx - w * .04, y1)]), 1.1, TINTA, .55)
            L.linea(L.curva([(x0 + w * fx + w * .04, y0), (x0 + w * fx + w * .04, y1)]), 1.1, TINTA, .55)
        # franja central y cierre
        L.linea(L.curva([(x0, cy - h * .06), (x1, cy - h * .06)]), 1.4, TINTA, .55)
        L.mancha(L.suave([(cx - w * .05, cy - h * .1), (cx + w * .05, cy - h * .1), (cx + w * .05, cy + h * .04), (cx - w * .05, cy + h * .04)], True, .1), PAL["oro"], .95)
        L.linea(L.suave([(cx - w * .05, cy - h * .1), (cx + w * .05, cy - h * .1), (cx + w * .05, cy + h * .04), (cx - w * .05, cy + h * .04)], True, .1), 1.3, "#6b5210")
        # esquineros
        for sx, sy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            ax = 1 if sx == x0 else -1
            ay = 1 if sy == y0 else -1
            c = [(sx, sy), (sx + ax * w * .1, sy), (sx + ax * w * .1, sy + ay * h * .03), (sx + ax * w * .03, sy + ay * h * .03), (sx + ax * w * .03, sy + ay * h * .12), (sx, sy + ay * h * .12)]
            L.mancha(L.suave(c, True, .05), PAL["oro_osc"], .85)
        L.linea(L.suave(cuerpo, True, .06), 2.0)


def almohada(L, cx, cy, w, h, rot=0.0):
    with L.grupo(rot, cx, cy):
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
        pts = [(x0 + w * .02, y0 + h * .12), (x0 + w * .3, y0 - h * .03), (cx + w * .05, y0 + h * .04), (x1 - w * .05, y0 - h * .05), (x1, y0 + h * .3), (x1 - w * .02, cy + h * .1),
               (x1 + w * .01, y1 - h * .15), (x1 - w * .3, y1 + h * .03), (cx, y1 - h * .04), (x0 + w * .25, y1 + h * .02), (x0 - w * .01, y1 - h * .2), (x0 + w * .02, cy)]
        L.mancha(L.suave(pts, True, .3), PAL["azul"], .92)
        L.mancha(L.blob(x1 - w * .12, y1 - h * .15, w * .13, h * .2, 8, .15), PAL["azul_osc"], .6)
        L.mancha(L.blob(x0 + w * .1, y0 + h * .2, w * .1, h * .17, 8, .15), PAL["azul_osc"], .5)
        L.mancha(L.blob(cx + w * .15, cy, w * .22, h * .17, 8, .15), "#a9cce2", .5)
        L.linea(L.suave([(p[0] + L.jit(0, 2), p[1] + L.jit(0, 2)) for p in pts], True, .3), 1.5, "#4d6e82", .75)


def llave(L, cx, cy, largo, rot=0.0, numero="1005"):
    """Llave antigua con etiqueta; (cx, cy) es el centro de la anilla."""
    with L.grupo(rot, cx, cy):
        r = largo * .16
        L.trazo_color(L.blob(cx, cy, r, r, 10, .03), PAL["oro"], r * .55, .92, rim=PAL["oro_osc"])
        L.linea(L.blob(cx, cy, r * 1.2, r * 1.2, 10, .03), 1.5, "#6b5210", .7)
        L.linea(L.blob(cx, cy, r * .78, r * .78, 10, .03), 1.3, "#6b5210", .6)
        L.trazo_color(L.curva([(cx + r * 1.1, cy), (cx + largo * .9, cy + L.jit(0, 1))]), PAL["oro"], r * .38, .92, rim=PAL["oro_osc"])
        for k, f in enumerate((.72, .85)):
            L.trazo_color(L.curva([(cx + largo * f, cy), (cx + largo * f, cy + r * (.9 if k == 0 else .7))]), PAL["oro"], r * .34, .92, rim=PAL["oro_osc"])
        L.linea(L.curva([(cx + r * 1.1, cy - r * .2), (cx + largo * .9, cy - r * .2)]), 1.2, "#6b5210", .6)
        # etiqueta colgando de un hilo
        L.linea(L.curva([(cx, cy + r * 1.1), (cx - largo * .08, cy + largo * .22), (cx - largo * .1, cy + largo * .32)]), 1.3, TINTA, .7)
        tag = [(cx - largo * .2, cy + largo * .3), (cx + largo * .04, cy + largo * .28), (cx + largo * .06, cy + largo * .46), (cx - largo * .18, cy + largo * .48)]
        with L.grupo(-12, cx - largo * .07, cy + largo * .38):
            L.mancha(L.suave(tag, True, .05), "#d3e4ee", .95)
            L.linea(L.suave(tag, True, .03), 1.3, "#4d6e82", .8)
            L.texto(cx - largo * .17, cy + largo * .42, numero, int(largo * .1), 0)
