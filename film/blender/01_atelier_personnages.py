# -*- coding: utf-8 -*-
"""
FILM LÉNA & RUBEN  ·  Script 01 : l'atelier des personnages
================================================================

Ce que fait ce script (dans Blender 4.2 ou plus récent, testé avec Blender 5.0) :
  1. Vide la scène et règle le projet (mètres, 24 images/seconde, 1920x1080).
  2. Crée les MATÉRIAUX OFFICIELS du film (peau, cheveux, yeux, lèvres, vêtements)
     avec les couleurs relevées sur les vraies photos (voir film/bible/personnages.md).
  3. Construit deux MAQUETTES DE PROPORTIONS (Léna et Ruben) : ce ne sont PAS les
     personnages finaux, ce sont des silhouettes de travail qui fixent la taille,
     le nombre de « têtes », la largeur d'épaules, la taille des yeux, etc.
     Elles servent : (a) de gabarit pour modeler les vrais personnages,
     (b) de doublures pour le story-board 3D (animatique) en attendant.
  4. Ajoute une TOISE (règle de hauteur tous les 10 cm et en « têtes »).
  5. Charge vos PHOTOS de référence (si elles sont dans film/references/photos/).
  6. Installe un STUDIO PHOTO : 3 lumières « Disney » (chaude, douce, contre-jour),
     et 5 caméras : FACE, TROIS_QUARTS, PROFIL, DOS (orthographiques) + PORTRAIT.

Utilisation (débutante) :
  Blender > onglet « Scripting » en haut > bouton « Ouvrir » > choisir ce fichier
  > bouton ▶ (Exécuter le script).  Puis Fichier > Enregistrer sous…
  > film/blender/atelier_personnages.blend

Utilisation en ligne de commande (rendus automatiques des 4 vues) :
  blender -b --python 01_atelier_personnages.py -- --rendu DOSSIER_DE_SORTIE
"""

import math
import os
import sys

import bpy

# ---------------------------------------------------------------------------
# 1. RÉGLAGES À VÉRIFIER (les seules lignes que vous aurez peut-être à changer)
# ---------------------------------------------------------------------------

# Tailles réelles en mètres : À CONFIRMER par Léna (valeurs provisoires).
TAILLE_LENA = 1.62
TAILLE_RUBEN = 1.78

# Stylisation « film d'animation moderne » : nombre de hauteurs de tête dans le corps.
# Un humain réel ≈ 7,5 têtes. On réduit un peu pour une tête plus grande, plus expressive.
TETES_LENA = 6.4
TETES_RUBEN = 6.9

# Dossier des photos de référence. Laissez "" : le script le trouve tout seul
# s'il est rangé dans film/blender/ et les photos dans film/references/photos/.
DOSSIER_PHOTOS = ""

# ---------------------------------------------------------------------------
# 2. PALETTE OFFICIELLE (relevée sur les photos, ajustée pour le rendu 3D)
#    Toute modification ici doit aussi être reportée dans film/bible/personnages.md
# ---------------------------------------------------------------------------
PALETTE = {
    # Léna
    "LENA_peau":        "#D69A77",
    "LENA_cheveux":     "#241B1D",
    "LENA_iris":        "#3B2622",
    "LENA_levres":      "#C38786",
    "LENA_sourcils":    "#2A1E1E",
    "LENA_haut":        "#D9D8DA",   # débardeur côtelé gris clair (photo devant la porte)
    "LENA_jean":        "#2C3D5B",   # jean brut large
    "LENA_baskets":     "#F1EFEA",
    "LENA_fil_rouge":   "#C8102E",   # bracelet fil rouge (présent sur 2 photos)
    # Ruben
    "RUBEN_peau":       "#D4A591",
    "RUBEN_cheveux":    "#231816",
    "RUBEN_iris":       "#473831",
    "RUBEN_levres":     "#A8636A",
    "RUBEN_sourcils":   "#221715",
    "RUBEN_tshirt":     "#F3F1EC",
    "RUBEN_jean":       "#1F2533",
    "RUBEN_baskets":    "#C9C7C2",
    "RUBEN_casquette":  "#5E6166",
    # Communs
    "blanc_oeil":       "#F4EFEA",
    "pupille":          "#0B0807",
    "studio_sol":       "#E8E1D8",
}


# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------
def hex_vers_lineaire(h):
    """'#RRGGBB' -> (r, g, b, 1) en espace linéaire (ce que Blender attend)."""
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], 1.0)


