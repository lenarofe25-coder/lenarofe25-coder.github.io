"""Recettes : un fichier par chapitre. Chaque recette est créée avec R(...)."""
import re
import unicodedata


def slugify(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def R(t, d, lvl, prep, cook, rest, serv, oven, ing, ust, steps, tips, err, cons, img, mode="chaleur tournante", slug=None, **kw):
    """Fiche recette.

    oven : « 170 °C » (court) ; mode : chaleur tournante / statique ; « — » = sans four.
    ing  : liste de groupes ; un groupe = liste de lignes, ou (« Pour la pâte », [lignes]).
    steps: « Titre | texte » ; « @slug » renvoie vers une préparation de base.
    """
    r = dict(t=t, d=d, lvl=lvl, prep=prep, cook=cook, rest=rest, serv=serv, oven=oven, ing=ing, ust=ust,
             steps=steps, tips=tips, err=err, cons=cons, img=img, slug=slug or slugify(t))
    if oven in ("—", "-", ""):
        r["oven"] = "Sans four"
        r["oven_long"] = "Aucune cuisson au four"
    else:
        r["oven_long"] = f"{oven}, {mode}" + (f" · {kw['oven_note']}" if kw.get("oven_note") else "")
    r.update({k: v for k, v in kw.items() if k != "oven_note"})
    return r


import importlib  # noqa: E402

MODULES = ["c1_gateaux", "c2_tartes", "c3_biscuits", "c4_entremets", "c5_individuels",
           "c6_gourmandises", "c7_sans_cuisson", "c8_viennoiseries", "c9_fruits"]
CHAPTERS = []
for _m in MODULES:
    try:
        CHAPTERS.append(importlib.import_module(f"{__name__}.{_m}").CHAPTER)
    except ModuleNotFoundError as e:
        if _m not in str(e):
            raise
