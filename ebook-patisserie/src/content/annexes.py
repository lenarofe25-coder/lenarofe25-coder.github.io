"""Guides pratiques, lexique, index et pages de notes."""
import html
import unicodedata

import illus

C = illus.C
HERO = "annexes-hero"
INTRO = ("Conversions, températures, farines, chocolats, crèmes et conservation : "
         "un carnet pratique à garder à portée de main, avec un lexique et l'index de toutes les recettes.")
EXTRA_IMAGES = {
    "annexes-hero": dict(kind="items", scene="creme", item="macaron", base="plate",
                         pos=[(440, 610), (600, 580), (760, 610), (520, 700), (680, 700)]),
}

ORN = ('<svg class="orn left" viewBox="0 0 200 16"><path d="M0 8 H82 M118 8 H200" stroke="#B48E4F" stroke-width=".8"/>'
       '<path d="M100 1 L107 8 L100 15 L93 8 Z" fill="none" stroke="#B48E4F" stroke-width=".9"/><circle cx="100" cy="8" r="1.8" fill="#B48E4F"/></svg>')


def page(n, folio, right, title, lead, body, anchor=None):
    aid = f' id="{anchor}"' if anchor else ""
    return (f'<section class="page"><div class="runhead"><span>Guides &amp; annexes</span><span>{right}</span></div>'
            f'<div class="txt fit"><div class="kicker">Le carnet du pâtissier</div><h1{aid}>{title}</h1>{ORN}'
            f'<p class="lead">{lead}</p>{body}</div>{folio(n)}</section>')


def table(head, rows, widths=None):
    th = "".join(f'<th{f" style=width:{widths[i]}" if widths else ""}>{h}</th>' for i, h in enumerate(head))
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="tbl"><tr>{th}</tr>{tr}</table>'


# ------------------------------------------------------------------ conversions
def conversions(n, k, folio, B):
    left = table(["Ingrédient", "1 c. à c.", "1 c. à s.", "1 tasse (250 ml)"], [
        ["Farine", "3 g", "10 g", "140 g"], ["Sucre semoule", "5 g", "15 g", "200 g"], ["Sucre glace", "3 g", "10 g", "130 g"],
        ["Cassonade", "5 g", "14 g", "200 g"], ["Cacao en poudre", "3 g", "8 g", "100 g"], ["Poudre d'amande", "3 g", "8 g", "100 g"],
        ["Beurre", "5 g", "15 g", "225 g"], ["Riz", "—", "15 g", "200 g"], ["Miel", "7 g", "21 g", "340 g"],
        ["Levure chimique", "4 g", "12 g", "—"], ["Sel fin", "5 g", "15 g", "—"], ["Fécule de maïs", "3 g", "9 g", "130 g"]])
    right = table(["Liquides", "Équivalence"], [
        ["1 c. à c.", "5 ml"], ["1 c. à s.", "15 ml"], ["1 cl", "10 ml"], ["1 verre à moutarde", "200 ml"], ["1 tasse (US)", "240 ml"],
        ["1 bol", "350 ml"], ["½ litre", "500 ml"], ["1 litre de lait", "1 030 g"], ["1 litre de crème", "1 000 g environ"]])
    eggs = table(["Œufs (calibre M)", "Poids moyen"], [
        ["1 œuf entier sans coquille", "50 g"], ["1 jaune", "20 g"], ["1 blanc", "30 g"], ["Gros œuf (L)", "60 g"]])
    misc = table(["Produit", "Équivalence"], [
        ["1 sachet de levure chimique", "11 g"], ["1 sachet de sucre vanillé", "7,5 g"], ["1 sachet de levure sèche", "5,5 à 7 g"],
        ["Levure fraîche → sèche", "diviser par 3"], ["1 feuille de gélatine", "2 g"], ["1 gousse de vanille", "≈ 1 c. à c. d'extrait"],
        ["1 citron", "40 à 50 ml de jus"], ["1 orange", "80 à 100 ml de jus"], ["1 noix de beurre", "≈ 10 g"], ["1 pincée", "≈ 0,5 g"]])
    body = (f'<div class="grid2" style="grid-template-columns:1.35fr 1fr;gap:5mm 7mm"><div><div class="h3">Poids des cuillères et des tasses</div>{left}'
            f'<div class="h3" style="margin-top:5mm">Petites mesures utiles</div>{misc}</div>'
            f'<div><div class="h3">Volumes</div>{right}<div class="h3" style="margin-top:5mm">Les œufs</div>{eggs}'
            f'<div class="card" style="margin-top:5mm"><h4>Pourquoi peser ?</h4><p>Une tasse de farine peut varier de 120 à 160 g selon qu\'elle est tassée ou non. '
            f'La balance élimine toute approximation : c\'est le premier secret des pâtisseries réussies.</p></div></div></div>')
    return page(n, folio, "Conversions", "Équivalences &amp; conversions",
                "Toutes les recettes de ce livre sont pesées. Ces tables vous aideront si vous adaptez une recette ou si vous n'avez pas de balance sous la main.", body)


