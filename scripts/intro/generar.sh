#!/usr/bin/env bash
# Regenera las dos piezas generadas de la entrada de la portada:
#   · «Marta y Jorge» escritos a pluma (SVG con el orden de trazos de cada letra)  -> .tmp/nombres.svg.html
#   · el ornamento: rayas de la ruta con corazón + fotogramas del vuelo del avión   -> .tmp/orn/ornamento.{svg.html,css}
# Requisitos: python3 con numpy, scikit-image, fonttools, brotli, uharfbuzz y pillow; Node con Playwright
# (PLAYWRIGHT_PATH=/ruta/a/node_modules/playwright si no está instalado globalmente). Guía: LEEME.md
set -euo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(cd "$AQUI/../.." && pwd)"
TMP="$AQUI/.tmp"
PY="${PYTHON:-python3}"
mkdir -p "$TMP" && cd "$TMP"

echo "1/5 Caveat estática en peso 700 (desde la fuente variable autoalojada)"
"$PY" - "$RAIZ/public/assets/fonts/caveat-latin-wght-normal.woff2" <<'PY'
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
f = TTFont(sys.argv[1])
g = instancer.instantiateVariableFont(f, {"wght": 700})
g.flavor = None
g.save("caveat700.ttf")
PY
echo "2/5 Glifos y esqueletos";            "$PY" "$AQUI/glifos.py" >/dev/null
echo "3/5 Trazos de pluma ordenados";      "$PY" "$AQUI/trazos.py" >/dev/null
echo "4/5 Grosor de cobertura y ajustes";  "$PY" "$AQUI/ensamblar.py"
echo "5/5 SVG de los nombres y ornamento"; "$PY" "$AQUI/svg.py" "${VELOCIDAD:-7600}" | head -1
node "$AQUI/ornamento.cjs" "$RAIZ/public/assets/ilustraciones/ruta-horizontal.svg" "$TMP/orn" 2.1 0.2
echo
echo "Listo. Salidas en $TMP:"
echo "  nombres.svg.html           -> pegar dentro de <h1 class=\"nombres\"> en public/index.html"
echo "  orn/ornamento.svg.html     -> pegar dentro de <div class=\"portada__ruta\"> en public/index.html"
echo "  orn/ornamento.css          -> sustituir el bloque «GENERADO» al final de public/css/intro.css"
