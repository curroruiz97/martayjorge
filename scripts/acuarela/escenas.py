"""Escenas completas de acuarela para la web. Cada función devuelve un Lienzo ya dibujado.

  guirnalda    un tramo de guirnalda de banderines, para repetirlo en horizontal         420 × 130
  bodegon      una mesa puesta (entre la portada y la Agenda)                            1000 × 720
  ramo         un ramo de flores rojas con las alianzas (entre la Agenda y el Transporte)  760 × 420
  almohada     almohada y llave de habitación (Alojamiento)                             640 × 400
  maleta       maleta antigua con pegatinas (Lista de bodas)                            520 × 400
  granadas     par de granadas con hojas (pie de página)                                380 × 220
"""
import math

import objetos as O
from lib import Lienzo, TINTA


def guirnalda():
    """Un tramo de guirnalda que se repite en horizontal (los extremos de la cuerda quedan a la misma altura)."""
    L = Lienzo(420, 130, 7)
    O.banderines(L, 0, 420, 16, 54, 5, tam=50)
    return L


def bodegon():
    L = Lienzo(1000, 720, 11)

    # ---- grupo izquierdo: tarro con narcisos, menú y tomates
    O.tarro_flores(L, 200, 500, 150, 112)
    O.menu(L, 58, 480, 104, 142, -14)
    O.tomate(L, 138, 626, 54, 8)
    O.tomate(L, 262, 646, 46, -10)

    # ---- centro: vela en candelero turquesa, copa, naranjas y uvas
    copa_y = O.candelero(L, 452, 580, 330)
    O.vela(L, 452, copa_y + 8, 205)
    O.copa(L, 590, 580, 210)
    O.naranja(L, 392, 666, 40)
    O.naranja(L, 508, 678, 33)
    O.uvas(L, 622, 630, 112, -8)

    # ---- derecha: gerberas, botella y tarta
    for (x, y, r, c1, c2, rot) in [(770, 270, 78, "#c3262f", "#f08a24", 10), (872, 350, 60, "#f08a24", "#c3262f", -12), (835, 202, 48, "#c3262f", "#f2c230", 0)]:
        O.tallo(L, [(x, y + r * .5), (x + L.jit(0, 10), y + 190), (790 + L.jit(0, 12), 580)], 5)
        O.gerbera(L, x, y, r, c1, c2, rot)
    O.hojas_tallo(L, 800, 500, 80, -66, 32, O.PAL["hoja"], 8)
    O.hojas_tallo(L, 795, 540, -86, -52, 32, O.PAL["hoja_clara"], -8)
    O.botella(L, 944, 630, 290)
    O.plato_tarta(L, 800, 682, 96)
    return L


def ramo():
    L = Lienzo(760, 420, 23)
    O.ramo(L, 210, 330, 150)
    O.anillos(L, 560, 220, 110)
    return L


def almohada():
    L = Lienzo(700, 470, 31)
    O.almohada(L, 345, 165, 360, 230, -4)
    O.llave(L, 250, 352, 270, 8)
    return L


def maleta():
    L = Lienzo(520, 400, 41)
    O.maleta(L, 250, 215, 330, 220, -5)
    # pegatinas
    with L.grupo(-12, 140, 250):
        L.mancha(L.blob(140, 250, 28, 28, 9, .05), "#c1243a", .85)
        L.linea(L.curva([(130, 247), (140, 238), (150, 247), (140, 262), (130, 247)]), 1.6, "#fff", .0)
    with L.grupo(10, 345, 290):
        L.mancha(L.blob(345, 290, 30, 24, 9, .06), "#f2c230", .85)
        L.linea(L.blob(345, 290, 31, 25, 9, .05), 1.4, TINTA, .7)
    # etiqueta colgada del asa
    L.linea(L.curva([(262, 92), (300, 120), (330, 146)]), 1.4, TINTA, .7)
    with L.grupo(12, 345, 182):
        d = [(300, 142), (392, 146), (388, 222), (296, 218)]
        L.mancha(L.suave(d, True, .05), "#f4ecd9", .95)
        L.linea(L.suave(d, True, .04), 1.4)
        L.texto(312, 176, "luna", 26, 0)
        L.texto(314, 208, "de miel", 26, 0)
    return L


def granadas():
    L = Lienzo(420, 230, 53)
    O.hojas_tallo(L, 190, 120, 110, -70, 34, O.PAL["hoja"], 8)
    O.hojas_tallo(L, 175, 120, -100, -60, 32, O.PAL["hoja_clara"], -8)
    O.hojas_tallo(L, 200, 130, 40, -96, 26, O.PAL["hoja_osc"], 4)
    O.granada(L, 120, 150, 66, -8)
    O.granada(L, 262, 164, 54, 14)
    return L


ESCENAS = {"guirnalda": guirnalda, "bodegon": bodegon, "ramo": ramo, "almohada": almohada, "maleta": maleta, "granadas": granadas}