# ------------------------------------------------------------------ températures
def temperatures(n, k, folio, B):
    th = table(["Thermostat", "Température", "Chaleur", "Utilisation"], [
        ["Th. 1", "30 °C", "Tiède", "Faire lever une pâte (four éteint, lumière allumée)"], ["Th. 2", "60 °C", "Très doux", "Sécher des fruits, garder au chaud"],
        ["Th. 3", "90 °C", "Doux", "Meringues françaises"], ["Th. 4", "120 °C", "Doux", "Crèmes cuites, ganache de tarte"],
        ["Th. 5", "150 °C", "Modéré", "Macarons, crèmes brûlées (100–150 °C)"], ["Th. 6", "180 °C", "Moyen", "Gâteaux, tartes, choux, biscuits"],
        ["Th. 7", "210 °C", "Chaud", "Pâte feuilletée, biscuit joconde"], ["Th. 8", "240 °C", "Très chaud", "Caraméliser, saisir"],
        ["Th. 9", "270 °C", "Gril", "Gratiner"]], ["17mm", "24mm", "22mm", None])
    sugar = table(["Stade", "Température", "Usage"], [
        ["Nappé", "100–105 °C", "Sirops d'imbibage"], ["Petit filé", "106–110 °C", "Fruits confits, caramel nappant"],
        ["Petit boulé", "112–115 °C", "Fondant, pâte de fruits"], ["Gros boulé", "118–121 °C", "Meringue italienne, caramels mous"],
        ["Petit cassé", "130–135 °C", "Nougat tendre"], ["Grand cassé", "145–150 °C", "Sucre d'art, sucettes"],
        ["Caramel clair", "155–165 °C", "Choux glacés, Saint-Honoré"], ["Caramel ambré", "170–180 °C", "Caramel au beurre salé, Tatin"]], ["24mm", "24mm", None])
    keys = table(["Repère", "Température à cœur"], [
        ["Crème anglaise", "82–84 °C"], ["Meringue suisse", "55 °C"], ["Sabayon", "65 °C"], ["Génoise (bain-marie)", "45 °C"],
        ["Fonte du chocolat noir", "45–50 °C (max.)"], ["Chocolat noir tempéré", "31–32 °C"], ["Glaçage miroir", "32–35 °C"],
        ["Pâte levée (pousse idéale)", "24–27 °C"], ["Huile de friture", "170–175 °C"]])
    body = (f'<div class="h3">Thermostats et températures</div>{th}'
            f'<div class="grid2" style="margin-top:4mm;gap:4mm 7mm;grid-template-columns:1.25fr 1fr"><div><div class="h3">La cuisson du sucre</div>{sugar}</div>'
            f'<div><div class="h3">Repères au thermomètre</div>{keys}</div></div>'
            f'<div class="card" style="margin-top:4mm"><h4>Chaleur tournante ou statique ?</h4><p>La chaleur tournante répartit la chaleur et permet de cuire plusieurs plaques ; elle dessèche un peu plus. '
            f'La chaleur statique (voûte et sole) convient aux soufflés, choux et feuilletages, qui aiment une chaleur montante. '
            f'Pour passer de l\'une à l\'autre, ajoutez ou retirez 10 à 15 °C.</p></div>')
    return page(n, folio, "Températures", "Températures de cuisson",
                "Les températures de ce livre sont données en chaleur tournante. Voici les correspondances utiles, ainsi que les repères au thermomètre qui rendent les recettes infaillibles.", body)


