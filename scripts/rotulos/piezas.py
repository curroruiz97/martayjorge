"""Piezas hechas con el mismo pincel: bordes de foto (máscaras), aguada de la entrada y pincelada de botón."""
import math

import numpy as np

import pincel
from pincel import Lienzo, ESTILOS, BLANCO, ROJO_LADRILLO

# Pincel ancho para bordes y fondos: las medidas van en «anchos de pincel»
ESTILOS['brocha'] = dict(ancho=1.0, cerdas=90, carga=1.5, recorrido=9.0, fin=(0.35, 0.55), seco=0.6,
                         umbral=(0.16, 0.66), suavidad=0.07, densidad=2.6, temblor=0.0)
ESTILOS['brocha-cargada'] = dict(ancho=1.0, cerdas=90, carga=2.1, recorrido=14.0, fin=(0.6, 0.8), seco=0.4,
                                 umbral=(0.14, 0.6), suavidad=0.08, densidad=3.0, temblor=0.0)


def _ondulada(x0, x1, y, amp, rng, n=7):
    """Puntos de una pasada casi horizontal con una ondulación suave."""
    xs = np.linspace(x0, x1, n)
    fase = rng.uniform(0, math.tau)
    return [(x, y + amp * math.sin(fase + 2.2 * i / (n - 1) * math.pi) + rng.normal(0, amp * 0.3)) for i, x in enumerate(xs)]


def _pasadas(lz, est, rng, ancho, alto, y_c, brocha, n, color, dir_x=1):
    """n pasadas de brocha a lo largo de la anchura, solapadas, alrededor de la altura y_c."""
    x = -0.08 * ancho
    while x < ancho:
        largo = rng.uniform(0.35, 0.7) * ancho
        y = y_c + rng.uniform(-0.12, 0.12) * brocha
        pts = _ondulada(x, x + largo, y, 0.08 * brocha, rng)
        if dir_x < 0:
            pts = pts[::-1]
        lz.trazo(pts, color, est, rng, brocha * rng.uniform(0.85, 1.1), tipo='c')
        x += largo * rng.uniform(0.45, 0.7)


def borde_tira(ancho=1200, alto=120, semilla=31, invertir=False):
    """Tira para el borde superior de una foto: arriba transparente, abajo opaca, en medio pinceladas
    secas horizontales (el borde rasgado). Con invertir=True sirve para el borde inferior."""
    rng = np.random.RandomState(semilla)
    est = ESTILOS['brocha']
    lz = Lienzo(ancho, alto, ss=2, semilla_papel=semilla, densidad=est['densidad'])
    base = np.zeros((alto, ancho), np.float32)
    base[int(alto * 0.78):, :] = 1.0
    lz.relleno(base, BLANCO)
    _pasadas(lz, est, rng, ancho, alto, alto * 0.62, alto * 0.42, 6, BLANCO)
    _pasadas(lz, est, rng, ancho, alto, alto * 0.42, alto * 0.3, 6, BLANCO, dir_x=-1)
    im = lz.imagen(granulado=False, oscurecer=False)
    if invertir:
        im = im.transpose(method=1)  # FLIP_TOP_BOTTOM
    return im


def borde_caja(ancho=800, alto=1000, semilla=41):
    """Máscara de cuatro lados para una foto en caja (proporción fija)."""
    rng = np.random.RandomState(semilla)
    est = ESTILOS['brocha']
    lz = Lienzo(ancho, alto, ss=2, semilla_papel=semilla, densidad=est['densidad'])
    m = int(min(ancho, alto) * 0.07)
    base = np.zeros((alto, ancho), np.float32)
    base[m:alto - m, m:ancho - m] = 1.0
    lz.relleno(base, BLANCO)
    b = min(ancho, alto) * 0.09
    for y in (m * 0.9, alto - m * 0.9):
        _pasadas(lz, est, rng, ancho, alto, y, b, 4, BLANCO)
    # laterales: pasadas verticales (se pintan como horizontales en coordenadas giradas)
    for x in (m * 0.9, ancho - m * 0.9):
        yv = -0.06 * alto
        while yv < alto:
            largo = rng.uniform(0.35, 0.7) * alto
            pts = [(x + rng.normal(0, 0.06 * b), yy) for yy in np.linspace(yv, yv + largo, 7)]
            lz.trazo(pts, BLANCO, est, rng, b * rng.uniform(0.85, 1.1), tipo='c')
            yv += largo * rng.uniform(0.45, 0.7)
    return lz.imagen(granulado=False, oscurecer=False)


def aguada(ancho=600, alto=1800, semilla=53):
    """Máscara de la aguada que «pinta» la foto: tercio de arriba opaco, en medio un frente de agua
    rasgado, tercio de abajo transparente. Se desplaza con mask-position (ver css/intro.css)."""
    rng = np.random.RandomState(semilla)
    est = ESTILOS['brocha-cargada']
    lz = Lienzo(ancho, alto, ss=2, semilla_papel=semilla, densidad=est['densidad'])
    base = np.zeros((alto, ancho), np.float32)
    base[: int(alto * 0.46), :] = 1.0
    lz.relleno(base, BLANCO)
    b = alto * 0.075
    for k in range(4):
        _pasadas(lz, est, rng, ancho, alto, alto * (0.47 + 0.035 * k), b * (1 - 0.15 * k), 4, BLANCO, dir_x=1 if k % 2 else -1)
    return lz.imagen(granulado=False, oscurecer=False)


def pincelada_boton(ancho=760, alto=190, semilla=61, color=ROJO_LADRILLO):
    """Fondo de botón: dos pasadas de pincel cargado; la zona central (bajo el texto) queda llena."""
    rng = np.random.RandomState(semilla)
    est = ESTILOS['brocha-cargada']
    lz = Lienzo(ancho, alto, ss=3, semilla_papel=semilla, densidad=est['densidad'])
    base = np.zeros((alto, ancho), np.float32)
    yy, xx = np.mgrid[0:alto, 0:ancho]
    base[((xx - ancho / 2) / (ancho * 0.4)) ** 2 + ((yy - alto / 2) / (alto * 0.26)) ** 2 < 1] = 0.6
    lz.relleno(base, color)
    for y, b, d in ((alto * 0.47, alto * 0.62, 1), (alto * 0.55, alto * 0.5, -1)):
        pts = _ondulada(ancho * 0.05, ancho * 0.95, y, 0.05 * alto, rng, n=5)
        lz.trazo(pts if d > 0 else pts[::-1], color, est, rng, b, tipo='c')
    return lz.imagen(oscurecer=False)
