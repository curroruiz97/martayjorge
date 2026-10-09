"""Textura de lino sin costuras (public/assets/img/lino.webp).

Es una imagen casi blanca, con hilos horizontales en filas de pequeñas «puntadas» (la trama), hilos verticales muy tenues
(la urdimbre), algunos nudos y motas, y un leve tono de beige verdoso en los hilos. Se superpone con «multiply» sobre el color
crema y las rayas rosas que pone base.css, de modo que los hilos se ven también sobre las rayas, como en una tela de verdad.

Uso:  python3 scripts/fondo/generar.py [salida.webp]      (necesita numpy, scipy y pillow)
Las rayas rosas NO salen de aquí: son un degradado CSS (base.css, --p = ancho de cada repetición).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

N = 512                      # px del lado; en la web se muestra a 256 px CSS (el doble de densidad)
FILAS = 160                  # filas de hilo en la baldosa (3,2 px cada una; 1,6 px CSS)
rng = np.random.default_rng(20270508)


def suave(a, sy, sx):
    """Desenfoque circular (la textura queda sin costuras)."""
    return gaussian_filter(a, (sy, sx), mode="wrap")


def normal(sy, sx):
    r = suave(rng.normal(size=(N, N)), sy, sx)
    return r / r.std()


# --- 1) Filas de puntadas: cada fila es una sucesión de trazos cortos (4-11 px) separados por pequeños huecos ---
yy = np.arange(N)[:, None]
perfil = np.zeros((N, N))
for k in range(FILAS):
    yc = (k + 0.5) * N / FILAS + rng.normal(0, 0.28)          # un poco de irregularidad en cada fila
    fuerza_fila = rng.uniform(0.55, 1.0)
    x = int(rng.integers(0, 8))
    while x < N + 12:
        largo = int(rng.integers(5, 13))
        hueco = int(rng.integers(1, 4))
        f = fuerza_fila * rng.uniform(0.35, 1.0)
        xs = np.arange(x, x + largo) % N
        dy = (np.arange(N) - yc + N / 2) % N - N / 2           # distancia vertical circular a la fila
        banda = np.exp(-(dy / 0.95) ** 2)                       # perfil gaussiano de ~1,9 px de ancho
        perfil[:, xs] += banda[:, None] * f
        x += largo + hueco
perfil = suave(perfil, 0.35, 0.5)
perfil /= perfil.max()

modulacion = 0.75 + 0.5 * (0.5 + 0.5 * np.tanh(normal(70, 70)))      # zonas con más y menos densidad de hilo
img = 1.0 - perfil * modulacion * 0.30

# --- 2) Urdimbre: hilos verticales, más tenues ---
img += normal(8.0, 0.7) * 0.007
# --- 3) Grano fino ---
img += rng.normal(size=(N, N)) * 0.0045
# --- 4) Nudos y hebras sueltas ---
def trazos(cuantos, largo, grueso, fuerza, signo=-1):
    capa = np.zeros((N, N))
    for _ in range(cuantos):
        y = rng.integers(0, N)
        x = rng.integers(0, N)
        l = int(rng.uniform(*largo))
        g = int(rng.choice(grueso))
        f = rng.uniform(*fuerza)
        for dy in range(g):
            xs = (x + np.arange(l)) % N
            capa[(y + dy) % N, xs] += f * (1 - 0.5 * dy / max(g, 1))
    return signo * suave(capa, 0.45, 0.8)

img += trazos(45, (18, 40), (2, 3), (0.025, 0.05))                    # nudos de hilo
img += trazos(500, (6, 14), (1, 1, 2), (0.015, 0.035), +1)             # hebras más claras
# --- 5) Motas (fibras y semillas del lino) ---
motas = np.zeros((N, N))
for _ in range(60):
    y, x = rng.integers(0, N, 2)
    motas[y, x] += rng.uniform(0.05, 0.12)
img -= suave(motas, 0.8, 0.8) * 2.4

img = np.clip(img, 0.0, 1.0)
img = (img - img.min()) / (img.max() - img.min())
img = 0.78 + 0.22 * img                               # luminancia entre 0,80 y 1: casi blanco, con hilos visibles

# Tono: los hilos oscuros se tiñen de beige verdoso (como en la tela de referencia); lo claro queda neutro
oscuridad = 1.0 - img
rgb = np.stack([img - oscuridad * 0.02, img + oscuridad * 0.0, img - oscuridad * 0.26], axis=-1)
rgb = (np.clip(rgb, 0, 1) * 255).round().astype(np.uint8)

salida = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "public/assets/img/lino.webp")
Image.fromarray(rgb, "RGB").save(salida, "WEBP", quality=60, method=6)
print(f"{salida} · {salida.stat().st_size / 1024:.0f} KB · media {rgb.mean():.1f} · mín {rgb.min()} · máx {rgb.max()}")