# ------------------------------------------------------------------ farines
def farines(n, k, folio, B):
    t = table(["Farine", "Caractéristiques", "Usages en pâtisserie"], [
        ["T45 (blanche)", "Très fine, pauvre en son, riche en amidon. La « fluide » ou « à pâtisserie ».", "Pâtes sucrées, génoises, cakes, biscuits, crèmes"],
        ["T45 de force (gruau)", "Plus riche en protéines (11–13 %) : réseau de gluten élastique.", "Brioches, croissants, pains au lait, babka"],
        ["T55", "Polyvalente, légèrement plus bise. La farine « standard ».", "Pâte brisée, pâte à choux, feuilletage, pain"],
        ["T65 à T80", "Plus complètes, goût de céréale prononcé.", "Pains, sablés rustiques, crumbles"],
        ["Fécule de maïs", "Amidon pur, sans gluten.", "Crèmes pâtissières, biscuits légers, pavlova"],
        ["Farine de riz", "Fine, sans gluten, texture sablée.", "Sablés, biscuits sans gluten"],
        ["Farine de sarrasin", "Sans gluten, goût de noisette grillée.", "Sablés bretons, galettes, crêpes"],
        ["Poudres de fruits secs", "Amande, noisette, pistache : sans gluten, riches en matières grasses.", "Financiers, macarons, dacquoises, crème d'amande"]],
        ["38mm", None, "58mm"])
    body = (f'{t}<div class="grid2" style="margin-top:5mm">'
            f'<div class="card"><h4>Que signifie le « T » ?</h4><p>Le type indique le taux de minéraux (cendres) : T45 = 0,45 % environ. Plus le chiffre est élevé, plus la farine contient de son et plus elle est complète.</p></div>'
            f'<div class="card"><h4>Tamiser, toujours</h4><p>Tamiser aère la farine, élimine les grumeaux et permet une incorporation homogène, surtout dans les biscuits montés.</p></div>'
            f'<div class="card"><h4>Sans gluten</h4><p>Remplacez la farine T45 par un mélange de 60 % de farine de riz et 40 % de fécule. Pour les gâteaux, ajoutez un peu de poudre d\'amande pour le moelleux.</p></div>'
            f'<div class="card"><h4>Conservation</h4><p>Dans un bocal hermétique, au sec et à l\'abri de la lumière. Les farines complètes et les poudres de fruits secs rancissent plus vite : gardez-les au frais.</p></div></div>')
    return page(n, folio, "Farines", "Guide des farines",
                "Le choix de la farine change la texture d'une pâtisserie : friable ou élastique, légère ou rustique. Voici comment s'y retrouver.", body)


