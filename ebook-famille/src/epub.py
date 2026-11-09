"""Version Kindle (EPUB 3 « recomposable ») : python3 src/epub.py -> dist/Mes-recettes-de-patisserie.epub

Le texte s'adapte à l'écran (liseuse, téléphone, tablette). Une recette par section,
avec sa photo, ses repères, ses ingrédients, ses étapes et son astuce.
"""
import html
import json
import os
import re
import sys
import uuid
import zipfile
from datetime import datetime, timezone

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from liste import CHAPITRES, RECETTES  # noqa: E402
from recettes import toutes  # noqa: E402
from livre import QTE  # noqa: E402

PHOTOS = os.path.join(ROOT, "photos", "recettes")
OUT = os.path.join(ROOT, "dist", "Mes-recettes-de-patisserie.epub")
COUV = os.path.join(ROOT, "dist", "kindle", "couverture-kindle.jpg")
TITRE = "Mes recettes de pâtisserie"
SOUS_TITRE = "100 gâteaux simples et gourmands à réaliser chez soi"
LANG = "fr"
UID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "mes-recettes-de-patisserie"))

e = lambda t: html.escape(t, quote=True)  # noqa: E731

CSS = """
body { font-family: serif; line-height: 1.45; margin: 0 2%; }
h1 { font-size: 1.7em; line-height: 1.15; margin: 0.6em 0 0.2em; text-align: left; page-break-before: always; }
h1.chap { font-size: 2em; margin-top: 30%; text-align: center; }
h2 { font-size: 1.15em; margin: 1.1em 0 0.4em; }
p { margin: 0 0 0.5em; text-indent: 0; }
.photo { margin: 0 0 0.6em; text-align: center; }
.photo img { width: 100%; max-width: 100%; height: auto; }
.desc { font-style: italic; color: #6b4433; margin-bottom: 0.7em; }
.infos { font-size: 0.9em; margin: 0.4em 0 0.8em; padding: 0.4em 0.6em; background-color: #f3ebe1; border-radius: 0.4em; }
.infos b { color: #6b4433; }
ul.ing { margin: 0 0 0.6em 0; padding-left: 1.2em; }
ul.ing li { margin-bottom: 0.25em; }
ol.etapes { margin: 0 0 0.6em 0; padding-left: 1.4em; }
ol.etapes li { margin-bottom: 0.45em; }
.astuce { margin: 0.9em 0 1em; padding: 0.5em 0.7em; background-color: #f4dfda; border-radius: 0.4em; }
.astuce b { color: #c0796d; }
.liste { margin: 1em 0; padding-left: 1.2em; }
.centre { text-align: center; }
.petit { font-size: 0.8em; color: #555; }
.credits p { font-size: 0.75em; margin-bottom: 0.3em; }
a { color: inherit; text-decoration: none; }
"""


