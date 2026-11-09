"""Assemble le livre complet : python3 src/livre.py -> src/livre.html (puis node src/render.js livre)."""
import html
import json
import os
import re
import shutil
import sys
import unicodedata

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from liste import CHAPITRES, RECETTES  # noqa: E402
from recettes import toutes  # noqa: E402
from photos_choix import CHOIX, COUVERTURE, HEROS  # noqa: E402

CAND = os.path.join(ROOT, "build", "candidats")
PHOTOS = os.path.join(ROOT, "photos", "recettes")
TITRE = "Mes recettes de pâtisserie"
SOUS_TITRE = "100 gâteaux simples et gourmands à réaliser chez soi"

e = lambda t: html.escape(t, quote=False)  # noqa: E731


# ------------------------------------------------------------------ photos
def preparer_photos():
    """Copie chaque photo choisie dans photos/recettes/<id>.jpg et relève ses crédits."""
    os.makedirs(PHOTOS, exist_ok=True)
    credits, formats = {}, {}
    for rid, ref in list(CHOIX.items()) + [("chap-" + k, v) for k, v in HEROS.items()]:
        src_id, idx = ref.rsplit("-", 1)
        second = idx.startswith("b")
        n = int(idx[1:] if second else idx)
        meta = json.load(open(os.path.join(CAND, src_id + (".2.json" if second else ".json"))))[n]
        src = os.path.join(CAND, "img", f"{src_id}-{idx}.jpg")
        dst = os.path.join(PHOTOS, rid + ".jpg")
        im = Image.open(src).convert("RGB")
        im.thumbnail((1800, 1800))
        im.save(dst, quality=86)
        formats[rid] = im.width / im.height
        credits[rid] = dict(titre=meta.get("title") or "", auteur=meta.get("creator") or "",
                            licence=meta["license"].upper(), version=meta.get("license_version") or "",
                            source=meta.get("foreign_landing_url") or "", site=meta["source"])
    return credits, formats


# ------------------------------------------------------------------ mise en forme
QTE = re.compile(r"^((?:\d+[\d,./]*|½|⅓|¼|¾|un|une)\s*(?:g|kg|ml|cl|c\. à soupe|c\. à café|pots?|sachets?|gros|grande|grandes|petits?|tranches?|feuilles?|boules?)?\b)", re.I)


def ingredient(t):
    if ":" in t and t.index(":") < 30:  # « Pour le glaçage : … »
        a, b = t.split(":", 1)
        return f'<li class="sous"><b>{e(a.strip())}</b> : {e(b.strip())}</li>'
    m = QTE.match(t)
    if m and m.group(1).strip():
        q = m.group(1)
        return f"<li><b>{e(q.strip())}</b> {e(t[len(q):].lstrip())}</li>"
    return f"<li>{e(t)}</li>"


def niveau(n):
    lab = {1: "Très facile", 2: "Facile", 3: "Un peu plus long"}[n]
    dots = "".join(f'<i class="{"on" if k <= n else ""}"></i>' for k in (1, 2, 3))
    return f'<span class="dots">{dots}</span>{lab}'


def meta(r):
    cells = [("Préparation", r["prep"])]
    if r["repos"]:
        cells.append(("Repos", r["repos"]))
    cells.append(("Cuisson", r["cuisson"]))
    cells.append(("Pour", r["pour"]))
    out = "".join(f"<div><small>{k}</small><strong>{e(v)}</strong></div>" for k, v in cells)
    return f'<div class="meta">{out}<div><small>Difficulté</small><strong>{niveau(r["niveau"])}</strong></div></div>'


def folio(n, ch, droite=True):
    if droite:
        return f'<div class="folio r">{e(ch)}<b>{n}</b></div>'
    return f'<div class="folio l"><b>{n}</b>{e(ch)}</div>'


def page_recette(r, titre, chap, n, ratio):
    ing = "".join(ingredient(i) for i in r["ing"])
    etapes = "".join(f"<li>{e(s)}</li>" for s in r["etapes"])
    astuce = f'<div class="tip"><span class="hand">L\'astuce</span><p>{e(r["astuce"])}</p></div>'
    tete = (f'<span class="pill">{e(chap)}</span><h1 id="{r["id"]}">{e(titre)}</h1>'
            f'<p class="desc">{e(r["desc"])}</p>{meta(r)}')
    photo = f'<div class="photo"><img src="../photos/recettes/{r["id"]}.jpg" alt=""></div>'
    if ratio < 1.0:  # photo verticale : colonne à gauche
        corps = (f'<div class="ing"><h3>Ingrédients</h3><ul>{ing}</ul></div>'
                 f'<div class="steps"><h3>Préparation</h3><ol>{etapes}</ol></div>{astuce}')
        return f'<section class="page recipe rB">{photo}<div class="inner fit">{tete}{corps}</div>{folio(n, chap)}</section>'
    corps = (f'<div class="grid"><div class="ing"><h3>Ingrédients</h3><ul>{ing}</ul></div>'
             f'<div class="steps"><h3>Préparation</h3><ol>{etapes}</ol>{astuce}</div></div>')
    return f'<section class="page recipe rA">{photo}<div class="inner fit">{tete}{corps}</div>{folio(n, chap)}</section>'