# ------------------------------------------------------------------ chocolats
def chocolats(n, k, folio, B):
    t = table(["Chocolat", "Cacao", "Profil", "Usages"], [
        ["Noir intense", "70–85 %", "Amer, puissant, peu sucré", "Ganaches, mousses très intenses, cacao en finition"],
        ["Noir pâtissier", "55–70 %", "Équilibré, rond", "Gâteaux, fondants, tartes, mousses (le plus polyvalent)"],
        ["Au lait", "33–40 %", "Doux, lacté, caramélisé", "Ganaches montées, mousses, enrobages, pralinés"],
        ["Blond / caramélisé", "30–35 %", "Biscuité, caramel", "Ganaches, entremets modernes, cookies"],
        ["Blanc", "28–35 % de beurre de cacao", "Vanillé, très sucré", "Ganaches montées, mousses aux fruits, glaçages"],
        ["Cacao en poudre", "100 %", "Amer, sans sucre", "Pâtes, biscuits, glaçages miroirs, décor"],
        ["Pâte à glacer", "variable", "Facile, brillante sans tempérage", "Enrobages rapides (moins fine en goût)"]],
        ["30mm", "26mm", "36mm", None])
    body = (f'{t}<div class="grid3" style="margin-top:5mm">'
            f'<div class="card"><h4>Couverture</h4><p>Le chocolat « de couverture » contient plus de beurre de cacao (au moins 31 %). Plus fluide, il est idéal pour les enrobages et les ganaches lisses.</p></div>'
            f'<div class="card"><h4>Fondre sans risque</h4><p>Au bain-marie doux ou au micro-ondes par séries de 30 secondes. Pas plus de 50 °C pour le noir, 45 °C pour le lait et le blanc.</p></div>'
            f'<div class="card"><h4>Il a « massé » ?</h4><p>Une goutte d\'eau l\'a rendu épais et granuleux. Ajoutez une cuillerée de crème chaude et mixez : il servira pour une ganache ou une sauce.</p></div>'
            f'<div class="card"><h4>Le blanchiment</h4><p>Un voile blanc à la surface signale un écart de température ou d\'humidité. Le chocolat reste parfaitement utilisable en pâtisserie.</p></div>'
            f'<div class="card"><h4>Conservation</h4><p>Entre 15 et 18 °C, au sec et à l\'abri des odeurs. Évitez le réfrigérateur, sauf pour les ganaches et les bonbons.</p></div>'
            f'<div class="card"><h4>Les origines</h4><p>Madagascar : fruité et acidulé. Équateur : floral. Ghana : cacaoté et classique. Venezuela : rond et boisé.</p></div></div>')
    return page(n, folio, "Chocolats", "Guide des chocolats",
                "Le pourcentage indiqué correspond à la part totale de cacao (pâte et beurre de cacao). Il guide le choix, mais l'origine des fèves et le savoir-faire comptent tout autant.", body)


# ------------------------------------------------------------------ crèmes
def cremes(n, k, folio, B):
    rows = [
        ["Crème pâtissière", "Lait, jaunes, sucre, fécule, cuite", "Ferme, onctueuse", "Choux, éclairs, tartes aux fruits", "creme-patissiere"],
        ["Crème diplomate", "Pâtissière + crème fouettée (± gélatine)", "Légère, se tient", "Mille-feuille, tartes, trifle", "creme-patissiere"],
        ["Crème mousseline", "Pâtissière + beurre fouetté", "Riche, aérienne, stable", "Fraisier, Paris-Brest", "creme-mousseline"],
        ["Crème chiboust", "Pâtissière + meringue italienne + gélatine", "Très légère", "Saint-Honoré traditionnel", None],
        ["Crème frangipane", "⅔ crème d'amande + ⅓ pâtissière", "Moelleuse, cuite", "Galettes, tartes amandines", "creme-amande"],
        ["Crème d'amande", "Beurre, sucre, amande, œufs", "Moelleuse, cuite", "Bourdaloue, tartes aux fruits", "creme-amande"],
        ["Crème anglaise", "Lait, jaunes, sucre, cuite à 83 °C", "Nappante, liquide", "Sauce, île flottante, bavarois", "creme-anglaise"],
        ["Crème au beurre", "Meringue (ou sirop) + beurre", "Ferme, riche", "Opéra, décors, macarons", None],
        ["Chantilly", "Crème fouettée, sucre, vanille", "Aérienne", "Décor, garniture, accompagnement", "chantilly"],
        ["Ganache montée", "Ganache refroidie puis fouettée", "Légère, stable", "Entremets, tartelettes", "ganache-montee"],
        ["Crémeux", "Anglaise + chocolat ou fruit (± gélatine)", "Dense, fondant", "Inserts, tartes, verrines", None],
        ["Lemon curd", "Jus de citron, œufs, sucre, beurre", "Acidulé, nappant", "Tarte au citron, scones", None],
    ]

    def pg(slug):
        if not slug:
            return "—"
        a = "base-" + slug
        return f'<a href="#{a}" style="color:#B48E4F;text-decoration:none">p. {B.pg(a)}</a>'
    t = table(["Crème", "Composition", "Texture", "Usages", "Base"], [r[:4] + [pg(r[4])] for r in rows], ["30mm", "48mm", "26mm", None, "13mm"])
    body = (f'{t}<div class="grid2" style="margin-top:5mm">'
            f'<div class="card"><h4>La règle de l\'ébullition</h4><p>Toute crème contenant de la fécule ou de la farine doit bouillir 1 minute pour perdre son goût d\'amidon et épaissir durablement. À l\'inverse, une crème anglaise (sans amidon) ne doit jamais bouillir.</p></div>'
            f'<div class="card"><h4>Hygiène</h4><p>Les crèmes aux œufs sont fragiles : refroidissez-les rapidement, filmez-les au contact, conservez-les au réfrigérateur et consommez-les sous 48 heures.</p></div></div>')
    return page(n, folio, "Crèmes", "Guide des crèmes pâtissières",
                "La plupart des grandes crèmes dérivent les unes des autres. Ce tableau vous aide à choisir la bonne, et à retrouver sa recette de base.", body)


