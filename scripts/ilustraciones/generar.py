#!/usr/bin/env python3
"""
generar.py · regenera todas las ilustraciones en public/assets/ilustraciones/.

Uso (desde la raíz del repo):
    python3 scripts/ilustraciones/generar.py            # todo
    python3 scripts/ilustraciones/generar.py san_pablo  # solo una pieza
    python3 scripts/ilustraciones/generar.py --salida /otra/carpeta

Determinista: con las mismas semillas sale exactamente el mismo SVG.
"""
import os
import sys

sys.dont_write_bytecode = True   # no dejar __pycache__ en el repo

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
SALIDA = os.path.join(RAIZ, "public", "assets", "ilustraciones")
# Variantes «solo tinta» (sin aguada): no se usan en la web, así que no se publican
ALTERNATIVAS = os.path.join(RAIZ, "docs", "ilustraciones")

LIMITE = 70 * 1024


def escribir(carpeta, nombre, texto):
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    kb = len(texto.encode("utf-8")) / 1024
    aviso = "  <-- ¡SUPERA 70 KB!" if kb * 1024 > LIMITE else ""
    print("  %-26s %6.1f KB%s" % (nombre, kb, aviso))


# San Pablo y el Palomar a pluma (V1): la web usa ahora la versión en acuarela (scripts/acuarela/arquitectura.py), así
# que estos SVG se guardan en docs/ilustraciones/v1/ y no se publican.
V1 = os.path.join(ALTERNATIVAS, "v1")


def pieza_san_pablo(carpeta):
    import san_pablo
    L = san_pablo.dibujar()
    escribir(V1, "san-pablo.svg", L.svg())
    escribir(ALTERNATIVAS, "san-pablo-linea.svg", L.svg(con_color=False))


def pieza_palomar(carpeta):
    import palomar
    L = palomar.dibujar()
    escribir(V1, "palomar.svg", L.svg())
    escribir(ALTERNATIVAS, "palomar-linea.svg", L.svg(con_color=False))


def pieza_rutas(carpeta):
    import rutas
    escribir(carpeta, "ruta-vertical.svg", rutas.vertical())
    escribir(carpeta, "ruta-vertical-v3.svg", rutas.vertical_v3())


def pieza_adornos(carpeta):
    import adornos
    escribir(carpeta, "adornos.svg", adornos.sprite())


def pieza_iconos(carpeta):
    import iconos
    escribir(carpeta, "iconos.svg", iconos.sprite())


def pieza_favicon(carpeta):
    import favicon
    escribir(carpeta, "favicon.svg", favicon.svg())


PIEZAS = {
    "san_pablo": pieza_san_pablo,
    "palomar": pieza_palomar,
    "rutas": pieza_rutas,
    "adornos": pieza_adornos,
    "iconos": pieza_iconos,
    "favicon": pieza_favicon,
}


def main(argv):
    carpeta = SALIDA
    nombres = []
    i = 0
    while i < len(argv):
        if argv[i] == "--salida":
            carpeta = os.path.abspath(argv[i + 1])
            i += 2
            continue
        nombres.append(argv[i])
        i += 1
    os.makedirs(carpeta, exist_ok=True)
    print("Ilustraciones ->", carpeta)
    for n in (nombres or list(PIEZAS)):
        PIEZAS[n](carpeta)


if __name__ == "__main__":
    main(sys.argv[1:])
