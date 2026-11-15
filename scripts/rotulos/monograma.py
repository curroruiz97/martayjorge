"""Monograma «M&J» a pincel de acuarela para el panel de invitados (public/panel/monograma.webp).

Mismo pincel y rojo que los títulos de la web (generar.py: estilo 'acuarela-gracia', pincel.ROJO_ACUARELA).
Uso:  python3 scripts/rotulos/monograma.py      (determinista: misma semilla → mismo fichero)
"""
import io
import os

import pincel

ESTILO = 'acuarela-gracia'                 # = generar.ESTILO
TINTA = lambda *_: pincel.ROJO_ACUARELA    # = generar.TINTA

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DEST = os.path.join(RAIZ, 'public', 'panel', 'monograma.webp')
CAP_PX = 220   # altura de la mayúscula: nítida a 3× en la pantalla de acceso (allí mide ≈ 70 px de mayúscula)
SEMILLA = 9


def webp(im, ruta):
    b = io.BytesIO()
    im.save(b, 'WEBP', quality=80, alpha_quality=60, method=6)   # como generar.webp
    with open(ruta, 'wb') as f:
        f.write(b.getvalue())
    return b.tell()


def main():
    lz, info = pincel.rotular(['M&J'], CAP_PX, estilo=ESTILO, semilla=SEMILLA, tinta=TINTA, margen_x=0.15, interlinea=0.62)
    im = lz.imagen(granulado=False)
    caja = im.getchannel('A').point(lambda v: 255 if v > 6 else 0).getbbox()
    m = round(CAP_PX * 0.06)
    im = im.crop((max(0, caja[0] - m), max(0, caja[1] - m), min(im.width, caja[2] + m), min(im.height, caja[3] + m)))
    kb = webp(im, DEST)
    print(f'{os.path.relpath(DEST, RAIZ)}: {im.width}×{im.height} · {kb / 1024:.0f} KB')


if __name__ == '__main__':
    main()
