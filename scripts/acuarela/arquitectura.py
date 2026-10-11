"""San Pablo y el Palomar de La Posada, en acuarela y a pincel (V2).

Reutiliza la geometría de los dibujos a pluma (scripts/ilustraciones/san_pablo.py y palomar.py, que no se tocan):
una subclase de pluma.Lienzo registra, mientras se dibujan, los trazos (contornos y detalles), los polígonos que
se iban a rayar (sombras) y las aguadas. Con eso se pinta otra cosa:
  · aguadas de acuarela (lib.py) con la paleta de la V2, veladuras frías donde había rayado y un cielo apenas
    insinuado;
  · líneas de pincel (scripts/rotulos/pincel.py): contornos y detalles con pincel de tinta, y el rayado y las
    texturas (sillería, tejas…) con un pincel muy fino y una tinta más suave, que dan el grano de la piedra;
  · la tinta va un poco desplazada respecto al color, como en un boceto de tinta y acuarela.
Se guarda sobre blanco (sin transparencia: pesa la tercera parte) y en la página se funde con el lino con
mix-blend-mode: multiply, como el pigmento transparente sobre el papel.
Las ilustraciones a pluma de la V1 siguen en docs/ilustraciones/v1/ (y se regeneran con scripts/ilustraciones).

  python3 scripts/acuarela/arquitectura.py      (necesita Node con Playwright y Chromium, como generar.py)
"""
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
SALIDA = RAIZ / "public" / "assets" / "ilustraciones" / "acuarela"
sys.path.insert(0, str(RAIZ / "scripts" / "ilustraciones"))
sys.path.insert(0, str(RAIZ / "scripts" / "rotulos"))
sys.path.insert(0, str(AQUI))

import pluma  # noqa: E402
import san_pablo  # noqa: E402
import palomar  # noqa: E402
import pincel  # noqa: E402
from lib import Lienzo  # noqa: E402

ANCHOS = (640, 960)
TINTA = (74, 59, 54)
TINTA_SUAVE = (120, 104, 96)
COLOR = {pluma.OCRE: "#d3b27a", pluma.TERRACOTA: "#c0603f", pluma.OLIVA: "#8c9d76"}
SOMBRA = "#a497a8"        # veladura fría donde el dibujo a pluma llevaba rayado
CIELO = "#c6d9e3"
DESREGISTRO = (2.2, -1.6)  # unidades del dibujo
pincel.ESTILOS["linea-pincel"] = dict(ancho=1.0, cerdas=10, carga=2.0, recorrido=90.0, fin=(0.45, 0.7), seco=0.4,
                                      umbral=(0.12, 0.55), suavidad=0.08, densidad=2.2, temblor=0.0)


class Registro(pluma.Lienzo):
    """pluma.Lienzo que además apunta la geometría (llamando siempre a super(): el dibujo es el mismo de la V1)."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.reg, self.sombras, self.manchas = [], [], []

    def _datos_mano(self, pts, esquinas, fam, *a, **k):
        self.reg.append((fam, list(pts)))
        return super()._datos_mano(pts, esquinas, fam, *a, **k)

    def raya(self, A, B, *a, **k):
        self.reg.append(("s", [A, B]))
        return super().raya(A, B, *a, **k)

    def rayado(self, poly, *a, **k):
        self.sombras.append(list(poly))
        return super().rayado(poly, *a, **k)

    def aguada(self, poly, color, op=0.2, *a, **k):
        self.manchas.append((list(poly), color, op))
        return super().aguada(poly, color, op, *a, **k)


def capturar(modulo, **kw):
    original = modulo.Lienzo
    modulo.Lienzo = Registro
    try:
        return modulo.dibujar(**kw)
    finally:
        modulo.Lienzo = original


def poligono(poly):
    return "M" + " L".join("%.1f %.1f" % p for p in poly) + "Z"


def aguadas_svg(R, semilla, cielo):
    L = Lienzo(R.w, R.h, semilla)
    if cielo:
        cx, cy, rx, ry = cielo
        L.mancha(L.blob(cx, cy, rx, ry, 12, .12), CIELO, .16, rimo=.12)
    for poly in R.sombras:
        if len(poly) >= 3:
            L.mancha(poligono(poly), SOMBRA, .3)
    for poly, color, op in R.manchas:
        L.mancha(poligono(poly), COLOR.get(color, color), min(.85, op * 2.4))
    return L.svg(fondo=False, fuente_css="")


def lineas(R, ancho_px, semilla, prop_textura=0.75):
    k = ancho_px / R.w
    alto_px = round(R.h * k)
    rng = np.random.RandomState(semilla)
    elegir = random.Random(semilla)
    lz = pincel.Lienzo(ancho_px, alto_px, ss=2, semilla_papel=semilla, densidad=2.2)
    est = pincel.ESTILOS["linea-pincel"]
    for fam, pts in R.reg:
        if fam == "s" and elegir.random() > prop_textura:
            continue
        w = {"c": 2.8, "d": 1.5, "s": 0.95}[fam] * k
        P = [((x + DESREGISTRO[0]) * k, (y + DESREGISTRO[1]) * k) for x, y in pts]
        lz.trazo(P, TINTA_SUAVE if fam == "s" else TINTA, est, rng, w, tipo="l" if len(P) == 2 else "c")
    return lz.imagen(granulado=False)


def pieza(nombre, R, semilla, cielo):
    with tempfile.TemporaryDirectory() as tmp:
        svgs, pngs = Path(tmp) / "svg", Path(tmp) / "png"
        svgs.mkdir()
        (svgs / f"{nombre}.svg").write_text(aguadas_svg(R, semilla, cielo), encoding="utf-8")
        subprocess.run(["node", str(AQUI / "exportar.cjs"), str(svgs), str(pngs), str(max(ANCHOS))], check=True, env=os.environ)
        color = Image.open(pngs / f"{nombre}-{max(ANCHOS)}.png").convert("RGBA")
    tinta = lineas(R, color.width, semilla)
    if tinta.size != color.size:
        tinta = tinta.resize(color.size, Image.LANCZOS)
    color.alpha_composite(tinta)
    plano = Image.new("RGBA", color.size, (255, 255, 255, 255))
    plano.alpha_composite(color)
    plano = plano.convert("RGB")
    for a in ANCHOS:
        im = plano if a == plano.width else plano.resize((a, round(plano.height * a / plano.width)), Image.LANCZOS)
        destino = SALIDA / f"{nombre}-acuarela-{a}.webp"
        im.save(destino, "WEBP", quality=72, method=6)
        print(f"  {destino.relative_to(RAIZ)}  {im.width}×{im.height}  {destino.stat().st_size / 1024:.0f} KB")


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    pieza("san-pablo", capturar(san_pablo), 1506, (260, 230, 270, 190))
    pieza("palomar", capturar(palomar), 2017, (350, 150, 340, 120))


if __name__ == "__main__":
    main()
