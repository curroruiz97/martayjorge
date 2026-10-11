"""Genera las ilustraciones de acuarela de la web (public/assets/ilustraciones/acuarela/*.webp).

  python3 scripts/acuarela/generar.py            (necesita Pillow, Node con Playwright y Chromium)
  python3 scripts/acuarela/generar.py bodegon    (solo las escenas indicadas)

Pasos: 1) dibuja cada escena de escenas.py como SVG sin fondo; 2) Chromium (exportar.cjs) lo convierte en PNG transparente
a cada anchura; 3) Pillow lo guarda como WebP con transparencia. Los dibujos son deterministas: salen siempre iguales.
Variables: PLAYWRIGHT_PATH, CHROME_PATH (ver exportar.cjs).
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
SALIDA = RAIZ / "public" / "assets" / "ilustraciones" / "acuarela"
sys.path.insert(0, str(AQUI))
import escenas  # noqa: E402

# anchuras (px) de cada imagen: la pequeña para móviles, la grande para pantallas anchas o de mucha densidad
ANCHOS = {"guirnalda": (630,), "bodegon": (640, 1000), "ramo": (480, 760), "almohada": (460, 700), "maleta": (380, 560), "granadas": (300, 420)}
# iconos junto a los títulos: se recortan al dibujo y se guardan a 2× y 3× de su alto en pantalla (1,15 × la mayúscula
# de los rótulos, que mide como mucho 44 px: ver .titulo__icono en site.css)
ICONOS = {"alianzas-icono": 51, "almohada-icono": 51}
CALIDAD, CALIDAD_ALFA = 66, 62      # con estos valores pesan la mitad que con 82/90 y no se nota (el grano del papel se suaviza algo)


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        svgs, pngs = Path(tmp) / "svg", Path(tmp) / "png"
        svgs.mkdir()
        pedidas = sys.argv[1:] or list(escenas.ESCENAS)
        for nombre in pedidas:
            L = escenas.ESCENAS[nombre]()
            (svgs / f"{nombre}.svg").write_text(L.svg(fondo=False), encoding="utf-8")
        todos = sorted({a for n, v in ANCHOS.items() if n in pedidas for a in v} | ({600} if set(pedidas) & set(ICONOS) else set()))
        subprocess.run(["node", str(AQUI / "exportar.cjs"), str(svgs), str(pngs), ",".join(map(str, todos))], check=True, env=os.environ)
        total = 0
        for nombre in pedidas:
            if nombre in ICONOS:
                im = Image.open(pngs / f"{nombre}-600.png").convert("RGBA")
                x0, y0, x1, y1 = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
                m = int((y1 - y0) * .03)
                im = im.crop((max(0, x0 - m), max(0, y0 - m), min(im.width, x1 + m), min(im.height, y1 + m)))
                for sufijo, k in (("2x", 2), ("3x", 3)):
                    alto = ICONOS[nombre] * k
                    ic = im.convert("RGBa").resize((round(im.width * alto / im.height), alto), Image.LANCZOS).convert("RGBA")
                    destino = SALIDA / f"{nombre}-{sufijo}.webp"
                    ic.save(destino, "WEBP", quality=80, alpha_quality=80, method=6)
                    kb = destino.stat().st_size / 1024
                    total += kb
                    print(f"  {destino.relative_to(RAIZ)}  {ic.width}×{ic.height}  {kb:.0f} KB")
                continue
            for a in ANCHOS[nombre]:
                im = Image.open(pngs / f"{nombre}-{a}.png").convert("RGBA")
                destino = SALIDA / f"{nombre}-{a}.webp"
                im.save(destino, "WEBP", quality=CALIDAD, alpha_quality=CALIDAD_ALFA, method=6)
                kb = destino.stat().st_size / 1024
                total += kb
                print(f"  {destino.relative_to(RAIZ)}  {im.width}×{im.height}  {kb:.0f} KB")
    print(f"Total: {total:.0f} KB")


if __name__ == "__main__":
    main()
