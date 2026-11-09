"""Visuels de vente (Etsy, Payhip, Gumroad) à partir des pages rendues en PNG.

Pré-requis : PNG=1 SCALE=2 PAGES=1,2,3,17,34,39,40,52,61,97,102,104,109,111,113 node src/render.js livre
Sortie : dist/visuels/
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(ROOT, "build", "livre")
OUT = os.path.join(ROOT, "dist", "visuels")
FONTS = os.path.join(ROOT, "fonts")
os.makedirs(OUT, exist_ok=True)

CREME = (251, 247, 242)
SABLE = (243, 235, 225)
ROSE = (244, 223, 218)
ROSE_FONCE = (192, 121, 109)
ENCRE = (51, 37, 31)
BRUN = (107, 68, 51)


def police(nom, taille, poids=None):
    f = ImageFont.truetype(os.path.join(FONTS, nom), taille)
    if poids:
        try:
            f.set_variation_by_axes([poids] if "DMSans" not in nom else [14, poids])
        except Exception:
            pass
    return f


def titre_font(t):
    f = ImageFont.truetype(os.path.join(FONTS, "Fraunces-normal-latin.woff2"), t)
    f.set_variation_by_axes([144, 420])
    return f


def texte_font(t, poids=400):
    f = ImageFont.truetype(os.path.join(FONTS, "DMSans-normal-latin.woff2"), t)
    try:
        f.set_variation_by_axes([24, poids])
    except Exception:
        pass
    return f


def page(n, h):
    im = Image.open(os.path.join(PAGES, f"p{n:03d}.png")).convert("RGB")
    w = int(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)


def ombre(fond, im, xy, flou=30, decal=(16, 22), opacite=95, angle=0):
    im = im.convert("RGBA")
    if angle:
        im = im.rotate(angle, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (im.width + flou * 4, im.height + flou * 4), (0, 0, 0, 0))
    masque = Image.new("L", im.size, 0)
    masque.paste(im.split()[3])
    calque = Image.new("RGBA", im.size, (70, 45, 30, opacite))
    sh.paste(calque, (flou * 2, flou * 2), masque)
    sh = sh.filter(ImageFilter.GaussianBlur(flou))
    fond.paste(sh, (xy[0] - flou * 2 + decal[0], xy[1] - flou * 2 + decal[1]), sh)
    fond.paste(im, xy, im)


def centre(d, y, txt, f, couleur, largeur):
    w = d.textlength(txt, font=f)
    d.text(((largeur - w) / 2, y), txt, font=f, fill=couleur)


def bandeau(c, titre, sous, y):
    d = ImageDraw.Draw(c)
    centre(d, y, titre, titre_font(86), ENCRE, c.width)
    centre(d, y + 112, sous, texte_font(38, 500), ROSE_FONCE, c.width)


# 1. couverture carrée (vignette Etsy / Payhip)
def couverture_carree():
    c = Image.new("RGB", (2000, 2000), SABLE)
    p = page(1, 1820)
    ombre(c, p, ((2000 - p.width) // 2, 80), flou=36)
    c.save(os.path.join(OUT, "01-couverture-carree.jpg"), quality=92)
    # couverture seule (fichier de couverture du livre)
    Image.open(os.path.join(PAGES, "p001.png")).convert("RGB").save(os.path.join(OUT, "couverture-livre.jpg"), quality=94)


# 2. éventail de fiches
def eventail():
    c = Image.new("RGB", (2000, 2000), CREME)
    nums = [17, 52, 39, 97, 34]
    h = 1180
    pas = 300
    x0 = 1000 - (pas * (len(nums) - 1) + int(h * 0.707)) // 2
    for i, n in enumerate(nums):
        p = page(n, h)
        ang = (i - 2) * 3.5
        y = 120 + abs(i - 2) * 30
        ombre(c, p, (x0 + i * pas, y), flou=26, angle=ang)
    bandeau(c, "100 recettes simples et gourmandes", "UNE PHOTO ET UNE PAGE PAR RECETTE", 1560)
    c.save(os.path.join(OUT, "02-cent-recettes.jpg"), quality=92)


# 3. une fiche en grand
def fiche():
    c = Image.new("RGB", (2000, 2000), ROSE)
    p = page(17, 1600)
    ombre(c, p, (110, 200), flou=34)
    d = ImageDraw.Draw(c)
    x = 110 + p.width + 80
    d.text((x, 380), "Tout tient", font=titre_font(74), fill=ENCRE)
    d.text((x, 470), "sur une page", font=titre_font(74), fill=ENCRE)
    puces = ["Temps et difficulté", "Ingrédients pesés", "Étapes numérotées", "Une astuce", "Une vraie photo"]
    for i, t in enumerate(puces):
        y = 640 + i * 110
        d.ellipse((x, y + 10, x + 26, y + 36), fill=ROSE_FONCE)
        d.text((x + 50, y), t, font=texte_font(44, 500), fill=BRUN)
    c.save(os.path.join(OUT, "03-une-recette-une-page.jpg"), quality=92)


# 4. sommaire
def sommaire():
    c = Image.new("RGB", (2000, 2000), SABLE)
    a, b = page(2, 1330), page(3, 1330)
    x0 = (2000 - a.width - b.width) // 2
    ombre(c, a, (x0, 110), flou=30)
    ombre(c, b, (x0 + a.width, 110), flou=30)
    ImageDraw.Draw(c).line([(x0 + a.width, 110), (x0 + a.width, 110 + a.height)], fill=(220, 208, 196), width=3)
    bandeau(c, "Retrouvez une recette en 1 seconde", "SOMMAIRE ET INDEX CLIQUABLES SUR TABLETTE", 1620)
    c.save(os.path.join(OUT, "04-sommaire.jpg"), quality=92)


# 5. grille de photos
def mosaique():
    c = Image.new("RGB", (2000, 2000), CREME)
    noms = ["cookies", "tarte-fraises", "pancakes", "cinnamon-rolls", "tiramisu", "cupcakes-vanille",
            "fondant-chocolat", "meringues", "brownies", "crepes", "cake-pops", "roule-nutella"]
    cols, marge, gout = 4, 70, 26
    cote = (2000 - 2 * marge - (cols - 1) * gout) // cols
    for i, n in enumerate(noms):
        im = Image.open(os.path.join(ROOT, "photos", "recettes", n + ".jpg")).convert("RGB")
        s = min(im.size)
        im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2)).resize((cote, cote), Image.LANCZOS)
        m = Image.new("L", (cote, cote), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, cote, cote), radius=34, fill=255)
        x = marge + (i % cols) * (cote + gout)
        y = 90 + (i // cols) * (cote + gout)
        c.paste(im, (x, y), m)
    bandeau(c, "Des gâteaux qui donnent envie", "COOKIES · TARTES · CUPCAKES · CRÊPES · BROWNIES…", 1600)
    c.save(os.path.join(OUT, "05-photos.jpg"), quality=92)


# 6. avec les enfants
def enfants():
    c = Image.new("RGB", (2000, 2000), ROSE)
    a, b = page(104, 1330), page(111, 1330)
    x0 = (2000 - a.width - b.width) // 2
    ombre(c, a, (x0, 110), flou=30)
    ombre(c, b, (x0 + a.width, 110), flou=30)
    bandeau(c, "Un chapitre à faire avec les enfants", "POUR DÉBUTANTS · EN FAMILLE · SANS MATÉRIEL DE PRO", 1620)
    c.save(os.path.join(OUT, "06-enfants.jpg"), quality=92)


# bannière horizontale (Gumroad / Payhip)
def banniere():
    c = Image.new("RGB", (1280, 720), SABLE)
    p = page(1, 640)
    ombre(c, p, (90, 40), flou=22)
    d = ImageDraw.Draw(c)
    x = 90 + p.width + 70
    d.text((x, 190), "Mes recettes", font=titre_font(64), fill=ENCRE)
    d.text((x, 262), "de pâtisserie", font=titre_font(64), fill=BRUN)
    d.text((x, 370), "100 gâteaux simples et gourmands", font=texte_font(30, 500), fill=ENCRE)
    d.text((x, 412), "à réaliser chez soi", font=texte_font(30, 500), fill=ENCRE)
    d.rounded_rectangle((x, 490, x + 330, 556), radius=33, fill=ROSE)
    d.text((x + 34, 505), "PDF · 116 pages", font=texte_font(28, 600), fill=BRUN)
    c.save(os.path.join(OUT, "banniere-1280x720.jpg"), quality=92)


if __name__ == "__main__":
    couverture_carree()
    eventail()
    fiche()
    sommaire()
    mosaique()
    enfants()
    banniere()
    print("visuels ->", OUT, sorted(os.listdir(OUT)))
