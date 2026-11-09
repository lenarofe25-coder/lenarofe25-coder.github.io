"""Visuels pour la fiche Etsy (2000 × 1600 px) à partir des pages du livre.

Pré-requis : python3 src/build.py && SCALE=2 OUT=build/etsy-pages node src/preview.js book <pages…>
(le script `make_etsy.sh` enchaîne tout).
"""
import json
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(ROOT, "build", "etsy-pages")
OUT = os.path.join(ROOT, "dist", "etsy")
FONT = os.path.join(ROOT, "assets", "fonts")
A = json.load(open(os.path.join(ROOT, "build", "book-anchors.json")))

BG = (242, 233, 218)
CHOC = (58, 42, 34)
GOLD = (180, 142, 79)


def page(n):
    return Image.open(os.path.join(PAGES, f"p{n:03d}.png")).convert("RGB")


def shadowed(canvas, im, xy, blur=28, off=(14, 18)):
    x, y = xy
    sh = Image.new("RGBA", (im.width + blur * 4, im.height + blur * 4), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([blur * 2, blur * 2, blur * 2 + im.width, blur * 2 + im.height], fill=(60, 40, 25, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(sh, (x - blur * 2 + off[0], y - blur * 2 + off[1]), sh)
    canvas.paste(im, (x, y))


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT, name), size)


def caption(c, title, sub):
    d = ImageDraw.Draw(c)
    f1, f2 = font("Cormorant-500.ttf", 74), font("Jost-400.ttf", 26)
    w = d.textlength(title, font=f1)
    d.text(((c.width - w) / 2, 1400), title, font=f1, fill=CHOC)
    sp = " ".join(sub.upper())
    w2 = d.textlength(sp, font=f2)
    d.text(((c.width - w2) / 2, 1500), sp, font=f2, fill=GOLD)


def spread(left, right, title, sub, name, h=1240):
    c = Image.new("RGB", (2000, 1600), BG)
    l, r = page(left), page(right)
    w = int(l.width * h / l.height)
    l, r = l.resize((w, h), Image.LANCZOS), r.resize((w, h), Image.LANCZOS)
    x0 = (2000 - 2 * w) // 2
    shadowed(c, l, (x0, 80))
    shadowed(c, r, (x0 + w, 80))
    ImageDraw.Draw(c).line([(x0 + w, 80), (x0 + w, 80 + h)], fill=(210, 198, 180), width=2)
    caption(c, title, sub)
    c.save(os.path.join(OUT, name), quality=92)


def fan(pages, title, sub, name, h=1050):
    c = Image.new("RGB", (2000, 1600), BG)
    n = len(pages)
    ims = [page(p) for p in pages]
    w = int(ims[0].width * h / ims[0].height)
    step = (2000 - 160 - w) // (n - 1)
    for i, im in enumerate(ims):
        im = im.resize((w, h), Image.LANCZOS).convert("RGBA")
        ang = (i - (n - 1) / 2) * 3
        rot = im.rotate(ang, expand=True, resample=Image.BICUBIC)
        x = 80 + i * step
        y = 150 + abs(i - (n - 1) / 2) * 25
        sh = Image.new("RGBA", rot.size, (0, 0, 0, 0))
        sh.paste((60, 40, 25, 100), mask=rot.split()[3])
        sh = sh.filter(ImageFilter.GaussianBlur(20))
        c.paste(sh, (int(x) + 14, int(y) + 18), sh)
        c.paste(rot, (int(x), int(y)), rot)
    caption(c, title, sub)
    c.save(os.path.join(OUT, name), quality=92)


def cover():
    c = Image.new("RGB", (2000, 2000), BG)
    p = page(1)
    h = 1760
    w = int(p.width * h / p.height)
    shadowed(c, p.resize((w, h), Image.LANCZOS), ((2000 - w) // 2, 110), blur=34)
    c.save(os.path.join(OUT, "01-couverture.jpg"), quality=92)
    p.save(os.path.join(OUT, "couverture-seule.png"))


def main():
    os.makedirs(OUT, exist_ok=True)
    cover()
    fa = A["fraisier"]
    spread(fa, fa + 1, "Une recette, une double page", "Photo · ingrédients · étapes · conseils", "02-fiche-recette.jpg")
    fan([A["ch-entremets"], A["tarte-aux-fraises"], A["eclairs-au-chocolat"], A["macarons-a-la-framboise"], A["croissants"]],
        "100 recettes de pâtisserie française", "9 chapitres · du goûter aux grandes occasions", "03-chapitres.jpg")
    spread(A["sommaire"], A["sommaire"] + 1, "Sommaire détaillé et cliquable", "Idéal sur tablette comme à l'impression", "04-sommaire.jpg")
    spread(A["base-creme-patissiere"], A["chocolats"], "Les bases et les guides", "18 préparations de base · 9 guides pratiques", "05-bases-guides.jpg")
    tp = A["tarte-aux-fraises"]
    spread(tp, tp + 1, "Pas à pas, sans approximation", "Grammes · températures · erreurs à éviter", "06-tarte.jpg")
    print("visuels ->", OUT)


if __name__ == "__main__":
    main()
