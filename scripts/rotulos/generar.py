"""Genera el rotulado a pincel de acuarela de la web y lo coloca en public/index.html.

Estilo (segunda vuelta de la V2, el de la invitación de referencia que mandaron los novios, más legible):
pincel de acuarela fino «con gracia» (pincel.ESTILOS['acuarela-gracia']) en rojo acuarela; los títulos de sección
llevan un subrayado a mano. La primera vuelta (pincel seco grueso) sigue disponible en pincel.ESTILOS['rotulo'].

Uso:  python3 scripts/rotulos/generar.py
Salidas (public/assets/rotulos/):
  <título>.webp                 títulos de sección (misma altura de mayúscula en todos: 104 px, nítidos en móviles
                                3× y en pantallas 2×; en CSS la mayúscula mide como mucho 44 px)
  nombres.webp                  «MARTA y JORGE» de la portada (se pinta trazo a trazo con una máscara SVG)
  fecha.webp                    «8 DE MAYO DE 2027» de la portada
  borde-sup / borde-inf / borde-4 / aguada .webp   máscaras de las fotos (blanco con alfa)
  pincelada-boton.webp          fondo de los botones principales
En public/index.html reescribe lo que hay entre <!-- rotulo:ID --> y <!-- /rotulo:ID --> (imágenes de los títulos,
SVG de los nombres) y el --rn (proporción de los nombres) de la portada. Es determinista: mismas semillas → mismos
ficheros.
"""
import io
import math
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw

import pincel
import piezas

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PUB = os.path.join(RAIZ, 'public')
DEST = os.path.join(PUB, 'assets', 'rotulos')
HTML = os.path.join(PUB, 'index.html')
WEB = 'assets/rotulos/'

ESTILO = 'acuarela-gracia'
TINTA = lambda *_: pincel.ROJO_ACUARELA
CAP_CSS = 44           # altura máxima de la mayúscula en CSS px (--cap en base.css: min(2.75rem, 8.4vw))
CAP_PX = 104           # altura de la mayúscula en la imagen (móvil de 390 px a 3×: 33 × 3 ≈ 99 px)
NOMBRES_ANCHO = 1100   # ancho de la imagen de los nombres (≈ 3× del ancho que ocupan en el móvil)

# id, líneas, semilla, texto accesible, subrayado, icono (fichero de scripts/acuarela, opcional)
TITULOS = [
    ('agenda', ['AGENDA'], 3, 'Agenda', True, None),
    ('transporte', ['TRANSPORTE'], 7, 'Transporte', True, None),
    ('alojamiento', ['ALOJAMIENTO'], 17, 'Alojamiento', True, 'almohada-icono'),
    ('src', ['S.R.C. · SE RUEGA', 'CONFIRMACIÓN'], 11, 'S.R.C. · Se ruega confirmación', True, None),
    ('lista-de-bodas', ['LISTA DE BODAS'], 8, 'Lista de bodas', True, 'alianzas-icono'),
    ('os-esperamos', ['¡OS ESPERAMOS!'], 13, '¡Os esperamos!', False, None),
]
# la fecha de la portada: más pequeña (en CSS, --cap de .portada__fecha); se pinta a una mayúscula de 64 px
FECHA = (['8 DE MAYO DE 2027'], 9, '8 de mayo de 2027', 64)


def webp(im, ruta, alfa=60):
    """Guarda en WebP. El color de cada tinta es plano (toda la textura va en el alfa), así que el color
    no cuesta casi nada; el alfa va con pérdida (con calidad 60 las estrías siguen nítidas)."""
    b = io.BytesIO()
    im.save(b, 'WEBP', quality=80, alpha_quality=alfa, method=6)
    with open(ruta, 'wb') as f:
        f.write(b.getvalue())
    return b.tell()