# ------------------------------------------------------------------ conservation
def conservation(n, k, folio, B):
    t = table(["Dessert", "Ambiante", "Réfrigérateur", "Congélateur"], [
        ["Cakes, quatre-quarts, financiers", "4–5 jours (filmés)", "1 semaine", "3 mois"],
        ["Gâteaux au chocolat, brownies", "3–5 jours", "1 semaine", "3 mois"],
        ["Biscuits secs, sablés, tuiles", "1–3 semaines (boîte métal)", "Déconseillé", "2 mois (pâte crue)"],
        ["Tartes aux fruits frais", "Quelques heures", "24 h", "Déconseillé"],
        ["Tartes cuites (amandine, Tatin)", "1–2 jours", "3 jours", "1 mois"],
        ["Crèmes aux œufs, choux garnis", "Non", "24–48 h", "Choux vides : 2 mois"],
        ["Entremets, mousses", "Non", "2–3 jours", "1 mois (sans décor)"],
        ["Cheesecakes", "Non", "3 jours", "1 mois"],
        ["Meringues sèches", "2 semaines (boîte hermétique)", "Non", "Non"],
        ["Macarons garnis", "Non", "5 jours", "1 mois"],
        ["Brioches, viennoiseries", "1–3 jours (sac fermé)", "Déconseillé", "1–2 mois"],
        ["Pâtes crues (sucrée, brisée, feuilletée)", "Non", "3 jours", "2–3 mois"],
        ["Glaces et sorbets maison", "—", "—", "1 à 2 semaines"]], ["50mm", "40mm", "32mm", None])
    body = (f'{t}<div class="grid3" style="margin-top:5mm">'
            f'<div class="card"><h4>Bien emballer</h4><p>Film alimentaire au contact pour les crèmes, boîte hermétique pour les biscuits, sac fermé pour les brioches. L\'air est l\'ennemi du moelleux.</p></div>'
            f'<div class="card"><h4>Congeler malin</h4><p>Congelez les entremets nus, à découvert 2 heures puis emballés. Décongelez-les 6 à 8 heures au réfrigérateur, jamais à l\'air libre.</p></div>'
            f'<div class="card"><h4>Raviver</h4><p>5 minutes à 160 °C redonnent leur croustillant aux tartes, choux et viennoiseries de la veille.</p></div></div>')
    return page(n, folio, "Conservation", "Guide de conservation",
                "Bien conservée, une pâtisserie garde son goût et sa texture. Ces durées s'entendent pour des préparations maison, sans conservateur.", body)