def page_chapitre(num, titre, recs, pages, hero, n):
    lignes = "".join(f'<a href="#{rid}"><span>{e(t)}</span><span class="pg">{pages[rid]}</span></a>' for rid, t in recs)
    return (f'<section class="page opener"><div class="photo"><img src="../photos/recettes/{hero}.jpg" alt=""></div>'
            f'<div class="inner"><span class="num">{num:02d}</span><h1 id="ch-{num}">{e(titre)}</h1>'
            f'<div class="liste">{lignes}</div></div>{folio(n, titre)}</section>')


def page_couverture():
    return f'''<section class="page cover">
  <div class="photo"><img src="../photos/recettes/{COUVERTURE}.jpg" alt=""></div>
  <div class="sticker">100<br>recettes</div>
  <div class="band"><h1>Mes recettes<br><em>de pâtisserie</em></h1><p class="sub">{e(SOUS_TITRE)}</p></div>
  <div class="foot"><span>Simples · Rapides · Gourmandes</span><span>Pour débuter et cuisiner en famille</span></div>
</section>'''


def pages_sommaire(pages, chap_pages):
    blocs = []
    for k, (cid, ct) in enumerate(CHAPITRES, 1):
        recs = [(rid, t) for rid, t, c, q in RECETTES if c == cid]
        items = "".join(f'<a href="#{rid}"><span>{e(t)}</span><i></i><span class="pg">{pages[rid]}</span></a>' for rid, t in recs)
        blocs.append(f'<div class="bloc"><a class="ch" href="#ch-{k}"><span class="n">{k:02d}</span>{e(ct)}<span class="pg">{chap_pages[cid]}</span></a>{items}</div>')
    p1 = "".join(blocs[:5])
    p2 = "".join(blocs[5:])
    return [
        f'<section class="page sommaire"><div class="inner"><span class="label">Toutes les recettes</span><h1 id="sommaire">Sommaire</h1><div class="cols">{p1}</div></div>{folio(2, "Sommaire", False)}</section>',
        f'<section class="page sommaire"><div class="inner"><span class="label">Toutes les recettes</span><div class="cols" style="margin-top:6mm">{p2}</div>'
        f'<div class="extra"><a href="#avant"><span>Avant de commencer</span><span class="pg">4</span></a><a href="#index"><span>Index alphabétique</span><span class="pg">{pages["__index"]}</span></a></div></div>{folio(3, "Sommaire")}</section>',
    ]


def page_avant():
    return f'''<section class="page avant"><div class="inner">
<span class="label">Avant de commencer</span><h1 id="avant">Le petit matériel et 6 conseils</h1>
<div class="two">
 <div class="card"><h3>Le matériel</h3><ul class="check">
  <li>Une balance de cuisine</li><li>Deux saladiers</li><li>Un fouet et une spatule</li><li>Un moule rond de 22 cm</li>
  <li>Un moule à cake</li><li>Un moule à muffins</li><li>La plaque du four et du papier cuisson</li><li>Une casserole</li>
  <li>Un batteur électrique (pratique, pas obligatoire)</li></ul></div>
 <div class="tips6">
  <div><span class="n">1</span><p><b>Lisez la recette en entier</b> avant de commencer.</p></div>
  <div><span class="n">2</span><p><b>Pesez tout</b> avec une balance : c'est le secret.</p></div>
  <div><span class="n">3</span><p><b>Préchauffez le four</b> 15 minutes avant.</p></div>
  <div><span class="n">4</span><p><b>Sortez le beurre et les œufs</b> 30 minutes avant.</p></div>
  <div><span class="n">5</span><p><b>Ne mélangez pas trop</b> une fois la farine ajoutée.</p></div>
  <div><span class="n">6</span><p><b>Testez avec un couteau</b> : s'il ressort sec, c'est cuit.</p></div>
 </div>
</div>
<div class="card rose" style="margin-top:8mm"><h3>Les fours ne chauffent pas tous pareil</h3><p>Les temps sont donnés pour un four à chaleur tournante. Surveillez la fin de cuisson la première fois, et notez votre temps dans la marge.</p></div>
<div class="card" style="margin-top:5mm"><h3>Avec les enfants</h3><p>Les enfants pèsent, versent, mélangent et décorent. Le four, les plaques chaudes, le caramel et les couteaux restent l'affaire des grands.</p></div>
</div>{folio(4, "Avant de commencer")}</section>'''