def regler_entree(bsdf, noms, valeur):
    """Règle une entrée du Principled BSDF en tolérant les différences de version."""
    for n in noms:
        if n in bsdf.inputs:
            bsdf.inputs[n].default_value = valeur
            return


def materiau(nom, couleur_hex, rugosite=0.5, sss=0.0, brillant=0.0, sheen=0.0):
    mat = bpy.data.materials.get(nom) or bpy.data.materials.new(nom)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    col = hex_vers_lineaire(couleur_hex)
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = rugosite
    mat.diffuse_color = col  # couleur visible aussi en mode « Solide »
    if sss:
        regler_entree(bsdf, ["Subsurface Weight", "Subsurface"], sss)
        regler_entree(bsdf, ["Subsurface Radius"], (1.0, 0.35, 0.2))
        regler_entree(bsdf, ["Subsurface Scale"], 0.03)
    if brillant:
        regler_entree(bsdf, ["Coat Weight", "Clearcoat"], brillant)
    if sheen:
        regler_entree(bsdf, ["Sheen Weight", "Sheen"], sheen)
    return mat


def collection(nom, parent=None):
    col = bpy.data.collections.get(nom) or bpy.data.collections.new(nom)
    parent = parent or bpy.context.scene.collection
    if col.name not in [c.name for c in parent.children]:
        parent.children.link(col)
    return col


def ranger(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def lisser(obj, niveaux=2):
    for p in obj.data.polygons:
        p.use_smooth = True
    if niveaux:
        m = obj.modifiers.new("Lissage", "SUBSURF")
        m.levels = 1
        m.render_levels = niveaux


def piece(nom, forme, loc, echelle, mat, col, parent, rot=(0, 0, 0), lisse=None):
    """Ajoute une forme simple (sphère, cylindre, cube, cône) déjà placée et colorée."""
    if forme == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    elif forme == "cylindre":
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, location=loc)
    elif forme == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=24, location=loc)
    else:
        bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    if lisse is None:  # les sphères et cubes s'arrondissent, les cylindres restent nets
        lisse = 2 if forme in ("sphere", "cube") else 0
    o.name = nom
    o.scale = echelle
    o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    lisser(o, lisse)
    ranger(o, col)
    o.parent = parent
    o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o


