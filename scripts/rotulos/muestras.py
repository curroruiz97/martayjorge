"""Hoja de muestras del rotulado a pincel seco (para revisar antes de integrar).

Uso: python3 scripts/rotulos/muestras.py salida.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import pincel
import piezas

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PUB = os.path.join(RAIZ, 'public')
ANCHO = 1200


def lino(w, h):
    """Fondo de lino como en la web (textura multiplicada sobre el crema)."""
    tex = Image.open(os.path.join(PUB, 'assets/img/lino.webp')).convert('RGB').resize((256, 256), Image.LANCZOS)
    t = np.asarray(tex, np.float32) / 255
    reps = (h // 256 + 1, w // 256 + 1, 1)
    t = np.tile(t, reps)[:h, :w]
    base = np.array([251, 249, 241], np.float32) / 255
    return Image.fromarray((t * base * 255).astype(np.uint8), 'RGB').convert('RGBA')


def fuente(nombre, tam):
    return ImageFont.truetype(os.path.join(PUB, 'assets/fonts', nombre), tam)


def foto_con_bordes(ruta, ancho, prop=6 / 5, semilla=31):
    im = Image.open(ruta).convert('RGBA')
    w, h = im.size
    alto_c = int(w / prop)
    y0 = int((h - alto_c) * 0.55)
    im = im.crop((0, y0, w, y0 + alto_c)).resize((ancho, int(ancho / prop)), Image.LANCZOS)
    b = int(ancho * 0.09)
    sup = piezas.borde_tira(semilla=semilla).resize((ancho, b), Image.LANCZOS).split()[3]
    inf = piezas.borde_tira(semilla=semilla + 1, invertir=True).resize((ancho, b), Image.LANCZOS).split()[3]
    a = Image.new('L', im.size, 255)
    a.paste(sup, (0, 0))
    a.paste(inf, (0, im.height - b))
    im.putalpha(a)
    return im


def main(salida):
    filas = []
    leyenda = fuente('playfair-display-latin-400-italic.woff2', 30)
    rotulo_txt = fuente('covered-by-your-grace-latin-400-normal.woff2', 30)
    variantes = (('A · más seco (más estrías y bordes rotos)', 'rotulo-seco'),
                 ('B · intermedio', 'rotulo'),
                 ('C · más cargado (casi lleno; textura en los finales)', 'rotulo-cargado'))
    for titulo, est in variantes:
        filas.append(('txt', titulo))
        a, _ = pincel.rotular(['AGENDA'], 72, estilo=est, semilla=3)
        n, _ = pincel.rotular(['MARTA Y JORGE'], 72, estilo=est, semilla=5,
                              tinta=lambda li, ci, ch: pincel.NEGRO if ch == 'Y' else pincel.ROJO_LADRILLO)
        filas.append(('img', [a.imagen(), n.imagen()]))
    filas.append(('txt', 'Botón con pincelada · fotos de lado a lado con el borde a pincel seco'))
    boton = piezas.pincelada_boton().resize((380, 95), Image.LANCZOS)
    d = ImageDraw.Draw(boton)
    d.text((190, 50), 'CONFIRMAR ASISTENCIA', font=rotulo_txt, fill=(251, 248, 241, 255), anchor='mm')
    filas.append(('img', [boton]))
    fotos = [foto_con_bordes(os.path.join(PUB, 'assets/img/hero-vertical-740.webp'), 560),
             foto_con_bordes(os.path.join(PUB, 'assets/img/playa-840.webp'), 560, semilla=37)]
    filas.append(('img', fotos))

    alto = 40
    for tipo, cont in filas:
        alto += 60 if tipo == 'txt' else max(i.height for i in cont) + 30
    hoja = lino(ANCHO, alto)
    dib = ImageDraw.Draw(hoja)
    y = 30
    for tipo, cont in filas:
        if tipo == 'txt':
            dib.text((40, y + 10), cont, font=leyenda, fill=(90, 75, 69, 255))
            y += 60
        else:
            total = sum(i.width for i in cont) + 30 * (len(cont) - 1)
            x = (ANCHO - total) // 2
            for i in cont:
                hoja.alpha_composite(i, (x, y + (max(j.height for j in cont) - i.height) // 2))
                x += i.width + 30
            y += max(i.height for i in cont) + 30
    hoja.convert('RGB').save(salida)
    print(salida, hoja.size)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'muestras-rotulado.png')
