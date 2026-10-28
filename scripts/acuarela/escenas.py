"""Escenas completas de acuarela para la web. Cada función devuelve un Lienzo ya dibujado.

  guirnalda    un tramo de guirnalda de banderines, para repetirlo en horizontal         420 × 130
  bodegon      bodegón de boda rústica (entre la portada y la Agenda)                    1000 × 545
  ramo         un ramo de flores rojas con las alianzas (entre la Agenda y el Transporte)  760 × 420
  almohada     almohada y llave de habitación (Alojamiento)                             640 × 400
  maleta       maleta antigua con pegatinas (Lista de bodas)                            520 × 400
  granadas     par de granadas con hojas (pie de página)                                380 × 220
  alianzas-icono  dos alianzas, icono junto al título «Lista de bodas»                  240 × 170
  almohada-icono  almohada y llave, icono junto al título «Alojamiento»                 300 × 220
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
    """Bodegón de boda rústica, suelto y agrupado (los objetos se solapan): narcisos blancos en un jarrón, vela en
    candelabro turquesa, copa de rosado, tarjeta de menú, tomates cherry, rodajas de naranja, uvas, girasoles en una
    jarra de barro, botella verde oscuro y una porción de tarta."""
    L = Lienzo(1000, 545, 11)
    Y = lambda y: y - 175        # el grupo se pinta en y ≈ 210–720; se sube para no dejar aire arriba
    # sombra suave de la mesa: asienta el grupo
    L.mancha(L.blob(500, Y(668), 470, 34, 14, .05), "#e6d3c1", .32)

    # ---- fondo: botella, girasoles en la jarra, candelabro con la vela y narcisos
    O.botella(L, 880, Y(650), 300)
    for (x, y, r, rot, inc) in [(712, Y(300), 66, 8, .1), (812, Y(372), 52, -14, .3), (640, Y(392), 44, 20, .45)]:
        O.tallo(L, [(x, y + r * .4), (x + L.jit(0, 8), (y + Y(520)) / 2), (735 + L.jit(0, 10), Y(560))], 5, O.PAL["salvia"])
        O.girasol(L, x, y, r, rot, inc)
    O.hojas_tallo(L, 728, Y(470), 92, -40, 34, O.PAL["hoja"], 10)
    O.hojas_tallo(L, 724, Y(500), -84, -30, 30, O.PAL["hoja_clara"], -8)
    O.jarra(L, 735, Y(655), 130)
    copa_y = O.candelero(L, 432, Y(640), 300)
    O.vela(L, 432, copa_y + 8, 190)
    O.tarro_flores(L, 232, Y(640), 140, 104)

    # ---- medio: menú apoyado en el jarrón y copa de rosado
    O.menu(L, 96, Y(560), 100, 138, -12)
    O.copa(L, 566, Y(655), 200)

    # ---- delante: tomates cherry, rodajas de naranja, uvas y la tarta
    for (x, y, r, rot) in [(150, 672, 21, 8), (186, 684, 19, -12), (128, 692, 18, 20), (222, 690, 20, 4), (168, 702, 17, -6)]:
        O.tomate(L, x, Y(y), r, rot)
    O.naranja(L, 360, Y(678), 38)
    O.naranja(L, 430, Y(694), 31)
    O.uvas(L, 612, Y(618), 104, -10)
    O.plato_tarta(L, 790, Y(690), 92)
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


def alianzas_icono():
    L = Lienzo(240, 170, 29)
    O.anillos(L, 122, 92, 56)
    return L


def alianzas_icono_v3():
    """V3: las mismas alianzas con el diamante por fuera del aro."""
    L = Lienzo(240, 190, 29)
    O.anillos(L, 122, 108, 56, diamante_fuera=True)
    return L


def almohada_icono():
    L = Lienzo(300, 220, 37)
    O.almohada(L, 150, 92, 230, 140, -4)
    O.llave(L, 92, 172, 150, 6, etiqueta=False)
    return L


# (ramo, almohada grande, maleta y granadas ya no salen en la V2; se quedan aquí por si se quieren recuperar)
ESCENAS = {"guirnalda": guirnalda, "bodegon": bodegon, "alianzas-icono": alianzas_icono, "almohada-icono": almohada_icono,
           "alianzas-icono-v3": alianzas_icono_v3}
ESCENAS_V1 = {"ramo": ramo, "almohada": almohada, "maleta": maleta, "granadas": granadas}