# ---------------------------------------------------------------------------
# Maquettes de proportions
# ---------------------------------------------------------------------------
def maquette(prefixe, taille, tetes, x, profil, col):
    """Construit une silhouette stylisée aux proportions du personnage.

    profil : dictionnaire des différences de morphologie (voir appels plus bas).
    Le personnage regarde vers -Y (vers la caméra FACE)."""
    M = {k: bpy.data.materials[f"{prefixe}_{k}"] for k in
         ("peau", "cheveux", "iris", "levres", "sourcils")}
    M["blanc"] = bpy.data.materials["blanc_oeil"]
    M["pupille"] = bpy.data.materials["pupille"]

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(x, 0, 0))
    racine = bpy.context.active_object
    racine.name = f"{prefixe}_maquette"
    racine.empty_display_size = 0.3
    ranger(racine, col)

    H = taille / tetes                        # hauteur d'une tête
    sommet = taille
    menton = taille - H
    epaules = taille - 1.38 * H
    entrejambe = taille * profil["jambes"]
    genou = entrejambe * 0.52
    larg_ep = profil["epaules"] * H
    larg_hanches = profil["hanches"] * H

    # --- Tête (un peu plus large en haut, mâchoire selon le profil)
    cz = menton + H * 0.52
    piece(f"{prefixe}_tete", "sphere", (x, 0, cz),
          (H * profil["tete_larg"] / 2, H * 0.40, H * 0.54), M["peau"], col, racine)
    piece(f"{prefixe}_machoire", "sphere", (x, -H * 0.03, menton + H * 0.24),
          (H * profil["machoire"] / 2, H * 0.30, H * 0.26), M["peau"], col, racine)

    # --- Yeux stylisés (agrandis ×1,25 par rapport au réel)
    r_oeil = H * 0.075 * profil["yeux"]
    for cote in (-1, 1):
        ex = x + cote * H * 0.19
        ey = -H * 0.30
        ez = cz + H * 0.02
        piece(f"{prefixe}_oeil_{cote}", "sphere", (ex, ey, ez),
              (r_oeil, r_oeil, r_oeil * profil["paupiere"]), M["blanc"], col, racine, lisse=0)
        piece(f"{prefixe}_iris_{cote}", "sphere", (ex, ey - r_oeil * 0.72, ez),
              (r_oeil * 0.62, r_oeil * 0.35, r_oeil * 0.62 * profil["paupiere"]),
              M["iris"], col, racine, lisse=0)
        piece(f"{prefixe}_pupille_{cote}", "sphere", (ex, ey - r_oeil * 0.98, ez),
              (r_oeil * 0.26, r_oeil * 0.12, r_oeil * 0.26), M["pupille"], col, racine, lisse=0)
        # Sourcils : plus épais et plus droits pour Ruben
        piece(f"{prefixe}_sourcil_{cote}", "cube",
              (ex + cote * H * 0.01, ey - r_oeil * 0.2, ez + r_oeil * 1.55),
              (H * 0.11, H * 0.025, H * 0.016 * profil["sourcils"]), M["sourcils"], col, racine,
              rot=(0, cote * math.radians(profil["sourcil_angle"]), 0), lisse=1)

    # --- Nez et bouche
    piece(f"{prefixe}_nez", "cone", (x, -H * 0.40, cz - H * 0.13),
          (H * 0.05, H * 0.05, H * 0.11 * profil["nez"]), M["peau"], col, racine,
          rot=(math.radians(-20), 0, 0))
    piece(f"{prefixe}_bouche", "sphere", (x, -H * 0.29, menton + H * 0.25),
          (H * 0.10, H * 0.04, H * 0.028 * profil["levres"]), M["levres"], col, racine, lisse=1)

    # --- Oreilles
    for cote in (-1, 1):
        piece(f"{prefixe}_oreille_{cote}", "sphere",
              (x + cote * H * profil["tete_larg"] / 2, 0, cz - H * 0.02),
              (H * 0.04, H * 0.07, H * 0.12), M["peau"], col, racine)

    # --- Cheveux
    calotte = piece(f"{prefixe}_cheveux_calotte", "sphere", (x, H * 0.05, cz + H * 0.12),
                    (H * profil["tete_larg"] / 2 * 1.08, H * 0.43, H * 0.50),
                    M["cheveux"], col, racine)
    if profil["cheveux"] == "longs":
        # Longs cheveux lisses jusqu'au milieu du dos + deux mèches devant les épaules
        piece(f"{prefixe}_cheveux_dos", "cube", (x, H * 0.22, cz - H * 0.85),
              (H * 0.50, H * 0.16, H * 1.25), M["cheveux"], col, racine)
        for cote in (-1, 1):
            piece(f"{prefixe}_meche_{cote}", "cube",
                  (x + cote * H * 0.40, -H * 0.02, cz - H * 0.70),
                  (H * 0.11, H * 0.10, H * 1.05), M["cheveux"], col, racine,
                  rot=(0, cote * math.radians(-4), 0))
    else:
        # Court sur les côtés, volume sur le dessus, coiffé vers l'arrière
        piece(f"{prefixe}_cheveux_volume", "sphere", (x, H * 0.04, cz + H * 0.46),
              (H * 0.38, H * 0.46, H * 0.20), M["cheveux"], col, racine,
              rot=(math.radians(-12), 0, 0))
        # Duvet de barbe : légère ombre sur le menton et la lèvre supérieure
        barbe = materiau(f"{prefixe}_duvet", "#6E4E44", rugosite=0.9)
        piece(f"{prefixe}_duvet_menton", "sphere", (x, -H * 0.13, menton + H * 0.12),
              (H * 0.16, H * 0.17, H * 0.11), barbe, col, racine)

    # --- Cou
    piece(f"{prefixe}_cou", "cylindre", (x, 0.02, menton - H * 0.05),
          (H * profil["cou"], H * profil["cou"], H * 0.32), M["peau"], col, racine)

    # --- Buste (haut) et bassin (jean)
    haut = bpy.data.materials[profil["mat_haut"]]
    bas = bpy.data.materials[profil["mat_bas"]]
    chaussures = bpy.data.materials[profil["mat_chaussures"]]
    h_buste = epaules - entrejambe
    piece(f"{prefixe}_buste", "cube", (x, 0, epaules - h_buste * 0.30),
          (larg_ep / 2 * 1.02, H * 0.36, h_buste * 0.40), haut, col, racine)
    piece(f"{prefixe}_taille", "cube", (x, 0, entrejambe + h_buste * 0.36),
          (profil["taille"] * H / 2 * 1.1, H * 0.32, h_buste * 0.22), haut, col, racine)
    piece(f"{prefixe}_bassin", "cube", (x, 0, entrejambe + h_buste * 0.08),
          (larg_hanches / 2 * 1.1, H * 0.36, h_buste * 0.20), bas, col, racine)

    # --- Jambes (jean large) et baskets
    for cote in (-1, 1):
        jx = x + cote * larg_hanches * 0.24
        piece(f"{prefixe}_jambe_{cote}", "cylindre", (jx, 0, entrejambe / 2 + 0.06),
              (H * 0.20, H * 0.20, entrejambe / 2), bas, col, racine)
        piece(f"{prefixe}_basket_{cote}", "sphere", (jx, -H * 0.12, 0.045),
              (H * 0.16, H * 0.45, 0.05), chaussures, col, racine)

    # --- Bras (épaules nues pour Léna, manches courtes pour Ruben) et mains
    for cote in (-1, 1):
        bx = x + cote * (larg_ep / 2 + H * 0.02)
        long_bras = epaules - (entrejambe - H * 0.05)
        piece(f"{prefixe}_bras_{cote}", "cylindre", (bx, 0, epaules - long_bras / 2),
              (H * 0.085 * profil["bras"], H * 0.085 * profil["bras"], long_bras / 2),
              M["peau"], col, racine, rot=(0, cote * math.radians(-2), 0))
        piece(f"{prefixe}_epaule_{cote}", "sphere", (bx, 0, epaules - H * 0.05),
              (H * 0.15, H * 0.15, H * 0.15),
              haut if profil.get("manches") else M["peau"], col, racine)
        if profil.get("manches"):
            piece(f"{prefixe}_manche_{cote}", "cylindre", (bx, 0, epaules - H * 0.30),
                  (H * 0.13, H * 0.13, H * 0.30), haut, col, racine,
                  rot=(0, cote * math.radians(-2), 0))
        piece(f"{prefixe}_main_{cote}", "sphere",
              (bx + cote * long_bras * 0.07, 0, entrejambe - H * 0.12),
              (H * 0.09, H * 0.06, H * 0.15), M["peau"], col, racine)
        if profil.get("fil_rouge") and cote == 1:
            piece(f"{prefixe}_fil_rouge", "cylindre",
                  (bx + long_bras * 0.065, 0, entrejambe + H * 0.05),
                  (H * 0.095, H * 0.095, 0.004), bpy.data.materials["LENA_fil_rouge"],
                  col, racine, lisse=0)

    # --- Accessoire : casquette de Ruben (sans logo de marque)
    if profil.get("casquette"):
        cas = bpy.data.materials["RUBEN_casquette"]
        piece(f"{prefixe}_casquette", "sphere", (x, H * 0.02, cz + H * 0.30),
              (H * 0.47, H * 0.48, H * 0.30), cas, col, racine)
        piece(f"{prefixe}_visiere", "cylindre", (x, -H * 0.42, cz + H * 0.22),
              (H * 0.28, H * 0.26, 0.006), cas, col, racine, lisse=0)
        bpy.data.objects[f"{prefixe}_casquette"].hide_render = True
        bpy.data.objects[f"{prefixe}_casquette"].hide_viewport = True
        bpy.data.objects[f"{prefixe}_visiere"].hide_render = True
        bpy.data.objects[f"{prefixe}_visiere"].hide_viewport = True

    # --- Étiquette
    bpy.ops.object.text_add(location=(x - 0.38, -0.3, -0.12))
    t = bpy.context.active_object
    t.name = f"{prefixe}_etiquette"
    t.data.body = f"{prefixe.capitalize()} · {taille:.2f} m · {tetes} têtes"
    t.data.size = 0.07
    t.rotation_euler = (math.radians(90), 0, 0)
    ranger(t, col)
    t.parent = racine
    t.matrix_parent_inverse = racine.matrix_world.inverted()
    return racine