def titulo(id_, lineas, semilla, subrayado, cap_px=CAP_PX):
    lz, info = pincel.rotular(lineas, cap_px, estilo=ESTILO, semilla=semilla, tinta=TINTA, margen_x=0.2, interlinea=0.62,
                              subrayado=subrayado)
    im = lz.imagen(granulado=False)
    kb = webp(im, os.path.join(DEST, f'{id_}.webp'))
    k = CAP_CSS / cap_px
    return dict(u=info['u'], w=round(im.width * k), h=round(im.height * k), peso=kb)


def marcado_titulo(id_, texto, d, icono, perezosa=True):
    partes = []
    if icono:
        ruta3 = os.path.join(PUB, 'assets', 'ilustraciones', 'acuarela', f'{icono}-3x.webp')
        if os.path.exists(ruta3):
            iw, ih = Image.open(ruta3).size
            partes.append(
                f'<img class="titulo__icono" src="assets/ilustraciones/acuarela/{icono}-3x.webp" '
                f'srcset="assets/ilustraciones/acuarela/{icono}-2x.webp 2x, assets/ilustraciones/acuarela/{icono}-3x.webp 3x" '
                f'width="{round(iw / 3)}" height="{round(ih / 3)}" alt="" decoding="async" loading="lazy">')
    partes.append(f'<span class="sr-only">{texto}</span>')
    partes.append(
        f'<img class="rotulo" src="{WEB}{id_}.webp" '
        f'width="{d["w"]}" height="{d["h"]}" style="--u:{d["u"]:.3f}" alt="" decoding="async"'
        + (' loading="lazy">' if perezosa else '>'))
    return ''.join(partes)


def simplificar(P, paso):
    """Puntos de la polilínea cada `paso` px (más el último)."""
    d = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(d)])
    L = s[-1]
    n = max(2, int(L / paso) + 1)
    si = np.linspace(0, L, n)
    return np.stack([np.interp(si, s, P[:, 0]), np.interp(si, s, P[:, 1])], 1), float(L)


def nombres():
    # primero se mide el ancho en mayúsculas para que la imagen salga exactamente de NOMBRES_ANCHO px
    _, info = pincel.rotular(['MARTA y JORGE'], 10, estilo=ESTILO, semilla=5, tinta=TINTA, margen_x=0.2, pintar=False)
    cap = NOMBRES_ANCHO / info['u']
    lz, info = pincel.rotular(['MARTA y JORGE'], cap, estilo=ESTILO, semilla=5, tinta=TINTA, margen_x=0.2)
    im = lz.imagen(granulado=False)
    W, H = im.size
    peso = webp(im, os.path.join(DEST, 'nombres.webp'))

    # ejes de los trazos → máscara animada (cada trazo se «pinta» en orden)
    trazos = []
    for color, P, wmax in lz.trazos:
        Q, L = simplificar(P, 6.0)
        trazos.append((Q, L, 2.0 * wmax + 4))
    # comprobación: los ejes engordados cubren toda la tinta de la imagen
    m = Image.new('L', (W, H), 0)
    dib = ImageDraw.Draw(m)
    for Q, L, sw in trazos:
        pts = [tuple(p) for p in Q]
        dib.line(pts, fill=255, width=int(round(sw)), joint='curve')
        for x, y in (pts[0], pts[-1]):
            dib.ellipse((x - sw / 2, y - sw / 2, x + sw / 2, y + sw / 2), fill=255)
    alfa = np.asarray(im.split()[3]) > 12
    cubre = (np.asarray(m) > 0) & alfa
    cobertura = cubre.sum() / max(1, alfa.sum())
    if cobertura < 0.995:
        sys.exit(f'Los ejes de los nombres solo cubren el {cobertura:.1%} de la tinta: revisa simplificar()/anchos')

    # tiempos: cada trazo dura según su largo; pausa corta dentro de la letra y algo más entre letras
    inicio_letra = {n0 for _, _, _, n0, _ in info['letras']}
    t, tiempos = 0.0, []
    for i, (Q, L, sw) in enumerate(trazos):
        if i in inicio_letra and i:
            t += 0.05
        dur = min(0.4, max(0.08, 0.06 + L / (cap * 5.5)))
        tiempos.append((t, dur))
        t += dur * 0.85
    total = t
    escala = 2.4 / total             # toda la firma en ≈ 2,4 s
    paths = []
    for (Q, L, sw), (d0, dur) in zip(trazos, tiempos):
        d = 'M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in Q)
        paths.append(f'<path class="tz" pathLength="1" stroke-width="{sw:.0f}" style="--d:{d0 * escala:.2f}s;--t:{dur * escala:.2f}s" d="{d}"/>')
    fin = max(d0 + dur for d0, dur in tiempos) * escala
    svg = (f'<svg class="nombres__svg" viewBox="0 0 {W} {H}" style="--fin:{fin:.2f}s" aria-hidden="true" focusable="false">'
           f'<defs><mask id="m-nombres" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}" style="mask-type:alpha">'
           + ''.join(paths) +
           f'</mask></defs>'
           f'<image class="nombres__pinta" href="{WEB}nombres.webp" width="{W}" height="{H}" mask="url(#m-nombres)"/>'
           f'<image class="nombres__final" href="{WEB}nombres.webp" width="{W}" height="{H}"/></svg>')
    return svg, H / W, peso, cobertura


