"""Deuxième passe : recherche toutes sources (CC0, domaine public, CC BY) et nouvelle planche de choix."""
import json, os, sys, io
sys.path.insert(0, os.path.dirname(__file__))
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
from chercher_photos import get, EXCLU, CAND, PL
from liste import RECETTES

N2 = 8
Q2 = {  # requêtes alternatives
    "cake-marbre": "marble cake slice", "gateau-marrons": "chestnut cake", "tarte-chocolat": "chocolate tart",
    "creme-chocolat": "chocolate pudding cup", "brioche": "brioche bread loaf", "gateau-yaourt": "yogurt cake",
    "pizza-dessert": "nutella pizza", "quatre-quarts": "pound cake",
    "amaretti": "almond cookies", "blondies": "blondie bars", "tarte-sucre": "sugar tart", "flan": "custard pie slice",
    "mousse-citron": "lemon posset", "barres-riz": "rice krispie treats", "ile-flottante": "ile flottante",
    "far-breton": "prune flan", "verrines-speculoos": "biscoff dessert",
}


def chercher(q):
    p = dict(q=q, license="cc0,pdm,by", page_size=20, mature="false")
    res = json.loads(get("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(p)))["results"]
    ok = [r for r in res if not any(w in (r.get("title") or "").lower() for w in EXCLU) and (r.get("width") or 0) >= 1000]
    rang = {"rawpixel": 0, "stocksnap": 0, "wikimedia": 1, "flickr": 2}
    ok.sort(key=lambda r: rang.get(r["source"], 3))
    return ok


def miniature(u):
    """Wikimedia limite les originaux : on demande la miniature standard de 1920 px."""
    if "upload.wikimedia.org/wikipedia/commons/" in u and "/thumb/" not in u:
        parts = u.split("/wikipedia/commons/")[1]
        name = parts.split("/")[-1]
        return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{parts}/1920px-{name}"
    return u


def un(item):
    rid, titre, ch, q = item
    f = os.path.join(CAND, rid + ".2.json")
    if not os.path.exists(f):
        try:
            res = chercher(Q2.get(rid, q))
        except Exception as e:
            print("ÉCHEC", rid, e, flush=True)
            return
        json.dump(res, open(f, "w"))
    res = json.load(open(f))
    for i, r in enumerate(res[:N2]):
        dst = os.path.join(CAND, "img", f"{rid}-b{i}.jpg")
        if not os.path.exists(dst):
            try:
                open(dst, "wb").write(get(miniature(r["url"])))
            except Exception as e:
                print("image", rid, i, r["url"].split('/')[2], e, flush=True)
    print(rid, len(res), flush=True)


if __name__ == "__main__":
    ids = sys.argv[1].split(",")
    lot = [r for r in RECETTES if r[0] in ids]
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(un, lot))
