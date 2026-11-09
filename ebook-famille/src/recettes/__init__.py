"""Les 100 recettes. Chaque fiche est complète : aucune recette ne renvoie à une autre."""
import importlib


def R(rid, desc, prep, cuisson, pour, niveau, ing, etapes, astuce, repos=None):
    return dict(id=rid, desc=desc, prep=prep, cuisson=cuisson, repos=repos, pour=pour, niveau=niveau,
                ing=ing, etapes=etapes, astuce=astuce)


MODULES = ["c01_gateaux", "c02_cookies", "c03_muffins", "c04_chocolat", "c05_tartes",
           "c06_sans_cuisson", "c07_verrines", "c08_fruits", "c09_gouters", "c10_enfants"]


def toutes():
    out = {}
    for m in MODULES:
        for r in importlib.import_module(f"{__name__}.{m}").RECETTES:
            out[r["id"]] = r
    return out
