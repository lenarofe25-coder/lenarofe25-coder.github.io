"""Planches de choix pour la 2e passe : python3 src/planche2.py id1,id2,...  -> build/planches2/p-NN.jpg"""
import glob
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "build", "candidats", "img")
OUT = os.path.join(ROOT, "build", "planches2")
os.makedirs(OUT, exist_ok=True)
ids = sys.argv[1].split(",")
W, H, N, PAR = 230, 170, 8, 5
for s in range(0, len(ids), PAR):
    lot = ids[s:s + PAR]
    c = Image.new("RGB", (W * N + 150, H * len(lot)), "white")
    d = ImageDraw.Draw(c)
    for row, rid in enumerate(lot):
        d.text((4, row * H + 70), rid[:22], fill="black")
        for i in range(N):
            f = os.path.join(IMG, f"{rid}-b{i}.jpg")
            if not os.path.exists(f):
                continue
            try:
                im = Image.open(f).convert("RGB")
            except Exception:
                continue
            im.thumbnail((W - 6, H - 16))
            x, y = 150 + i * W, row * H
            c.paste(im, (x + 3, y + 14))
            d.text((x + 3, y + 1), f"b{i}", fill="black")
    c.save(os.path.join(OUT, f"p-{s // PAR:02d}.jpg"), quality=78)
print(len(ids))