# ------------------------------------------------------------------ lexique
LEXIQUE = [
    ("Abaisser", "Étaler une pâte au rouleau à l'épaisseur voulue. Le résultat s'appelle une abaisse."),
    ("Appareil", "Mélange de plusieurs ingrédients prêt à être utilisé ou cuit (appareil à clafoutis, à crème brûlée…)."),
    ("Apprêt", "Dernière pousse d'une pâte levée après façonnage, avant la cuisson."),
    ("Bain-marie", "Récipient posé sur une casserole d'eau frémissante, pour chauffer doucement sans contact direct avec la flamme."),
    ("Blanchir", "Fouetter des jaunes d'œufs et du sucre jusqu'à ce que le mélange éclaircisse et mousse."),
    ("Bouler", "Façonner un pâton en boule régulière en le roulant sous la paume."),
    ("Chemiser", "Tapisser un moule de beurre et de farine, de papier cuisson ou de biscuits."),
    ("Chinois", "Passoire conique très fine qui sert à filtrer crèmes et sauces."),
    ("Corner", "Racler un récipient à la corne pour en récupérer tout le contenu."),
    ("Crémer", "Travailler du beurre mou avec du sucre jusqu'à obtenir une texture crémeuse."),
    ("Cristalliser", "Laisser une ganache ou un chocolat se raffermir lentement, à température contrôlée."),
    ("Décuire", "Ajouter un liquide à un sucre cuit ou un caramel pour en arrêter la cuisson."),
    ("Dessécher", "Faire évaporer l'humidité d'une panade sur le feu (pâte à choux)."),
    ("Détailler", "Découper une pâte à l'emporte-pièce ou au couteau."),
    ("Détrempe", "Mélange de farine, d'eau et de sel (et de levure) dans lequel on enferme le beurre pour le feuilletage."),
    ("Dorer", "Badigeonner au pinceau d'œuf battu pour colorer et faire briller à la cuisson."),
    ("Émulsionner", "Mélanger intimement deux éléments qui ne se mélangent pas naturellement (gras et eau)."),
    ("Foncer", "Garnir un moule ou un cercle d'une abaisse de pâte."),
    ("Fraser", "Écraser une pâte sous la paume pour l'homogénéiser sans la corser."),
    ("Imbiber", "Humecter un biscuit de sirop au pinceau pour le rendre moelleux et parfumé."),
    ("Macaronner", "Incorporer la meringue à la pâte d'amande en la faisant légèrement retomber, jusqu'à la bonne fluidité."),
    ("Masquer", "Recouvrir entièrement un gâteau d'une couche de crème lissée."),
    ("Monter", "Fouetter un ingrédient pour y incorporer de l'air (blancs, crème)."),
    ("Napper", "Recouvrir d'une sauce ou d'un glaçage ; une crème « nappe » lorsqu'elle couvre la spatule."),
    ("Panade", "Mélange épais de liquide et de farine desséché sur le feu, base de la pâte à choux."),
    ("Pocher", "Dresser à la poche à douille ; ou cuire dans un liquide frémissant."),
    ("Pointage", "Première levée d'une pâte après pétrissage."),
    ("Pommade (beurre)", "Beurre ramolli à la consistance d'une crème, ni dur ni fondu."),
    ("Rhodoïd", "Feuille de plastique alimentaire qui chemise les cercles et donne des bords nets."),
    ("Ruban", "Texture d'un appareil fouetté qui retombe du fouet en formant un ruban continu."),
    ("Sabler", "Frotter farine et beurre froid entre les mains pour obtenir un sable fin."),
    ("Serrer", "Ajouter du sucre en fin de montage des blancs pour les raffermir."),
    ("Tant-pour-tant", "Mélange à poids égal de poudre d'amande et de sucre glace."),
    ("Tempérer", "Amener un chocolat à des températures précises pour qu'il soit brillant et cassant ; ou mélanger progressivement un liquide chaud à des œufs."),
    ("Torréfier", "Griller des fruits secs au four pour développer leurs arômes."),
    ("Tourer", "Donner des tours à une pâte feuilletée en la pliant et en l'étalant successivement."),
    ("Zester", "Prélever finement l'écorce colorée d'un agrume, sans la peau blanche."),
]