def toise(col, x=0.0):
    """Règle de hauteur : un trait tous les 10 cm, un trait épais tous les 50 cm."""
    mat = materiau("toise", "#9A8C7E", rugosite=0.8)
    for i in range(0, 21):
        z = i * 0.10
        large = 0.16 if i % 5 == 0 else 0.07
        bpy.ops.mesh.primitive_cube_add(location=(x, 0.25, z))
        o = bpy.context.active_object
        o.name = f"toise_{z:.1f}m"
        o.scale = (large / 2, 0.003, 0.003 if i % 5 else 0.006)
        o.data.materials.append(mat)
        ranger(o, col)
    bpy.ops.mesh.primitive_cube_add(location=(x, 0.25, 1.0))
    o = bpy.context.active_object
    o.name = "toise_axe"
    o.scale = (0.004, 0.003, 1.0)
    o.data.materials.append(mat)
    ranger(o, col)


def dossier_photos():
    if DOSSIER_PHOTOS:
        return DOSSIER_PHOTOS
    candidats = []
    try:  # script ouvert dans l'éditeur de texte de Blender
        for t in bpy.data.texts:
            if t.filepath:
                candidats.append(os.path.dirname(bpy.path.abspath(t.filepath)))
    except Exception:
        pass
    try:  # script lancé en ligne de commande
        candidats.append(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        pass
    if bpy.data.filepath:
        candidats.append(os.path.dirname(bpy.data.filepath))
    for c in candidats:
        p = os.path.normpath(os.path.join(c, "..", "references", "photos"))
        if os.path.isdir(p):
            return p
    return ""


def photos_reference(col):
    d = dossier_photos()
    if not d:
        print("[atelier] Pas de dossier film/references/photos : photos non chargées.")
        return 0
    fichiers = sorted(f for f in os.listdir(d)
                      if f.lower().endswith((".jpg", ".jpeg", ".png", ".heic", ".webp")))
    for i, f in enumerate(fichiers):
        try:
            img = bpy.data.images.load(os.path.join(d, f), check_existing=True)
        except RuntimeError:
            print(f"[atelier] Format non lu par Blender : {f} (convertissez en JPG)")
            continue
        bpy.ops.object.empty_add(type="IMAGE", location=(-3.2 - (i % 3) * 1.6, 1.5, 1.0 + (i // 3) * 2.1))
        e = bpy.context.active_object
        e.name = f"REF_{os.path.splitext(f)[0]}"
        e.data = img
        e.empty_display_size = 2.0
        e.rotation_euler = (math.radians(90), 0, 0)
        e.empty_image_depth = "BACK"
        e.hide_render = True
        ranger(e, col)
    print(f"[atelier] {len(fichiers)} photo(s) de référence chargée(s) depuis {d}")
    return len(fichiers)


def studio(col):
    sc = bpy.context.scene
    # Sol « cyclo » doux
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 4, 0))
    sol = bpy.context.active_object
    sol.name = "studio_sol"
    sol.data.materials.append(materiau("studio_sol", PALETTE["studio_sol"], rugosite=0.9))
    ranger(sol, col)

    def lumiere(nom, energie, couleur, loc, taille):
        bpy.ops.object.light_add(type="AREA", location=loc)
        l = bpy.context.active_object
        l.name = nom
        l.data.energy = energie
        l.data.color = hex_vers_lineaire(couleur)[:3]
        l.data.size = taille
        cible = l.constraints.new("TRACK_TO")
        cible.target = bpy.data.objects["cible_lumieres"]
        ranger(l, col)

    bpy.ops.object.empty_add(location=(0, 0, 1.1))
    bpy.context.active_object.name = "cible_lumieres"
    ranger(bpy.context.active_object, col)
    lumiere("lumiere_principale_chaude", 600, "#FFE1C2", (-2.5, -3.0, 3.2), 2.0)
    lumiere("lumiere_douce_froide", 200, "#C9D8FF", (3.0, -2.5, 1.6), 3.0)
    lumiere("lumiere_contre_jour", 500, "#FFD7A8", (1.5, 3.0, 3.0), 1.5)

    monde = sc.world or bpy.data.worlds.new("Monde")
    sc.world = monde
    monde.use_nodes = True
    fond = monde.node_tree.nodes.get("Background")
    fond.inputs["Color"].default_value = hex_vers_lineaire("#F6E7DA")
    fond.inputs["Strength"].default_value = 0.6

    def camera(nom, loc, rot, ortho=True, echelle=3.5, focale=85):
        bpy.ops.object.camera_add(location=loc, rotation=rot)
        c = bpy.context.active_object
        c.name = nom
        if ortho:
            c.data.type = "ORTHO"
            c.data.ortho_scale = echelle
        else:
            c.data.lens = focale
        ranger(c, col)
        return c

    face = camera("CAM_FACE", (0, -8, 0.98), (math.radians(90), 0, 0))
    # Les vues profil / 3/4 / dos se font en tournant les personnages (voir rendre_planches)
    camera("CAM_PORTRAIT", (0, -3.4, 1.52), (math.radians(90), 0, 0), ortho=False, focale=50)
    sc.camera = face


def regler_projet():
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.render.fps = 24
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1080
    for moteur in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = moteur
            break
        except TypeError:
            continue
    try:
        sc.view_settings.view_transform = "AgX"
    except TypeError:
        sc.view_settings.view_transform = "Filmic"


def rendre_planches(dossier_sortie, moteur=None):
    """Rend les 4 vues (face, 3/4, profil, dos) + un portrait des deux maquettes."""
    sc = bpy.context.scene
    if moteur:
        sc.render.engine = moteur
        if moteur == "CYCLES":
            sc.cycles.samples = 32
            sc.cycles.device = "CPU"
    os.makedirs(dossier_sortie, exist_ok=True)
    racines = [bpy.data.objects["LENA_maquette"], bpy.data.objects["RUBEN_maquette"]]
    vues = [("1_face", 0), ("2_trois_quarts", 35), ("3_profil", 90), ("4_dos", 180)]
    sc.camera = bpy.data.objects["CAM_FACE"]
    for nom, angle in vues:
        for r in racines:
            r.rotation_euler = (0, 0, math.radians(angle))
        sc.render.filepath = os.path.join(dossier_sortie, f"maquettes_{nom}.png")
        bpy.ops.render.render(write_still=True)
    for r in racines:
        r.rotation_euler = (0, 0, 0)
    sc.camera = bpy.data.objects["CAM_PORTRAIT"]
    sc.render.filepath = os.path.join(dossier_sortie, "maquettes_5_portrait.png")
    bpy.ops.render.render(write_still=True)
    sc.camera = bpy.data.objects["CAM_FACE"]


# ---------------------------------------------------------------------------
# PROGRAMME PRINCIPAL
# ---------------------------------------------------------------------------
def principal():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    regler_projet()

    # Matériaux officiels
    for nom, h in PALETTE.items():
        if nom.endswith("_peau"):
            materiau(nom, h, rugosite=0.45, sss=0.25)
        elif "cheveux" in nom or "sourcils" in nom:
            materiau(nom, h, rugosite=0.35, sheen=0.3)
        elif nom.endswith("_iris") or nom in ("blanc_oeil", "pupille"):
            materiau(nom, h, rugosite=0.1, brillant=1.0)
        elif nom.endswith("_levres"):
            materiau(nom, h, rugosite=0.35, sss=0.2)
        else:
            materiau(nom, h, rugosite=0.75, sheen=0.4)

    c_lena = collection("LENA")
    c_ruben = collection("RUBEN")
    c_refs = collection("REFERENCES")
    c_studio = collection("STUDIO")

    maquette("LENA", TAILLE_LENA, TETES_LENA, -0.55, {
        "jambes": 0.485, "epaules": 1.55, "hanches": 1.50, "taille": 1.05,
        "tete_larg": 0.80, "machoire": 0.62, "yeux": 1.30, "paupiere": 1.0,
        "sourcils": 1.1, "sourcil_angle": 8, "nez": 0.95, "levres": 1.25,
        "cou": 0.17, "bras": 0.85, "cheveux": "longs",
        "mat_haut": "LENA_haut", "mat_bas": "LENA_jean", "mat_chaussures": "LENA_baskets",
        "fil_rouge": True,
    }, c_lena)
    maquette("RUBEN", TAILLE_RUBEN, TETES_RUBEN, 0.60, {
        "jambes": 0.475, "epaules": 1.95, "hanches": 1.40, "taille": 1.45,
        "tete_larg": 0.76, "machoire": 0.66, "yeux": 1.15, "paupiere": 0.80,
        "sourcils": 1.7, "sourcil_angle": 2, "nez": 1.25, "levres": 1.35,
        "cou": 0.22, "bras": 1.05, "cheveux": "courts", "manches": True,
        "mat_haut": "RUBEN_tshirt", "mat_bas": "RUBEN_jean", "mat_chaussures": "RUBEN_baskets",
        "casquette": True,
    }, c_ruben)

    toise(c_refs)
    photos_reference(c_refs)
    studio(c_studio)
    print("[atelier] Terminé : maquettes, palette, toise, studio et caméras en place.")


principal()

# Rendu automatique : blender -b --python 01_atelier_personnages.py -- --rendu DOSSIER [--cycles]
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if "--rendu" in args:
        rendre_planches(args[args.index("--rendu") + 1],
                        moteur="CYCLES" if "--cycles" in args else None)
