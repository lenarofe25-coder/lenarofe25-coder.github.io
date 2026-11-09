"""Assemble le livre : contenu (src/content) + illustrations -> build/book.html.

Usage :
    python3 src/build.py            # livre complet
    python3 src/build.py maquette   # quelques pages représentatives
"""
import html
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import illus  # noqa: E402
from content import front, annexes, bases  # noqa: E402
from content.recipes import CHAPTERS  # noqa: E402
import config  # noqa: E402

BUILD = os.path.join(ROOT, "build")
SVG_DIR = os.path.join(BUILD, "svg")
IMG_DIR = os.path.join(BUILD, "img")
PHOTOS = os.path.join(ROOT, "photos")


# --------------------------------------------------------------- utilitaires
def esc(t):
    return html.escape(t, quote=False)


def slugify(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def image(slug):
    """Photo fournie par l'utilisatrice si présente, sinon illustration générée."""
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = os.path.join(PHOTOS, slug + ext)
        if os.path.exists(p):
            return "../photos/" + slug + ext
    return "img/" + slug + ".jpg"


def roman(n):
    return ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"][n]


ORN = ('<svg class="orn{cls}" viewBox="0 0 200 16"><path d="M0 8 H82 M118 8 H200" stroke="#B48E4F" stroke-width=".8"/>'
       '<path d="M100 1 L107 8 L100 15 L93 8 Z" fill="none" stroke="#B48E4F" stroke-width=".9"/>'
       '<circle cx="100" cy="8" r="1.8" fill="#B48E4F"/><circle cx="86" cy="8" r="1.2" fill="#B48E4F"/>'
       '<circle cx="114" cy="8" r="1.2" fill="#B48E4F"/></svg>')


def orn(cls=""):
    return ORN.format(cls=(" " + cls) if cls else "")


G = 'fill="none" stroke="#B48E4F" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"'
ICONS = {
    "lvl": f'<svg viewBox="0 0 24 24" {G}><path d="M12 2v7"/><path d="M8.5 9c-1.5 4-1 9 3.5 13 4.5-4 5-9 3.5-13z"/><path d="M10 12c0 3 .7 5.5 2 7.5M14 12c0 3-.7 5.5-2 7.5"/></svg>',
    "prep": f'<svg viewBox="0 0 24 24" {G}><circle cx="12" cy="13" r="8"/><path d="M12 9v4l3 2M10 2h4M12 2v3"/></svg>',
    "cook": f'<svg viewBox="0 0 24 24" {G}><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 8h18"/><rect x="6.5" y="11" width="11" height="6" rx="1"/><circle cx="7" cy="6" r=".6"/><circle cx="10" cy="6" r=".6"/></svg>',
    "rest": f'<svg viewBox="0 0 24 24" {G}><path d="M6 2h12M6 22h12M7 2c0 6 10 6 10 10S7 16 7 22M17 2c0 6-10 6-10 10s10 4 10 10"/></svg>',
    "serv": f'<svg viewBox="0 0 24 24" {G}><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5.5"/><path d="M12 3v3"/></svg>',
    "oven": f'<svg viewBox="0 0 24 24" {G}><path d="M12 2v13"/><circle cx="12" cy="18" r="4"/><path d="M15 5h2M15 8h2M15 11h2"/></svg>',
    "tip": f'<svg viewBox="0 0 24 24" {G}><path d="M12 2l2.6 6.2L21 9l-5 4.4L17.5 20 12 16.6 6.5 20 8 13.4 3 9l6.4-.8z"/></svg>',
    "err": f'<svg viewBox="0 0 24 24" {G}><path d="M12 3L2 21h20z"/><path d="M12 10v5M12 18v.5"/></svg>',
    "cons": f'<svg viewBox="0 0 24 24" {G}><rect x="5" y="7" width="14" height="14" rx="2"/><path d="M7 3h10v4H7zM9 12h6"/></svg>',
    "tools": f'<svg viewBox="0 0 24 24" {G}><path d="M8 2v9M5 2v5a3 3 0 0 0 6 0V2M8 11v11M17 2c-2 0-3 3-3 7h3v13"/></svg>',
    "note": f'<svg viewBox="0 0 24 24" {G}><path d="M4 20l4-1L19 8l-3-3L5 16zM14 7l3 3"/></svg>',
}

LEVELS = {1: "Facile", 2: "Intermédiaire", 3: "Avancé"}


class Book:
    def __init__(self):
        self.pages = []          # (callable -> html) ; numérotation déterminée avant rendu
        self.anchors = {}        # id -> page
        self.toc = []            # (niveau, titre, id)
        self.svg_specs = {}

    def reserve(self, n, fn, anchor=None):
        start = len(self.pages) + 1
        if anchor:
            self.anchors[anchor] = start
        for k in range(n):
            self.pages.append((fn, k))
        return start

    def pg(self, anchor):
        return self.anchors.get(anchor, "?")


B = Book()


def folio(n, label=None):
    label = label or config.TITLE.upper()
    return f'<div class="folio">{esc(label)}<b>{n}</b>{esc(config.SHORT.upper())}</div>'


def runhead(left, right):
    return f'<div class="runhead"><span>{esc(left)}</span><span>{esc(right)}</span></div>'


def see_refs(text):
    """« @pate-sucree » -> renvoi de page cliquable vers la préparation de base."""
    def rep(m):
        a = "base-" + m.group(1)
        return f' <span class="see"><a href="#{a}">→ p. {B.pg(a)}</a></span>'
    text = re.sub(r"\s*@([a-z0-9-]+)", rep, text)
    return re.sub(r"\s*§([a-z0-9-]+)", lambda m: f' <span class="see"><a href="#{m.group(1)}">→ p. {B.pg(m.group(1))}</a></span>', text)


def inline(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return see_refs(t)


# --------------------------------------------------------------- fiches
def meta_html(r):
    lvl = r["lvl"]
    dots = "".join(f'<i class="{"on" if i <= lvl else ""}"></i>' for i in (1, 2, 3))
    cells = [
        ("lvl", "Difficulté", f'<span class="lvl">{dots}</span><div class="v small">{LEVELS[lvl]}</div>'),
        ("prep", "Préparation", f'<div class="v">{esc(r["prep"])}</div>'),
        ("cook", "Cuisson", f'<div class="v">{esc(r["cook"])}</div>'),
        ("rest", "Repos", f'<div class="v">{esc(r["rest"])}</div>'),
        ("serv", "Portions", f'<div class="v small">{esc(r["serv"])}</div>'),
        ("oven", "Four", f'<div class="v small">{esc(r["oven"])}</div>'),
    ]
    return '<div class="meta">' + "".join(
        f'<div>{ICONS[i]}<div class="k">{k}</div>{v}</div>' for i, k, v in cells) + '</div>'


def ing_html(r, two=False):
    out = [f'<div class="ing{" two" if two else ""}"><div class="blk-title">Ingrédients</div>']
    for grp in r["ing"]:
        out.append('<div class="g">')
        if isinstance(grp, tuple):
            name, items = grp
            out.append(f'<div class="grp">{esc(name)}</div>')
        else:
            items = grp
        out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul></div>")
    out.append("</div>")
    return "".join(out)


def ing_count(r):
    n = 0
    for grp in r["ing"]:
        if isinstance(grp, tuple):
            n += 1.6 + len(grp[1])
        else:
            n += len(grp)
    return n


def tools_html(r, boxed=True):
    lis = "".join(f"<li>{inline(t)}</li>" for t in r["ust"])
    oven = f'<div class="oven"><span class="kicker">Température du four</span>{esc(r["oven_long"])}</div>' if r.get("oven_long") else ""
    return f'<div class="tools"><div class="blk-title">Ustensiles</div><ul>{lis}</ul>{oven}</div>'


def variant(r, i):
    heavy = ing_count(r) > 17
    if r.get("variant"):
        return r["variant"], heavy
    return ("A" if i % 2 == 0 else "C"), heavy


def recipe_page1(r, chap, n, var, heavy):
    head = (f'<div class="head"><div class="kicker">{esc(chap["title"])}</div>'
            f'<h2 class="rt" id="{r["slug"]}">{esc(r["t"])}</h2>{orn()}'
            f'<p class="desc">{esc(r["d"])}</p></div>')
    if heavy:
        body = f'<div class="cols" style="grid-template-columns:1fr">{ing_html(r, two=True)}</div>'
    else:
        body = f'<div class="cols">{ing_html(r)}{tools_html(r)}</div>'
    short = " short" if ing_count(r) > 11 and var != "B" else ""
    return (f'<section class="page r1 v{var}{short}"><div class="hero"><img src="{image(r["slug"])}" alt=""></div>'
            f'<div class="fit">{head}{meta_html(r)}{body}</div>{folio(n)}</section>')


def recipe_page2(r, chap, n, heavy):
    steps = []
    for k, st in enumerate(r["steps"], 1):
        if " | " in st:
            lab, txt = st.split(" | ", 1)
            st_html = f"<b>{esc(lab)}</b>{inline(txt)}"
        else:
            st_html = inline(st)
        steps.append(f'<div class="step"><div class="n">{k}</div><p>{st_html}</p></div>')
    side = []
    if heavy:
        side.append(f'<div class="box">{"<div class=bh>" + ICONS["tools"] + "Ustensiles</div>"}<ul>'
                    + "".join(f"<li>{inline(t)}</li>" for t in r["ust"]) + "</ul></div>")
    side.append(f'<div class="box tip"><div class="bh">{ICONS["tip"]}Conseils de réussite</div><ul>'
                + "".join(f"<li>{inline(t)}</li>" for t in r["tips"]) + "</ul></div>")
    side.append(f'<div class="box err"><div class="bh">{ICONS["err"]}Erreurs à éviter</div><ul>'
                + "".join(f"<li>{inline(t)}</li>" for t in r["err"]) + "</ul></div>")
    side.append(f'<div class="box cons"><div class="bh">{ICONS["cons"]}Conservation</div><p>{inline(r["cons"])}</p></div>')
    side.append(f'<div class="box notes"><div class="bh">{ICONS["note"]}Mes notes</div><div class="notes-lines"></div></div>')
    oven = f'<span class="kicker">{esc(r["oven_long"] if r.get("oven_long") else r["oven"])}</span>'
    return (f'<section class="page r2">{runhead(chap["title"], r["t"])}'
            f'<div class="fit"><div class="hd"><div class="h2">Préparation</div>{oven}</div>'
            f'<div class="steps">{"".join(steps)}</div><div class="side">{"".join(side)}</div></div>{folio(n)}</section>')


def base_page(b, n):
    steps = []
    for k, st in enumerate(b["steps"], 1):
        if " | " in st:
            lab, txt = st.split(" | ", 1)
            st_html = f"<b>{esc(lab)}</b>{inline(txt)}"
        else:
            st_html = inline(st)
        steps.append(f'<div class="step"><div class="n">{k}</div><p>{st_html}</p></div>')
    mini = "".join(f"<div><b>{esc(k)}</b>{esc(v)}</div>" for k, v in b["info"])
    tips = "".join(f"<li>{inline(t)}</li>" for t in b["tips"])
    uses = ""
    if b.get("uses"):
        uses = (f'<div class="box cons"><div class="bh">{ICONS["serv"]}Utilisée dans</div><p>'
                + ", ".join(f'<a href="#{s}" style="color:inherit;text-decoration:none">{esc(t)}</a>' for s, t in b["uses"]) + "</p></div>")
    return (f'<section class="page rb">{runhead("Préparations de base", b["t"])}<div class="fit">'
            f'<div class="head"><div><div class="kicker">Base n° {b["num"]:02d}</div>'
            f'<h2 class="rt" id="base-{b["slug"]}">{esc(b["t"])}</h2><p class="desc">{esc(b["d"])}</p></div>'
            f'<div class="mini">{mini}</div></div>'
            f'<div class="grid"><div>{ing_html(b)}<div class="side">'
            f'<div class="box tip"><div class="bh">{ICONS["tip"]}Les clés de la réussite</div><ul>{tips}</ul></div>{uses}</div></div>'
            f'<div><div class="blk-title">Méthode</div><div class="steps">{"".join(steps)}</div></div></div>'
            f'</div>{folio(n)}</section>')


def opener_page(chap, idx, n):
    items = "".join(f'<a href="#{r["slug"]}"><span>{esc(r["t"])}</span><span class="dots"></span><span class="pg">{B.pg(r["slug"])}</span></a>'
                    for r in chap["recipes"])
    return (f'<section class="page opener"><div class="frame"></div>'
            f'<div class="num"><span class="script">Chapitre</span><span class="roman">{roman(idx)}</span></div>'
            f'<h1 id="ch-{chap["id"]}">{esc(chap["title"])}</h1>'
            f'<div class="circle"><img src="{image(chap["hero"])}" alt=""></div>'
            f'<div class="intro">{esc(chap["intro"])}</div><div class="list">{items}</div>{folio(n)}</section>')


def section_opener(title, sub, intro, img, anchor, n, num_label):
    return (f'<section class="page opener"><div class="frame"></div>'
            f'<div class="num"><span class="script">{esc(num_label)}</span><span class="roman">{esc(sub)}</span></div>'
            f'<h1 id="{anchor}">{esc(title)}</h1>'
            f'<div class="circle"><img src="{image(img)}" alt=""></div>'
            f'<div class="intro">{esc(intro)}</div>{folio(n)}</section>')


# --------------------------------------------------------------- plan du livre
def plan(maquette=False):
    chapters = CHAPTERS
    all_recipes = [r for c in chapters for r in c["recipes"]]
    for r in all_recipes:
        B.svg_specs[r["slug"]] = r["img"]

    B.reserve(1, lambda n, k: front.cover(image(config.COVER_IMAGE)), "cover")
    B.reserve(1, lambda n, k: front.presentation(n, folio), "presentation")
    B.reserve(1, lambda n, k: front.mentions(n, folio), "mentions")
    if maquette:
        B.reserve(1, lambda n, k: front.charte(n, folio, image), "charte")
    B.reserve(2, lambda n, k: toc_page(n, k), "sommaire")
    for sec in front.SECTIONS:
        B.reserve(len(sec["pages"]), (lambda s: lambda n, k: s["pages"][k](n, folio, B))(sec), sec["id"])
        B.toc.append((0, sec["title"], sec["id"]))

    # préparations de base
    bl = bases.BASES
    B.reserve(1, lambda n, k: section_opener("Préparations de base", "LES FONDATIONS",
                                             bases.INTRO, bases.HERO, "bases", n, "Partie"), "bases")
    B.toc.append((0, "Préparations de base", "bases"))
    for i, b in enumerate(bl, 1):
        b["num"] = i
        if maquette and i > 2:
            continue
        B.reserve(1, (lambda b: lambda n, k: base_page(b, n))(b), "base-" + b["slug"])
        B.toc.append((1, b["t"], "base-" + b["slug"]))

    # chapitres
    for ci, chap in enumerate(chapters, 1):
        if maquette and ci not in (1, 4):
            continue
        B.reserve(1, (lambda c, ci: lambda n, k: opener_page(c, ci, n))(chap, ci), "ch-" + chap["id"])
        B.toc.append((0, chap["title"], "ch-" + chap["id"]))
        recs = chap["recipes"] if not maquette else chap["recipes"][:3]
        for ri, r in enumerate(recs):
            var, heavy = variant(r, ri)
            B.reserve(2, (lambda r, c, var, heavy: lambda n, k: recipe_page1(r, c, n, var, heavy) if k == 0
                          else recipe_page2(r, c, n, heavy))(r, chap, var, heavy), r["slug"])
            B.toc.append((1, r["t"], r["slug"]))

    # annexes
    B.reserve(1, lambda n, k: section_opener("Guides & annexes", "LE CARNET DU PÂTISSIER", annexes.INTRO,
                                             annexes.HERO, "annexes", n, "Partie"), "annexes")
    B.toc.append((0, "Guides & annexes", "annexes"))
    for a in annexes.PAGES:
        if maquette and a["id"] not in ("conversions", "chocolats"):
            continue
        B.reserve(a["n"], (lambda a: lambda n, k: a["fn"](n, k, folio, B))(a), a["id"])
        B.toc.append((1, a["title"], a["id"]))
    if not maquette:
        B.reserve(annexes.INDEX_PAGES, lambda n, k: annexes.index_page(n, k, folio, B, all_recipes, bl), "index")
        B.toc.append((1, "Index alphabétique", "index"))
        B.reserve(2, lambda n, k: annexes.notes_page(n, k, folio), "notes")
        B.toc.append((1, "Mes notes personnelles", "notes"))
        B.reserve(1, lambda n, k: front.back_cover(image(config.BACK_IMAGE)), "back")


def toc_page(n, k):
    entries = []
    for lvl, title, anchor in B.toc:
        p = B.pg(anchor)
        if lvl == 0:
            entries.append(f'<a href="#{anchor}" class="sec"><span class="lbl">{esc(title)}</span><span class="dots"></span><span class="pg">{p}</span></a>')
        else:
            entries.append(f'<a href="#{anchor}" class="it"><span class="lbl">{esc(title)}</span><span class="dots"></span><span class="pg">{p}</span></a>')
    # découpage en deux pages, à une frontière de section si possible
    half = (len(entries) + 1) // 2
    cut = half
    for j in range(half, min(len(entries), half + 14)):
        if 'class="sec"' in entries[j]:
            cut = j
            break
    part = entries[:cut] if k == 0 else entries[cut:]
    title = '<div class="kicker">Table des matières</div><h1 class="h-display" style="font-size:40pt" id="toc">Sommaire</h1>' if k == 0 else \
        '<div class="kicker">Table des matières</div><div class="h-display" style="font-size:28pt">Sommaire <em style="font-size:18pt;color:#B48E4F">(suite)</em></div>'
    return (f'<section class="page"><div class="toc fit">{title}{orn("left")}<div class="tcols">{"".join(part)}</div></div>{folio(n)}</section>')


def write_svgs():
    os.makedirs(SVG_DIR, exist_ok=True)
    specs = dict(B.svg_specs)
    for slug, spec in list(bases.EXTRA_IMAGES.items()) + list(annexes.EXTRA_IMAGES.items()) + list(front.EXTRA_IMAGES.items()):
        specs[slug] = spec
    n = 0
    for slug, spec in specs.items():
        svg = illus.render(slug, spec)
        p = os.path.join(SVG_DIR, slug + ".svg")
        if not os.path.exists(p) or open(p).read() != svg:
            open(p, "w").write(svg)
            n += 1
    return n


def main():
    maquette = len(sys.argv) > 1 and sys.argv[1] == "maquette"
    plan(maquette)
    changed = write_svgs()
    # « Utilisée dans » : relevé automatique des renvois @base dans les recettes
    for b in bases.BASES:
        b["uses"] = [(r["slug"], r["t"]) for c in CHAPTERS for r in c["recipes"]
                     if "@" + b["slug"] in repr(r["ing"]) + repr(r["steps"]) + repr(r["tips"])
                     and r["slug"] in B.anchors]
    by_page = {}
    for a, p in B.anchors.items():
        by_page.setdefault(p, []).append(a)
    pages = []
    for i, (fn, k) in enumerate(B.pages, 1):
        h = fn(i, k)
        if k == 0:
            missing = "".join(f'<a id="{a}"></a>' for a in by_page.get(i, []) if f'id="{a}"' not in h)
            h = h.replace(">", ">" + missing, 1)
        pages.append(h)
    doc = (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{esc(config.TITLE)} — {esc(config.SUBTITLE)}</title>'
           f'<link rel="stylesheet" href="../src/style.css"></head><body>{"".join(pages)}</body></html>')
    import json
    json.dump(B.anchors, open(os.path.join(BUILD, ("maquette" if maquette else "book") + "-anchors.json"), "w"), indent=0)
    out = os.path.join(BUILD, "maquette.html" if maquette else "book.html")
    open(out, "w").write(doc)
    print(f"{len(B.pages)} pages -> {out} ({changed} illustrations modifiées)")


if __name__ == "__main__":
    main()
