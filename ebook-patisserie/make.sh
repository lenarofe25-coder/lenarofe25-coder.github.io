#!/usr/bin/env bash
# Régénère tout : illustrations, livre complet, maquette, visuels Etsy.
set -euo pipefail
cd "$(dirname "$0")"
python3 src/build.py maquette
python3 src/build.py
node src/render_images.js
node src/render_pdf.js maquette
node src/render_pdf.js book dist/L-Art-de-la-Patisserie.pdf
PAGES=$(python3 -c "
import json; a=json.load(open('build/book-anchors.json'))
ps={1,a['fraisier'],a['fraisier']+1,a['ch-entremets'],a['tarte-aux-fraises'],a['tarte-aux-fraises']+1,a['eclairs-au-chocolat'],a['macarons-a-la-framboise'],a['croissants'],a['sommaire'],a['sommaire']+1,a['base-creme-patissiere'],a['chocolats']}
print(' '.join(map(str,sorted(ps))))")
SCALE=2 OUT=build/etsy-pages node src/preview.js book $PAGES
python3 src/etsy_mockups.py