def xhtml(titre, corps):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{LANG}" lang="{LANG}">
<head><meta charset="utf-8"/><title>{e(titre)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>{corps}</body></html>"""


def ingredient(t):
    if ":" in t and t.index(":") < 30:
        a, b = t.split(":", 1)
        return f"<li><b>{e(a.strip())}</b> : {e(b.strip())}</li>"
    m = QTE.match(t)
    if m and m.group(1).strip():
        q = m.group(1)
        return f"<li><b>{e(q.strip())}</b> {e(t[len(q):].lstrip())}</li>"
    return f"<li>{e(t)}</li>"


NIVEAU = {1: "●○○ Très facile", 2: "●●○ Facile", 3: "●●● Un peu plus long"}


def section_recette(r, titre):
    infos = [f"<b>Préparation :</b> {e(r['prep'])}"]
    if r["repos"]:
        infos.append(f"<b>Repos :</b> {e(r['repos'])}")
    infos += [f"<b>Cuisson :</b> {e(r['cuisson'])}", f"<b>Pour :</b> {e(r['pour'])}",
              f"<b>Difficulté :</b> {NIVEAU[r['niveau']]}"]
    return (f'<h1 id="{r["id"]}">{e(titre)}</h1>'
            f'<div class="photo"><img src="images/{r["id"]}.jpg" alt="{e(titre)}"/></div>'
            f'<p class="desc">{e(r["desc"])}</p>'
            f'<p class="infos">{" · ".join(infos)}</p>'
            f'<h2>Ingrédients</h2><ul class="ing">{"".join(ingredient(i) for i in r["ing"])}</ul>'
            f'<h2>Préparation</h2><ol class="etapes">{"".join(f"<li>{e(s)}</li>" for s in r["etapes"])}</ol>'
            f'<p class="astuce"><b>L\'astuce :</b> {e(r["astuce"])}</p>')


def images():
    """Photos allégées pour Kindle (le poids du fichier réduit la marge à 70 %)."""
    out = {}
    for rid, t, c, q in RECETTES:
        im = Image.open(os.path.join(PHOTOS, rid + ".jpg")).convert("RGB")
        im.thumbnail((720, 720))
        from io import BytesIO
        b = BytesIO()
        im.save(b, "JPEG", quality=70, optimize=True, progressive=True)
        out[rid] = b.getvalue()
    return out


def main():
    R = toutes()
    imgs = images()
    fichiers = []  # (id, href, contenu, media-type, propriétés)

    # page de titre
    fichiers.append(("titre", "titre.xhtml", xhtml(TITRE,
        f'<h1 class="chap" style="page-break-before:avoid">{e(TITRE)}</h1><p class="centre"><i>{e(SOUS_TITRE)}</i></p>'
        f'<p class="centre petit" style="margin-top:3em">© 2026 — Tous droits réservés. Usage personnel uniquement.</p>'
        f'<p class="centre petit">Les temps de cuisson sont donnés pour un four à chaleur tournante. Les recettes contiennent des allergènes courants (gluten, œufs, lait, fruits à coque).</p>'),
        "application/xhtml+xml", ""))

    # avant de commencer
    fichiers.append(("avant", "avant.xhtml", xhtml("Avant de commencer",
        '<h1 id="avant">Avant de commencer</h1><h2>Le petit matériel</h2><ul class="liste">'
        + "".join(f"<li>{x}</li>" for x in ["Une balance de cuisine", "Deux saladiers", "Un fouet et une spatule",
                                             "Un moule rond de 22 cm", "Un moule à cake", "Un moule à muffins",
                                             "La plaque du four et du papier cuisson", "Une casserole",
                                             "Un batteur électrique (pratique, pas obligatoire)"])
        + '</ul><h2>6 conseils</h2><ol class="etapes">'
        + "".join(f"<li>{x}</li>" for x in ["<b>Lisez la recette en entier</b> avant de commencer.",
                                             "<b>Pesez tout</b> avec une balance : c'est le secret.",
                                             "<b>Préchauffez le four</b> 15 minutes avant.",
                                             "<b>Sortez le beurre et les œufs</b> 30 minutes avant.",
                                             "<b>Ne mélangez pas trop</b> une fois la farine ajoutée.",
                                             "<b>Testez avec un couteau</b> : s'il ressort sec, c'est cuit."])
        + '</ol><p class="astuce"><b>Avec les enfants :</b> ils pèsent, versent, mélangent et décorent. Le four, les plaques chaudes, le caramel et les couteaux restent l\'affaire des grands.</p>'),
        "application/xhtml+xml", ""))

    # chapitres
    nav_items = []
    for k, (cid, ct) in enumerate(CHAPITRES, 1):
        recs = [(rid, t) for rid, t, c, q in RECETTES if c == cid]
        href = f"chap{k:02d}.xhtml"
        corps = (f'<h1 class="chap" id="ch{k}">{k:02d}<br/>{e(ct)}</h1><ul class="liste">'
                 + "".join(f'<li><a href="#{rid}">{e(t)}</a></li>' for rid, t in recs) + "</ul>"
                 + "".join(section_recette(R[rid], t) for rid, t in recs))
        fichiers.append((f"chap{k:02d}", href, xhtml(ct, corps), "application/xhtml+xml", ""))
        nav_items.append((href + f"#ch{k}", f"{k:02d}. {ct}", [(href + "#" + rid, t) for rid, t in recs]))

    # crédits photos
    cr = []
    for rid, t, c, q in RECETTES:
        ref = __import__("photos_choix").CHOIX[rid]
        src_id, idx = ref.rsplit("-", 1)
        second = idx.startswith("b")
        n = int(idx[1:] if second else idx)
        meta = json.load(open(os.path.join(ROOT, "build", "candidats", src_id + (".2.json" if second else ".json"))))[n]
        lic = "domaine public (CC0)" if meta["license"] in ("cc0", "pdm") else f'CC {meta["license"].upper()} {meta.get("license_version") or ""}'.strip()
        aut = f" — {meta['creator']}" if meta.get("creator") else ""
        cr.append(f"<p>{e(t)}{e(aut)}, {e(lic)}, {e(meta['source'])} : {e(meta.get('foreign_landing_url') or '')}</p>")
    fichiers.append(("credits", "credits.xhtml", xhtml("Crédits photos",
        '<h1 id="credits">Crédits photos</h1><div class="credits"><p>Photographies sous licence libre (domaine public CC0 '
        'ou Creative Commons Attribution CC BY), utilisées avec l\'attribution demandée par leurs auteurs.</p>' + "".join(cr) + "</div>"),
        "application/xhtml+xml", ""))

    # table des matières (EPUB 3 + NCX pour les anciennes liseuses)
    nav_ol = '<li><a href="avant.xhtml#avant">Avant de commencer</a></li>' + "".join(
        f'<li><a href="{h}">{e(t)}</a><ol>' + "".join(f'<li><a href="{hh}">{e(tt)}</a></li>' for hh, tt in sous) + "</ol></li>"
        for h, t, sous in nav_items) + '<li><a href="credits.xhtml#credits">Crédits photos</a></li>'
    nav = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{LANG}" lang="{LANG}">
<head><meta charset="utf-8"/><title>Sommaire</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body><nav epub:type="toc" id="toc"><h1 style="page-break-before:avoid">Sommaire</h1><ol>{nav_ol}</ol></nav>
<nav epub:type="landmarks" hidden="hidden"><ol><li><a epub:type="toc" href="nav.xhtml">Sommaire</a></li>
<li><a epub:type="bodymatter" href="chap01.xhtml">Recettes</a></li></ol></nav></body></html>"""

    po = [1]

    def np(label, src, enfants=()):
        i = po[0]
        po[0] += 1
        sub = "".join(np(t, h) for h, t in enfants)
        return f'<navPoint id="n{i}" playOrder="{i}"><navLabel><text>{e(label)}</text></navLabel><content src="{src}"/>{sub}</navPoint>'
    ncx_pts = np("Avant de commencer", "avant.xhtml") + "".join(np(t, h, sous) for h, t, sous in nav_items) + np("Crédits photos", "credits.xhtml")
    ncx = f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="{UID}"/></head>
<docTitle><text>{e(TITRE)}</text></docTitle><navMap>{ncx_pts}</navMap></ncx>"""

    # couverture
    couv = xhtml("Couverture", '<div class="centre"><img src="images/couverture.jpg" alt="Couverture" style="width:100%"/></div>')

    spine = ["couv", "titre", "nav", "avant"] + [f"chap{k:02d}" for k in range(1, len(CHAPITRES) + 1)] + ["credits"]
    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
                '<item id="css" href="style.css" media-type="text/css"/>',
                '<item id="couv" href="couverture.xhtml" media-type="application/xhtml+xml"/>',
                '<item id="img-couv" href="images/couverture.jpg" media-type="image/jpeg" properties="cover-image"/>']
    for fid, href, _, mt, pr in fichiers:
        manifest.append(f'<item id="{fid}" href="{href}" media-type="{mt}"/>')
    for rid in imgs:
        manifest.append(f'<item id="img-{re.sub(r"[^a-z0-9-]", "", rid)}" href="images/{rid}.jpg" media-type="image/jpeg"/>')
    modifie = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="{LANG}">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="uid">{UID}</dc:identifier><dc:title>{e(TITRE)}</dc:title><dc:language>{LANG}</dc:language>
<dc:description>{e(SOUS_TITRE)}</dc:description><meta property="dcterms:modified">{modifie}</meta>
<meta name="cover" content="img-couv"/>
</metadata>
<manifest>{"".join(manifest)}</manifest>
<spine toc="ncx">{"".join(f'<itemref idref="{s}"/>' for s in spine)}</spine>
<guide><reference type="cover" title="Couverture" href="couverture.xhtml"/><reference type="toc" title="Sommaire" href="nav.xhtml"/></guide>
</package>"""

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(OUT, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>', compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/toc.ncx", ncx, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/style.css", CSS, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/couverture.xhtml", couv, compress_type=zipfile.ZIP_DEFLATED)
        im = Image.open(COUV).convert("RGB")
        im.thumbnail((1000, 1600))
        from io import BytesIO
        b = BytesIO()
        im.save(b, "JPEG", quality=82)
        z.writestr("OEBPS/images/couverture.jpg", b.getvalue(), compress_type=zipfile.ZIP_STORED)
        for fid, href, contenu, mt, pr in fichiers:
            z.writestr("OEBPS/" + href, contenu, compress_type=zipfile.ZIP_DEFLATED)
        for rid, data in imgs.items():
            z.writestr(f"OEBPS/images/{rid}.jpg", data, compress_type=zipfile.ZIP_STORED)
    print(OUT, round(os.path.getsize(OUT) / 1e6, 1), "Mo")


if __name__ == "__main__":
    main()