def lexique(n, k, folio, B):
    half = (len(LEXIQUE) + 1) // 2
    items = LEXIQUE[:half] if k == 0 else LEXIQUE[half:]
    dl = "".join(f'<div><dt>{a}</dt><dd>{b}</dd></div>' for a, b in items)
    if k == 0:
        return page(n, folio, "Lexique", "Lexique du pâtissier",
                    "Les mots du métier, pour lire les recettes comme un professionnel.", f'<dl class="lex cols2">{dl}</dl>')
    return (f'<section class="page"><div class="runhead"><span>Guides &amp; annexes</span><span>Lexique</span></div>'
            f'<div class="txt fit"><div class="kicker">Le carnet du pâtissier</div><div class="h-display" style="font-size:28pt;margin-bottom:5mm">Lexique <em style="color:#6E4F3E">(suite)</em></div>'
            f'<dl class="lex cols2">{dl}</dl></div>{folio(n)}</section>')


PAGES = [
    dict(id="conversions", title="Équivalences & conversions", n=1, fn=conversions),
    dict(id="temperatures", title="Températures de cuisson", n=1, fn=temperatures),
    dict(id="farines", title="Guide des farines", n=1, fn=farines),
    dict(id="chocolats", title="Guide des chocolats", n=1, fn=chocolats),
    dict(id="cremes", title="Guide des crèmes pâtissières", n=1, fn=cremes),
    dict(id="conservation", title="Guide de conservation", n=1, fn=conservation),
    dict(id="lexique", title="Lexique des termes de pâtisserie", n=2, fn=lexique),
]


# ------------------------------------------------------------------ index & notes
INDEX_PAGES = 2


def _key(t):
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def index_page(n, k, folio, B, recipes, bases):
    entries = [(r["t"], r["slug"], False) for r in recipes] + [(b["t"], "base-" + b["slug"], True) for b in bases]
    entries.sort(key=lambda e: _key(e[0]))
    half = (len(entries) + 1) // 2
    # coupe à une frontière de lettre
    cut = half
    for j in range(half, len(entries)):
        if _key(entries[j][0])[0] != _key(entries[j - 1][0])[0]:
            cut = j
            break
    part = entries[:cut] if k == 0 else entries[cut:]
    out, last = [], None
    for t, a, is_base in part:
        L = _key(t)[0].upper()
        if L != last:
            out.append(f'<div class="L">{L}</div>')
            last = L
        out.append(f'<a href="#{a}" class="{"base" if is_base else ""}"><span class="lbl">{html.escape(t)}</span><span class="dots"></span><span class="pg">{B.pg(a)}</span></a>')
    head = ('<div class="kicker">Le carnet du pâtissier</div><h1>Index des recettes</h1>' + ORN +
            '<p class="lead" style="margin-bottom:0">Les préparations de base figurent en <em>italique</em>.</p>') if k == 0 else \
        '<div class="kicker">Le carnet du pâtissier</div><div class="h-display" style="font-size:28pt">Index <em style="color:#6E4F3E">(suite)</em></div>'
    return (f'<section class="page"><div class="runhead"><span>Guides &amp; annexes</span><span>Index</span></div>'
            f'<div class="txt fit">{head}<div class="idx">{"".join(out)}</div></div>{folio(n)}</section>')


def notes_page(n, k, folio):
    title = '<div class="kicker">Le carnet du pâtissier</div><h1>Mes notes personnelles</h1>' + ORN + \
        '<p class="lead">Vos ajustements, vos variantes, les desserts qui ont fait sensation : ce livre est aussi le vôtre.</p>' if k == 0 else \
        '<div class="kicker">Le carnet du pâtissier</div><div class="h-display" style="font-size:28pt">Mes notes</div>'
    return (f'<section class="page notes-page"><div class="txt" style="bottom:auto">{title}</div>'
            f'<div class="lines" style="top:{70 if k == 0 else 44}mm"></div>{folio(n)}</section>')