def reemplazar(html, id_, contenido):
    patron = re.compile(r'(<!-- rotulo:' + re.escape(id_) + r' -->).*?(<!-- /rotulo:' + re.escape(id_) + r' -->)', re.S)
    if not patron.search(html):
        sys.exit(f'Falta el marcador <!-- rotulo:{id_} --> en public/index.html')
    return patron.sub(lambda m: m.group(1) + contenido + m.group(2), html)


def main():
    os.makedirs(DEST, exist_ok=True)
    html = open(HTML, encoding='utf-8').read()
    total = 0
    for id_, lineas, semilla, texto, subrayado, icono in TITULOS:
        d = titulo(id_, lineas, semilla, subrayado)
        html = reemplazar(html, id_, marcado_titulo(id_, texto, d, icono))
        total += d['peso']
        print(f'  {id_:16s} u={d["u"]:.2f}  {d["peso"] / 1024:5.1f} KB')
    lineas, semilla, texto, cap_px = FECHA
    d = titulo('fecha', lineas, semilla, False, cap_px)
    html = reemplazar(html, 'fecha', marcado_titulo('fecha', texto, d, None, perezosa=False))
    total += d['peso']
    print(f'  fecha            u={d["u"]:.2f}  {d["peso"] / 1024:5.1f} KB')
    svg, rn, peso, cob = nombres()
    html = reemplazar(html, 'nombres', svg)
    html = re.sub(r'<header class="portada" id="portada"[^>]*>', f'<header class="portada" id="portada" style="--rn:{rn:.4f}">', html, count=1)
    total += peso
    print(f'  nombres          {peso / 1024:5.1f} KB  (ejes: {cob:.2%} de la tinta)')
    for nombre, im, alfa in (('borde-sup', piezas.borde_tira(ancho=900, alto=90, semilla=31), 50),
                             ('borde-inf', piezas.borde_tira(ancho=900, alto=90, semilla=32, invertir=True), 50),
                             ('borde-4', piezas.borde_caja(ancho=600, alto=750), 50),
                             ('aguada', piezas.aguada(ancho=400, alto=1200), 40),
                             ('pincelada-boton', piezas.pincelada_boton(ancho=640, alto=160), 60)):
        kb = webp(im, os.path.join(DEST, f'{nombre}.webp'), alfa=alfa)
        total += kb
        print(f'  {nombre:16s} {kb / 1024:5.1f} KB')
    open(HTML, 'w', encoding='utf-8').write(html)
    print(f'Total {total / 1024:.0f} KB en {os.path.relpath(DEST, RAIZ)}')


if __name__ == '__main__':
    main()