def cle(t):
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def page_index(pages, n):
    items = sorted(((t, rid) for rid, t, c, q in RECETTES), key=lambda x: cle(x[0]))
    out, last = [], None
    for t, rid in items:
        L = cle(t)[0].upper()
        if L != last:
            out.append(f'<div class="L">{L}</div>')
            last = L
        out.append(f'<a href="#{rid}"><span>{e(t)}</span><i></i><span class="pg">{pages[rid]}</span></a>')
    return f'<section class="page index"><div class="inner"><span class="label">Pour trouver vite</span><h1 id="index">Index</h1><div class="cols">{"".join(out)}</div></div>{folio(n, "Index")}</section>'


titres_globaux = {rid: t for rid, t, c, q in RECETTES}


def page_credits(credits, pages, n):
    lignes = []
    noms = {"chap-" + c: f"Ouverture « {t} »" for c, t in CHAPITRES}
    for rid in [r[0] for r in RECETTES] + list(noms):
        t = titres_globaux.get(rid) or noms[rid]
        cr = credits[rid]
        lic = "domaine public (CC0)" if cr["licence"] in ("CC0", "PDM") else f'{cr["licence"]} {cr["version"]}'.strip()
        aut = f' — {e(cr["auteur"])}' if cr["auteur"] else ""
        pg = pages.get(rid) or pages.get("ch:" + rid[5:], "")
        lignes.append(f'<div><b>p. {pg}</b> {e(t)}{aut}, {lic}, {e(cr["site"])}</div>')
    return (f'<section class="page credits"><div class="inner"><span class="label">Merci</span><h1>Crédits photos</h1>'
            f'<p class="note">Photographies sous licence libre (domaine public CC0 ou Creative Commons Attribution CC BY 2.0/3.0/4.0), '
            f'utilisées avec l\'attribution demandée par leurs auteurs. Les liens vers les originaux sont listés dans le fichier CREDITS.md fourni avec le livre.</p>'
            f'<div class="cols">{"".join(lignes)}</div></div>{folio(n, "Crédits")}</section>')


def main():
    R = toutes()
    credits, formats = preparer_photos()
    titres = {rid: t for rid, t, c, q in RECETTES}
    # pagination : 1 couverture, 2-3 sommaire, 4 avant, puis chapitres
    pages, chap_pages, n = {}, {}, 5
    for cid, ct in CHAPITRES:
        chap_pages[cid] = n
        n += 1
        for rid, t, c, q in RECETTES:
            if c == cid:
                pages[rid] = n
                n += 1
    pages["__index"] = n
    for cid in chap_pages:
        pages["ch:" + cid] = chap_pages[cid]
    html_pages = [page_couverture()] + pages_sommaire(pages, chap_pages) + [page_avant()]
    for k, (cid, ct) in enumerate(CHAPITRES, 1):
        recs = [(rid, t) for rid, t, c, q in RECETTES if c == cid]
        hero = "chap-" + cid
        html_pages.append(page_chapitre(k, ct, recs, pages, hero, chap_pages[cid]))
        for rid, t in recs:
            html_pages.append(page_recette(R[rid], t, ct, pages[rid], formats[rid]))
    html_pages.append(page_index(pages, n))
    html_pages.append(page_credits(credits, pages, n + 1))
    doc = (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{TITRE}</title>'
           f'<link rel="stylesheet" href="style.css"><link rel="stylesheet" href="livre.css"></head><body>{"".join(html_pages)}</body></html>')
    open(os.path.join(HERE, "livre.html"), "w").write(doc)
    # crédits détaillés
    with open(os.path.join(ROOT, "CREDITS.md"), "w") as f:
        f.write("# Crédits photos\n\n| Page | Recette | Auteur | Licence | Source |\n|---|---|---|---|---|\n")
        for rid, t, c, q in RECETTES:
            cr = credits[rid]
            f.write(f'| {pages[rid]} | {t} | {cr["auteur"]} | {cr["licence"]} {cr["version"]} | {cr["source"]} |\n')
    print(f"{len(html_pages)} pages")


if __name__ == "__main__":
    main()
