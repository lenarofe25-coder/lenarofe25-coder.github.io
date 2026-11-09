"""Planche-contact des pages rendues : python3 src/planche.py maquette sortie.jpg"""
import glob
import sys

from PIL import Image

name, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
fs = sorted(glob.glob(f"build/{name}/p*.png"))
ims = [Image.open(f) for f in fs]
w, h = ims[0].size
s = 0.5
W, H = int(w * s), int(h * s)
rows = (len(ims) + cols - 1) // cols
c = Image.new("RGB", (cols * (W + 10), rows * (H + 10)), "#999")
for i, im in enumerate(ims):
    c.paste(im.resize((W, H)), ((i % cols) * (W + 10), (i // cols) * (H + 10)))
c.save(out, quality=85)
