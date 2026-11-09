"""Cherche des photos CC0 (rawpixel via Openverse) pour chaque recette et fabrique des planches de choix.

python3 src/chercher_photos.py            -> build/candidats/<id>.json + build/planches/planche-NN.jpg
"""
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from liste import RECETTES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.path.join(ROOT, "build", "candidats")
PL = os.path.join(ROOT, "build", "planches")
UA = {"User-Agent": "ebook-maquette/1.0 (livre de recettes personnel; contact via github.com/lenarofe25-coder)"}
EXCLU = ("png", "vector", "illustration", "clip", "drawing", "sticker", "collage", "element", "icon", "cartoon",
         "psd", "mockup", "pattern", "vintage", "watercolor", "artwork", "logo", "template", "poster", "frame", "sketch")
N = 6


def get(u, tries=3):
    for k in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
        except Exception as e:  # 504 / 429 : on réessaie
            if k == tries - 1:
                raise
            time.sleep(4 * (k + 1))


def chercher(q):
    p = dict(q=q, license="cc0", source="rawpixel", page_size=20, mature="false")
    res = json.loads(get("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(p)))["results"]
    ok = []
    for r in res:
        t = (r.get("title") or "").lower()
        if any(w in t for w in EXCLU):
            continue
        if (r.get("width") or 0) < 1500:
            continue
        ok.append(r)
    return ok


def un(item):
    rid, titre, ch, q = item
    f = os.path.join(CAND, rid + ".json")
    if os.path.exists(f):
        res = json.load(open(f))
    else:
        try:
            res = chercher(q)
        except Exception as e:
            print("ÉCHEC", rid, e, flush=True)
            return
        json.dump(res, open(f, "w"))
    for i, r in enumerate(res[:N]):
        dst = os.path.join(CAND, "img", f"{rid}-{i}.jpg")
        if not os.path.exists(dst):
            try:
                open(dst, "wb").write(get(r["url"]))
            except Exception as e:
                print("image", rid, i, e, flush=True)
    print(rid, len(res), flush=True)


def main():
    from concurrent.futures import ThreadPoolExecutor
    os.makedirs(os.path.join(CAND, "img"), exist_ok=True)
    os.makedirs(PL, exist_ok=True)
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(un, RECETTES))
    # planches : 5 recettes par planche, 6 candidates par recette
    W, H = 260, 190
    for s in range(0, len(RECETTES), 5):
        lot = RECETTES[s:s + 5]
        c = Image.new("RGB", (W * N + 160, H * len(lot)), "white")
        d = ImageDraw.Draw(c)
        for row, (rid, titre, ch, q) in enumerate(lot):
            d.text((4, row * H + 80), rid[:22], fill="black")
            f = os.path.join(CAND, rid + ".json")
            res = json.load(open(f)) if os.path.exists(f) else []
            for i, r in enumerate(res[:N]):
                try:
                    im = Image.open(os.path.join(CAND, "img", f"{rid}-{i}.jpg")).convert("RGB")
                    im.thumbnail((W - 6, H - 18))
                    x, y = 160 + i * W, row * H
                    c.paste(im, (x + 3, y + 16))
                    d.text((x + 3, y + 2), f"{i} {r['width']}x{r['height']}", fill="black")
                except Exception as e:
                    print("vignette", rid, i, e)
        c.save(os.path.join(PL, f"planche-{s // 5:02d}.jpg"), quality=78)
        print("planche", s // 5, flush=True)


if __name__ == "__main__":
    main()
