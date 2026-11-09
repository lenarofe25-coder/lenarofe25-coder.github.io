"""Pages liminaires : couverture, présentation, mentions, introduction, matériel,
ingrédients, techniques fondamentales, quatrième de couverture."""
import config
import illus

C = illus.C

EXTRA_IMAGES = {
    "intro-atelier": dict(kind="items", scene="lin", item="sable", base="board",
                          pos=[(420, 600), (600, 570), (780, 600), (510, 700), (700, 700)],
                          scatter=[(["flour"], (300, 760, 500, 800), 1), (["vanilla"], (820, 780, 860, 800), 1), (["almond"], (850, 520, 1000, 560), 4)]),
    "intro-ingredients": dict(kind="items", scene="creme", item="madeleine", base="plate",
                              pos=[(450, 610), (620, 580), (760, 640), (560, 700)],
                              scatter=[(["lemon"], (900, 760, 960, 800), 1), (["vanilla"], (180, 780, 200, 800), 1)]),
    "intro-techniques": dict(kind="choux", scene="sauge", item="chou", top="sugar"),
}

# ------------------------------------------------------------------ icônes matériel
S = 'fill="none" stroke="#6E4F3E" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
TOOL_ICONS = {
    "balance": f'<svg viewBox="0 0 48 48" {S}><rect x="8" y="26" width="32" height="14" rx="3"/><path d="M14 26c0-6 20-6 20 0"/><path d="M8 20h32"/><rect x="20" y="31" width="8" height="5" rx="1"/></svg>',
    "fouet": f'<svg viewBox="0 0 48 48" {S}><path d="M24 44V28"/><path d="M24 28c-8-3-10-14-6-22 2-3 10-3 12 0 4 8 2 19-6 22z"/><path d="M24 28c-3-5-4-14-1-21M24 28c3-5 4-14 1-21"/></svg>',
    "maryse": f'<svg viewBox="0 0 48 48" {S}><path d="M24 44V22"/><path d="M17 22h14l-1-12c0-3-12-3-12 0z"/></svg>',
    "poche": f'<svg viewBox="0 0 48 48" {S}><path d="M10 8h28L27 36h-6z"/><path d="M21 36l1 6h4l1-6"/><path d="M14 16h20"/></svg>',
    "rouleau": f'<svg viewBox="0 0 48 48" {S}><rect x="12" y="19" width="24" height="10" rx="5"/><path d="M4 24h8M36 24h8"/></svg>',
    "thermo": f'<svg viewBox="0 0 48 48" {S}><circle cx="18" cy="16" r="9"/><path d="M18 16l4-4M24 23l16 18"/></svg>',
    "tamis": f'<svg viewBox="0 0 48 48" {S}><ellipse cx="22" cy="20" rx="14" ry="5"/><path d="M8 20c0 8 6 13 14 13s14-5 14-13"/><path d="M36 20h9"/><path d="M14 26h16M12 23h20"/></svg>',
    "robot": f'<svg viewBox="0 0 48 48" {S}><path d="M10 42h28M14 42V20h4"/><path d="M14 20c0-8 8-12 16-12h6v8H20"/><path d="M22 26h16l-2 10H24z"/></svg>',
    "cercle": f'<svg viewBox="0 0 48 48" {S}><ellipse cx="24" cy="18" rx="16" ry="6"/><path d="M8 18v12c0 3 7 6 16 6s16-3 16-6V18"/></svg>',
    "tarte": f'<svg viewBox="0 0 48 48" {S}><ellipse cx="24" cy="24" rx="18" ry="7"/><path d="M6 24v4c0 4 8 7 18 7s18-3 18-7v-4"/><path d="M10 29v3M16 31v3M24 32v3M32 31v3M38 29v3"/></svg>',
    "spatule": f'<svg viewBox="0 0 48 48" {S}><path d="M8 40l8-8"/><path d="M16 32l4-4h3l17-17c2-2 0-4-2-2L21 26"/></svg>',
    "mixeur": f'<svg viewBox="0 0 48 48" {S}><rect x="18" y="4" width="12" height="20" rx="4"/><path d="M22 24v12M26 24v12"/><path d="M18 38c0-2 12-2 12 0v3H18z"/></svg>',
    "tapis": f'<svg viewBox="0 0 48 48" {S}><rect x="6" y="12" width="36" height="24" rx="2"/><circle cx="16" cy="20" r="3"/><circle cx="28" cy="20" r="3"/><circle cx="16" cy="29" r="3"/><circle cx="28" cy="29" r="3"/></svg>',
    "moule": f'<svg viewBox="0 0 48 48" {S}><path d="M6 18h36l-4 18H10z"/><path d="M6 18l4-4h28l4 4"/></svg>',
    "minuteur": f'<svg viewBox="0 0 48 48" {S}><circle cx="24" cy="27" r="15"/><path d="M24 27l6-6M20 8h8M24 8v4"/></svg>',
    "casserole": f'<svg viewBox="0 0 48 48" {S}><path d="M8 20h26v14c0 3-2 5-5 5H13c-3 0-5-2-5-5z"/><path d="M34 22h10"/><path d="M14 14c0-3 3-3 3-6M22 14c0-3 3-3 3-6"/></svg>',
    "douilles": f'<svg viewBox="0 0 48 48" {S}><path d="M10 38l6-22h6l6 22z"/><path d="M16 16l3-6 3 6"/><path d="M28 38l5-18h4l5 18z"/><path d="M33 20l2-4 2 4"/></svg>',
    "emporte": f'<svg viewBox="0 0 48 48" {S}><circle cx="18" cy="24" r="11"/><path d="M33 34c-6-5-9-9-9-13 0-3 3-5 5-3l4 3 4-3c2-2 5 0 5 3 0 4-3 8-9 13z"/></svg>',
}


def cover(img):
    author = f'<div class="kicker" style="margin-top:2mm">{config.AUTHOR}</div>' if config.AUTHOR else ""
    return f'''<section class="page cover"><div class="frame"></div>
<div class="top"><div class="kicker">Recettes de pâtisserie française</div>
<div class="t1">L'Art de la</div><div class="t2">Pâtisserie</div>
<svg class="orn" viewBox="0 0 200 16" style="width:60mm;margin:3.5mm auto"><path d="M0 8 H82 M118 8 H200" stroke="#B48E4F" stroke-width=".8"/><path d="M100 1 L107 8 L100 15 L93 8 Z" fill="none" stroke="#B48E4F" stroke-width=".9"/><circle cx="100" cy="8" r="1.8" fill="#B48E4F"/></svg>
<div class="sub">{config.SUBTITLE}</div></div>
<div class="badge"><b>100</b><span>recettes</span></div>
<div class="arch"><img src="{img}" alt=""></div>
<div class="bottom"><div class="kicker">Gâteaux · Tartes · Biscuits · Entremets · Viennoiseries</div>{author}</div>
</section>'''


def back_cover(img):
    shop = f'<div class="kicker" style="color:#D4B57A;margin-top:4mm">{config.SHOP}</div>' if config.SHOP else ""
    return f'''<section class="page opener"><div class="frame"></div>
<div style="position:absolute;top:34mm;left:0;right:0;text-align:center"><span class="script" style="font-size:30pt;color:#D4B57A">Merci</span></div>
<div style="position:absolute;top:56mm;left:30mm;right:30mm;text-align:center;font-family:Cormorant;font-style:italic;font-size:15pt;line-height:1.45;color:#E9DCC8">
« La pâtisserie est une affaire de patience, de précision et de partage. Puisse ce livre accompagner vos plus beaux moments, du goûter du mercredi aux grandes tables de fête. »</div>
<div class="circle" style="top:112mm"><img src="{img}" alt=""></div>
<div style="position:absolute;top:204mm;left:0;right:0;text-align:center">
<div style="font-family:Cormorant;font-size:30pt;color:#FBF7F0">{config.TITLE}</div>
<div style="font-family:Garamond;font-style:italic;font-size:12pt;color:#E9DCC8;margin-top:2mm">{config.SUBTITLE}</div>
<div class="kicker" style="color:#D4B57A;margin-top:9mm">100 recettes · 18 préparations de base · 9 guides pratiques</div>{shop}
</div></section>'''


def presentation(n, folio):
    return f'''<section class="page"><div class="txt fit">
<div class="kicker">Bienvenue</div><h1 id="bienvenue">Un livre pour pâtisser <br><em style="color:#6E4F3E">en toute confiance</em></h1>
<svg class="orn left" viewBox="0 0 200 16"><path d="M0 8 H82 M118 8 H200" stroke="#B48E4F" stroke-width=".8"/><path d="M100 1 L107 8 L100 15 L93 8 Z" fill="none" stroke="#B48E4F" stroke-width=".9"/><circle cx="100" cy="8" r="1.8" fill="#B48E4F"/></svg>
<p class="lead">Cent recettes choisies, testées dans une cuisine ordinaire avec un four ménager, et expliquées pas à pas pour que chaque gâteau sorte du four tel que vous l'avez imaginé.</p>
<div class="cols2">
<p class="dropcap">Ce livre est né d'une conviction simple : la grande pâtisserie française n'est pas réservée aux professionnels. Elle repose sur des gestes que l'on apprend, des températures que l'on respecte et quelques préparations de base que l'on finit par connaître par cœur. Une fois ces fondations posées, le fraisier, le Paris-Brest ou la tarte au citron meringuée deviennent des projets tout à fait accessibles.</p>
<p>Vous trouverez d'abord les <strong>fondamentaux</strong> : le matériel vraiment utile, les ingrédients et leur rôle, les techniques essentielles, puis dix-huit <strong>préparations de base</strong> — pâtes, crèmes, ganaches, glaçages et biscuits — auxquelles les recettes renvoient par un simple numéro de page.</p>
<p>Viennent ensuite <strong>neuf chapitres</strong> de recettes, des gâteaux du quotidien aux entremets de fête, en passant par les biscuits, les viennoiseries et les desserts sans four. Le livre se termine par un <strong>carnet pratique</strong> : conversions, températures, guides des farines, des chocolats et des crèmes, conservation, lexique et index.</p>
</div>
<div class="h2" style="margin-top:7mm">Comment lire une fiche recette</div>
<div class="grid3" style="margin-top:3mm">
<div class="card"><h4>La première page</h4><p>Une grande image, une courte description, puis les repères pratiques : difficulté, temps de préparation, de cuisson et de repos, nombre de parts et réglage du four. Les ingrédients sont pesés en grammes et en millilitres.</p></div>
<div class="card"><h4>La seconde page</h4><p>La méthode, découpée en étapes numérotées et titrées. Dans la marge : les conseils de réussite, les erreurs à éviter, la conservation et un espace pour vos propres notes.</p></div>
<div class="card"><h4>Les renvois</h4><p>Lorsqu'une recette utilise une préparation de base, le renvoi <span class="see">→ p. 00</span> vous conduit directement à la bonne page. Sur tablette, il suffit de toucher le numéro.</p></div>
</div>
<div class="h2" style="margin-top:6mm">Les niveaux de difficulté</div>
<table class="tbl" style="margin-top:2mm">
<tr><td style="width:44mm"><span class="lvl"><i class="on"></i><i></i><i></i></span>&nbsp; Facile</td><td>Aucune technique particulière : idéal pour débuter ou pâtisser avec des enfants.</td></tr>
<tr><td><span class="lvl"><i class="on"></i><i class="on"></i><i></i></span>&nbsp; Intermédiaire</td><td>Quelques gestes à maîtriser (crème cuite, pâte à foncer, poche à douille). Lisez la recette en entier avant de commencer.</td></tr>
<tr><td><span class="lvl"><i class="on"></i><i class="on"></i><i class="on"></i></span>&nbsp; Avancé</td><td>Plusieurs préparations et des temps de repos : organisez-vous sur une ou deux journées, le résultat en vaut la peine.</td></tr>
</table>
</div>{folio(n)}</section>'''


def mentions(n, folio):
    who = config.AUTHOR or "l'autrice"
    return f'''<section class="page"><div class="txt fit" style="top:auto;bottom:30mm">
<div style="text-align:center"><span class="script" style="font-size:26pt">L'Art de la Pâtisserie</span></div>
<svg class="orn" viewBox="0 0 200 16"><path d="M0 8 H82 M118 8 H200" stroke="#B48E4F" stroke-width=".8"/><path d="M100 1 L107 8 L100 15 L93 8 Z" fill="none" stroke="#B48E4F" stroke-width=".9"/><circle cx="100" cy="8" r="1.8" fill="#B48E4F"/></svg>
<div style="max-width:120mm;margin:0 auto;text-align:center">
<p style="text-align:center;font-size:9.6pt">{config.EDITION} — {config.YEAR}</p>
<p style="text-align:center;font-size:9.6pt">© {config.YEAR} {who}. Tous droits réservés.</p>
<p style="text-align:center;font-size:9pt;color:#6F5E52;margin-top:5mm">Ce livre numérique est destiné à un usage strictement personnel. Toute reproduction, diffusion, revente ou mise à disposition, totale ou partielle, par quelque procédé que ce soit, est interdite sans autorisation écrite préalable (articles L.122-4 et L.335-2 du Code de la propriété intellectuelle). Vous pouvez bien entendu l'imprimer pour votre usage en cuisine.</p>
<p style="text-align:center;font-size:9pt;color:#6F5E52">Les textes et les recettes sont des créations originales. Les visuels sont des illustrations originales réalisées pour cet ouvrage.</p>
<p style="text-align:center;font-size:9pt;color:#6F5E52">Les temps de cuisson sont donnés pour un four ménager électrique préchauffé ; chaque four est différent, fiez-vous aussi aux indices visuels décrits dans les recettes. Les recettes contiennent des allergènes courants (gluten, œufs, lait, fruits à coque) : adaptez-les aux besoins de vos convives. Les préparations à base d'œufs crus sont déconseillées aux femmes enceintes, aux jeunes enfants et aux personnes fragiles.</p>
<p style="text-align:center;font-size:9pt;color:#6F5E52">Typographies : Cormorant Garamond, EB Garamond, Jost et Pinyon Script (licence SIL Open Font).</p>
</div></div>{folio(n)}</section>'''


def charte(n, folio, image):
    sw = [("Ivoire", "#FBF7F0"), ("Crème", "#F2E8D8"), ("Beige", "#E4D3BA"), ("Sable", "#CDB797"),
          ("Or", "#B48E4F"), ("Or clair", "#D4B57A"), ("Brun", "#6E4F3E"), ("Chocolat", "#3A2A22")]
    sws = "".join(f'<div><i style="background:{c}"></i><span>{nm.upper()}<br>{c}</span></div>' for nm, c in sw)
    return f'''<section class="page charte"><div class="txt fit">
<div class="kicker">Maquette · Direction artistique</div><h1>Charte graphique</h1>
<svg class="orn left" viewBox="0 0 200 16"><path d="M0 8 H82 M118 8 H200" stroke="#B48E4F" stroke-width=".8"/><path d="M100 1 L107 8 L100 15 L93 8 Z" fill="none" stroke="#B48E4F" stroke-width=".9"/><circle cx="100" cy="8" r="1.8" fill="#B48E4F"/></svg>
<p class="lead">Une pâtisserie de salon de thé parisien : lumière de fin d'après-midi, nappes de lin, porcelaine ivoire et touches d'or discrètes.</p>
<div class="h3">Palette</div><div class="sw">{sws}</div>
<div class="h3" style="margin-top:6mm">Typographies</div>
<div class="grid2">
<div class="card"><div style="font-family:Cormorant;font-size:30pt;color:#3A2A22;line-height:1">Cormorant Garamond</div><p>Titres et chiffres. Un Garamond de titrage aux contrastes marqués, élégant en grand corps.</p></div>
<div class="card"><div style="font-family:Garamond;font-size:20pt;color:#3A2A22">EB Garamond</div><p>Texte courant. Lisible à l'écran comme à l'impression, avec chiffres elzéviriens.</p></div>
<div class="card"><div style="font-family:Jost;font-size:12pt;letter-spacing:.28em;color:#B48E4F;padding:2mm 0">JOST — ÉTIQUETTES</div><p>Petites capitales espacées pour les repères : temps, rubriques, folios.</p></div>
<div class="card"><div style="font-family:Pinyon;font-size:26pt;color:#B48E4F;line-height:1.1">Pinyon Script</div><p>Accent calligraphique, utilisé avec parcimonie : chapitres et signatures.</p></div>
</div>
<div class="h3" style="margin-top:6mm">Principes de mise en page</div>
<ul class="dots"><li>Format A4 portrait, marges extérieures de 18 mm, folio centré en pied de page.</li>
<li>Chaque recette tient sur une double page : l'image et les ingrédients d'un côté, la méthode et les conseils de l'autre.</li>
<li>Trois compositions alternent (image pleine largeur, image encadrée, image en colonne) pour rythmer la lecture sans rompre l'unité.</li>
<li>Ouvertures de chapitre sur fond chocolat, filets et ornements dorés, médaillon rond.</li>
<li>Illustrations originales en nature morte : fond de mur clair, table en bois ou lin, lumière latérale, profondeur de champ.</li></ul>
</div>{folio(n)}</section>'''


# ------------------------------------------------------------------ introduction
def intro1(n, folio, B):
    return f'''<section class="page"><div class="hero" style="position:absolute;left:0;right:0;top:0;height:96mm;overflow:hidden">
<img src="img/intro-atelier.jpg" style="width:100%;height:100%;object-fit:cover;object-position:50% 62%"></div>
<div class="txt fit" style="top:106mm">
<div class="kicker">Introduction</div><h1 id="introduction">L'esprit de la pâtisserie</h1>
<svg class="orn left" viewBox="0 0 200 16"><path d="M0 8 H82 M118 8 H200" stroke="#B48E4F" stroke-width=".8"/><path d="M100 1 L107 8 L100 15 L93 8 Z" fill="none" stroke="#B48E4F" stroke-width=".9"/><circle cx="100" cy="8" r="1.8" fill="#B48E4F"/></svg>
<div class="cols2">
<p class="dropcap">La cuisine pardonne beaucoup : une pincée de sel en plus, quelques minutes de cuisson en moins, et le plat reste bon. La pâtisserie, elle, est une affaire d'équilibres. Une génoise lève parce que l'air emprisonné dans les œufs se dilate à la chaleur ; une crème pâtissière épaissit parce que l'amidon gonfle à l'ébullition ; une ganache est lisse parce que le gras du chocolat et l'eau de la crème forment une émulsion stable.</p>
<p>Comprendre ces mécanismes change tout. On ne suit plus une recette à l'aveugle : on sait pourquoi il faut tamiser la farine, pourquoi le beurre doit être « pommade » et pas fondu, pourquoi on n'ouvre pas la porte du four pendant la cuisson des choux. C'est l'ambition de ce livre : vous donner des recettes fiables, mais aussi les clés pour les réussir à chaque fois.</p>
<p>Toutes les quantités sont exprimées <strong>au poids</strong>, y compris les liquides lorsque la précision compte. Une balance de cuisine au gramme près est donc votre meilleure alliée — bien plus qu'un verre mesureur. Pour les œufs, nous comptons un œuf moyen (calibre M) à 50 g sans coquille : environ 30 g de blanc et 20 g de jaune.</p>
<p>Enfin, la pâtisserie se partage. Elle accompagne les anniversaires, les dimanches en famille, les goûters improvisés. Prenez le temps, lisez la recette jusqu'au bout avant de commencer, préparez vos ingrédients à l'avance — ce que les professionnels appellent la <em>mise en place</em> — et faites-vous plaisir.</p>
</div></div>{folio(n)}</section>'''


GOLDEN = [
    ("Lire la recette en entier", "avant d'allumer le four : vous repérerez les temps de repos et les ingrédients à sortir à l'avance."),
    ("Peser tout, toujours", "une balance au gramme près est indispensable ; les cuillères et les verres ne sont pas assez précis."),
    ("Sortir les ingrédients à l'avance", "beurre, œufs et produits laitiers à température ambiante (sauf indication contraire) s'émulsionnent mieux."),
    ("Préchauffer le four", "au moins 15 à 20 minutes. Un thermomètre de four révèle souvent un écart de 10 à 20 °C."),
    ("Respecter les temps de repos", "une pâte reposée se rétracte moins, une crème refroidie se tient, un entremets pris se démoule net."),
    ("Ne pas trop travailler les pâtes", "dès que la farine est incorporée, on s'arrête : un excès de pétrissage rend les pâtes dures."),
    ("Incorporer délicatement", "les blancs montés et les crèmes fouettées se mélangent à la maryse, en soulevant la masse."),
    ("Faire confiance à ses sens", "couleur, odeur, élasticité au toucher : les indices visuels complètent toujours le minuteur."),
    ("Travailler propre et sec", "un bol gras empêche les blancs de monter ; une goutte d'eau fait masser le chocolat."),
    ("Goûter et noter", "chaque four, chaque farine est différent : notez vos ajustements dans la marge prévue à cet effet."),
]


def intro2(n, folio, B):
    rules = "".join(f'<div class="step"><div class="n">{i}</div><p><b>{a}</b>{b}</p></div>' for i, (a, b) in enumerate(GOLDEN, 1))
    return f'''<section class="page">{'<div class="runhead"><span>Introduction</span><span>Les règles d\'or</span></div>'}
<div class="txt fit"><div class="kicker">Introduction</div><h1 style="font-size:32pt">Les dix règles d'or</h1>
<svg class="orn left" viewBox="0 0 200 16"><path d="M0 8 H82 M118 8 H200" stroke="#B48E4F" stroke-width=".8"/><path d="M100 1 L107 8 L100 15 L93 8 Z" fill="none" stroke="#B48E4F" stroke-width=".9"/><circle cx="100" cy="8" r="1.8" fill="#B48E4F"/></svg>
<p class="lead">Dix habitudes de pâtissier qui, à elles seules, évitent la plupart des déconvenues.</p>
<div class="steps" style="margin-top:2mm">{rules}</div>
<div class="card" style="margin-top:5mm;display:grid;grid-template-columns:1fr 1fr;gap:6mm">
<div><h4>Votre four</h4><p>Les températures de ce livre sont données en <strong>chaleur tournante</strong> sauf mention contraire. En chaleur statique (voûte et sole), augmentez de 10 à 15 °C et placez la plaque à mi-hauteur. Les pâtes feuilletées, les choux et les biscuits cuisent souvent mieux en statique : c'est alors précisé.</p></div>
<div><h4>Les unités</h4><p>g = gramme · ml = millilitre · cl = centilitre (10 ml) · c. à c. = cuillère à café (5 ml) · c. à s. = cuillère à soupe (15 ml). Un œuf moyen pèse 50 g sans coquille. Les conversions détaillées figurent en fin d'ouvrage.</p></div>
</div></div>{folio(n)}</section>'''


# ------------------------------------------------------------------ matériel
TOOLS = [
    ("balance", "Balance électronique", "Essentiel", "Précise au gramme, avec fonction tare. C'est l'outil le plus important du pâtissier : toutes les recettes sont pesées."),
    ("fouet", "Fouet & batteur", "Essentiel", "Un fouet à main pour les crèmes et un batteur électrique pour monter blancs et crème fouettée sans fatigue."),
    ("maryse", "Maryse", "Essentiel", "Spatule souple en silicone pour incorporer délicatement et racler les bols jusqu'à la dernière goutte."),
    ("thermo", "Thermomètre de cuisson", "Essentiel", "Sonde numérique pour le sucre cuit, la crème anglaise, le chocolat et la meringue italienne."),
    ("tamis", "Tamis fin", "Essentiel", "Pour aérer farine, cacao et sucre glace, et filtrer crèmes et coulis."),
    ("moule", "Moules de base", "Essentiel", "Un moule rond de 22 cm, un moule à cake de 26 cm, un moule carré de 20 cm et une plaque de cuisson."),
    ("tarte", "Cercles à tarte", "Essentiel", "Cercles perforés ou moules à fond amovible de 22–24 cm et tartelettes de 8–10 cm."),
    ("rouleau", "Rouleau à pâtisserie", "Essentiel", "Lisse et lourd, idéalement sans poignées, pour étaler les pâtes de façon régulière."),
    ("poche", "Poches à douille", "Utile", "Jetables ou lavables ; indispensables pour les choux, les meringues et les finitions."),
    ("douilles", "Douilles", "Utile", "Une unie de 10 mm, une unie de 14 mm, une cannelée de 12 mm et une douille à Saint-Honoré."),
    ("spatule", "Spatule coudée", "Utile", "Pour lisser une crème, étaler un biscuit ou soulever délicatement un entremets."),
    ("tapis", "Tapis de cuisson", "Utile", "En silicone ou en toile perforée : cuisson régulière des biscuits, sablés et macarons."),
    ("cercle", "Cercle à entremets", "Pour aller plus loin", "Cercles de 18 et 20 cm, hauteur 4,5 à 6 cm, avec du rhodoïd pour des bords nets."),
    ("mixeur", "Mixeur plongeant", "Pour aller plus loin", "Pour émulsionner une ganache ou un glaçage miroir sans incorporer de bulles."),
    ("robot", "Robot pâtissier", "Pour aller plus loin", "Précieux pour les pâtes levées (brioche, croissants) et les grandes quantités de meringue."),
    ("casserole", "Casseroles à fond épais", "Essentiel", "Une petite et une moyenne, en inox à fond épais, pour les crèmes et le caramel."),
    ("minuteur", "Minuteur", "Essentiel", "Un simple minuteur évite bien des cuissons oubliées."),
    ("emporte", "Emporte-pièces", "Utile", "Ronds unis et cannelés, en plusieurs diamètres, pour les sablés et les fonds de tartelettes."),
]


def tools_page(part):
    def f(n, folio, B):
        items = TOOLS[:10] if part == 0 else TOOLS[10:]
        cards = "".join(f'<div class="card"><h4>{TOOL_ICONS[i]}{t}<span class="tag">{tag}</span></h4><p>{d}</p></div>' for i, t, tag, d in items)
        head = ('<div class="kicker">Les fondamentaux</div><h1 id="materiel-h">Le matériel indispensable</h1>'
                '<svg class="orn left" viewBox="0 0 200 16"><path d="M0 8 H82 M118 8 H200" stroke="#B48E4F" stroke-width=".8"/><path d="M100 1 L107 8 L100 15 L93 8 Z" fill="none" stroke="#B48E4F" stroke-width=".9"/><circle cx="100" cy="8" r="1.8" fill="#B48E4F"/></svg>'
                '<p class="lead">Inutile de suréquiper sa cuisine : une douzaine d\'outils bien choisis suffisent pour réaliser toutes les recettes de ce livre.</p>') if part == 0 else \
            ('<div class="kicker">Les fondamentaux</div><div class="h-display" style="font-size:28pt;margin-bottom:4mm">Le matériel <em style="color:#6E4F3E">(suite)</em></div>')
        extra = ""
        if part == 1:
            extra = '''<div class="card" style="margin-top:5mm;background:#F2E8D8"><h4>Notre conseil</h4><p>Investissez d'abord dans une balance précise, un thermomètre-sonde et un bon moule à fond amovible. Préférez des moules métalliques clairs pour les cakes et les tartes : ils cuisent plus régulièrement que le silicone, qui convient en revanche très bien aux petites pièces (financiers, madeleines) et aux inserts congelés. Un rouleau de papier cuisson et du film alimentaire complètent l'équipement.</p></div>'''
        return (f'<section class="page"><div class="runhead"><span>Les fondamentaux</span><span>Matériel</span></div>'
                f'<div class="txt fit">{head}<div class="grid2">{cards}</div>{extra}</div>{folio(n)}</section>')
    return f


# ------------------------------------------------------------------ ingrédients
INGREDIENTS = [
    ("Les farines", "La farine de blé T45 (« farine de gruau » ou « fluide ») est la référence en pâtisserie : riche en amidon, elle donne des pâtes friables et des biscuits légers. La T55 convient aux pâtes à choux, pâtes brisées et brioches. Pour les viennoiseries, une farine de force (T45 riche en protéines, 11 à 13 %) donne une pâte plus élastique. Conservez-la au sec, à l'abri de l'humidité."),
    ("Les sucres", "Le sucre semoule sucre et structure ; le sucre glace (finement moulu, avec un peu d'amidon) s'utilise dans les pâtes sablées, les glaçages et les finitions. La cassonade et le sucre complet apportent des notes de caramel et du moelleux. Le sucre inverti ou le miel retiennent l'humidité et prolongent la fraîcheur des gâteaux."),
    ("Le beurre", "Choisissez un beurre doux à 82 % de matière grasse ; un beurre AOP (Charentes-Poitou, Isigny) apporte un goût incomparable. Pour le feuilletage, un beurre « de tourage », plus ferme, facilite le travail. « Beurre pommade » signifie mou, de la texture d'une crème, jamais fondu."),
    ("Les œufs", "Utilisez des œufs frais, de calibre moyen (M, 50 g sans coquille), à température ambiante. Les blancs se conservent plusieurs jours au réfrigérateur et se congèlent très bien ; les blancs « vieillis » de 24 à 48 h montent même plus facilement pour les macarons."),
    ("La crème et le lait", "La crème liquide entière à 30–35 % de matière grasse est indispensable pour la monter en chantilly ; elle doit être très froide. Le lait entier donne des crèmes plus onctueuses que le demi-écrémé. La crème épaisse (crème fraîche) n'est pas interchangeable avec la crème liquide dans les recettes."),
    ("Le chocolat", "Préférez du chocolat de couverture ou un chocolat pâtissier de qualité, avec un pourcentage de cacao clairement indiqué : 55 à 70 % pour le noir, 35 à 40 % pour le lait. Le cacao en poudre doit être non sucré. Le guide des chocolats, en fin d'ouvrage, détaille leurs usages."),
    ("Levures et poudres levantes", "La levure chimique (poudre à lever) agit à la chaleur du four ; on la tamise avec la farine. La levure de boulanger fraîche (ou sèche, en divisant le poids par trois) fait lever brioches et viennoiseries : elle ne doit jamais entrer en contact direct avec le sel ou le sucre en grande quantité."),
    ("Les gélifiants", "La gélatine en feuilles (2 g la feuille, force 200 Bloom) se réhydrate 10 minutes dans l'eau froide, puis se fond dans une préparation chaude. Comptez environ 1 feuille pour 120 à 150 g de crème ou de mousse à tenir. L'agar-agar, d'origine végétale, doit bouillir 1 minute pour agir et donne une texture plus ferme."),
    ("La poudre d'amande", "Ingrédient roi des financiers, de la crème d'amande, des macarons et des dacquoises. Choisissez-la blanche (amandes émondées) et fraîche ; gardez-la au réfrigérateur, car elle rancit vite. Les noisettes et pistaches en poudre s'utilisent de la même façon."),
    ("La vanille et les arômes", "Une gousse de vanille de Madagascar ou de Tahiti, fendue et grattée, parfume incomparablement crèmes et pâtes. À défaut, utilisez un extrait de vanille naturel (jamais d'arôme de synthèse). Les zestes d'agrumes non traités, la fleur d'oranger et les épices complètent la palette."),
    ("Le sel", "Une pincée de sel fin relève toutes les pâtes, y compris sucrées. La fleur de sel s'ajoute en finition, notamment sur le caramel et les cookies, pour son croquant."),
    ("Les fruits", "Privilégiez les fruits de saison, mûrs mais fermes pour les tartes. Les fruits surgelés conviennent très bien aux coulis, aux mousses et aux insertions, à condition de bien les égoutter après décongélation."),
]


def ingr_page(part):
    def f(n, folio, B):
        items = INGREDIENTS[:6] if part == 0 else INGREDIENTS[6:]
        cards = "".join(f'<div class="card"><h4>{t}</h4><p>{d}</p></div>' for t, d in items)
        head = ('<div class="kicker">Les fondamentaux</div><h1>Ingrédients &amp; produits de base</h1>'
                '<svg class="orn left" viewBox="0 0 200 16"><path d="M0 8 H82 M118 8 H200" stroke="#B48E4F" stroke-width=".8"/><path d="M100 1 L107 8 L100 15 L93 8 Z" fill="none" stroke="#B48E4F" stroke-width=".9"/><circle cx="100" cy="8" r="1.8" fill="#B48E4F"/></svg>'
                '<p class="lead">De bons produits simples font les meilleures pâtisseries. Voici ce qu\'il faut savoir de chacun d\'eux, et pourquoi ils comptent.</p>') if part == 0 else \
            ('<div class="kicker">Les fondamentaux</div><div class="h-display" style="font-size:28pt;margin-bottom:4mm">Ingrédients <em style="color:#6E4F3E">(suite)</em></div>')
        extra = ""
        if part == 1:
            extra = '''<div class="card" style="margin-top:5mm;background:#F2E8D8"><h4>Le placard idéal</h4><p>Farine T45 et T55, sucre semoule, sucre glace, cassonade, levure chimique, fécule de maïs, poudre d'amande, chocolat noir 64 %, chocolat au lait, cacao non sucré, gélatine en feuilles, gousses de vanille, fleur de sel. Au frais : beurre doux, crème liquide entière, lait entier, œufs, mascarpone, fromage frais.</p></div>'''
        return (f'<section class="page"><div class="runhead"><span>Les fondamentaux</span><span>Ingrédients</span></div>'
                f'<div class="txt fit">{head}<div class="grid2">{cards}</div>{extra}</div>{folio(n)}</section>')
    return f


# ------------------------------------------------------------------ techniques
TECH = [
    ("Chemiser un moule", "Beurrez le moule au pinceau, en remontant sur les bords, puis farinez-le et retournez-le pour ôter l'excédent. Pour un gâteau au chocolat, remplacez la farine par du cacao. Pour un démoulage parfait, ajoutez un disque de papier cuisson au fond."),
    ("Sabler et fraser", "Sabler consiste à frotter la farine et le beurre froid du bout des doigts jusqu'à obtenir un sable fin : la pâte sera friable. Fraser, c'est écraser la pâte avec la paume de la main, par petites portions, pour la rendre homogène sans la travailler."),
    ("Abaisser et foncer", "Étalez la pâte bien froide entre deux feuilles de papier cuisson, sur 2,5 à 3 mm. Déposez-la dans le cercle, faites-la descendre dans l'angle sans l'étirer, puis coupez l'excédent au ras du bord. Remettez au froid 20 minutes avant cuisson : la pâte ne se rétractera pas."),
    ("Cuire à blanc", "Piquez le fond de tarte, couvrez-le de papier cuisson et de billes de cuisson (ou de légumes secs), puis enfournez. Retirez les billes aux deux tiers de la cuisson pour laisser dorer le fond. Pour l'imperméabiliser, badigeonnez-le de jaune d'œuf battu et remettez 2 minutes au four."),
    ("Blanchir", "Fouetter vigoureusement des jaunes d'œufs avec du sucre jusqu'à ce que le mélange éclaircisse et devienne mousseux. Ne laissez jamais jaunes et sucre en contact sans les mélanger : le sucre « brûle » les jaunes et forme des grumeaux."),
    ("Monter des blancs", "Dans un bol parfaitement propre, fouettez les blancs à vitesse moyenne avec une pincée de sel ou quelques gouttes de citron. Ajoutez le sucre en pluie quand ils sont mousseux, puis augmentez la vitesse. Ils sont « fermes » lorsqu'ils forment un bec qui se tient au bout du fouet."),
    ("Incorporer délicatement", "Mélangez d'abord un tiers des blancs à la préparation pour la détendre, puis ajoutez le reste. Avec une maryse, coupez la masse par le centre, raclez le fond et remontez en tournant le bol d'un quart de tour. Arrêtez dès que le mélange est homogène."),
    ("Crémer le beurre", "Travaillez le beurre pommade avec le sucre au batteur jusqu'à ce que le mélange devienne pâle, léger et crémeux (3 à 5 minutes). Cet air emprisonné participe à la légèreté des cakes et des cookies."),
    ("Cuire une crème à la nappe", "Une crème anglaise cuit sans bouillir, à 82–84 °C. Elle est prête quand elle « nappe » la spatule : un trait tracé du doigt reste net. Au-delà de 85 °C, les jaunes coagulent et la crème tranche."),
    ("Réaliser un caramel", "À sec : versez le sucre en trois fois dans une casserole chaude, sans remuer avant qu'il ne fonde. Avec de l'eau : chauffez sucre et eau sans remuer, essuyez les parois au pinceau humide. Arrêtez la cuisson à la couleur ambrée, en versant la crème chaude petit à petit, en vous protégeant des projections."),
    ("Faire fondre le chocolat", "Au bain-marie, le bol ne touchant pas l'eau frémissante, ou au micro-ondes par séries de 30 secondes en mélangeant entre chaque. Le chocolat noir ne doit pas dépasser 50 °C, le lait et le blanc 45 °C. La moindre goutte d'eau le fait « masser »."),
    ("Émulsionner une ganache", "Versez la crème chaude en trois fois sur le chocolat haché, en mélangeant du centre vers l'extérieur à la maryse pour créer un « noyau » brillant et élastique. Terminez au mixeur plongeant, tête immergée, pour une texture parfaitement lisse."),
    ("Utiliser la gélatine", "Plongez les feuilles 10 minutes dans un grand bol d'eau très froide. Essorez-les, puis faites-les fondre dans une partie chaude de la préparation (50 à 60 °C), jamais bouillante. Si la préparation est froide, faites fondre la gélatine essorée 10 secondes au micro-ondes avec une cuillerée de celle-ci."),
    ("Remplir et utiliser une poche", "Placez la douille, tortillez la poche juste au-dessus pour éviter les fuites, puis posez-la dans un grand verre en rabattant les bords. Remplissez aux deux tiers, chassez l'air et tenez la poche bien verticale, à 1 cm de la plaque, en pressant du haut avec une main."),
    ("Dorer", "Battez un œuf entier avec une pincée de sel (ou un jaune avec une cuillerée de lait pour une couleur plus profonde). Appliquez au pinceau en couche fine, sans couler sur les bords tranchés d'une pâte feuilletée, qui ne pourrait plus se développer."),
    ("Tester la cuisson", "Plantez la lame d'un couteau ou un pique au centre du gâteau : elle doit ressortir sèche (ou avec quelques miettes humides pour un fondant). Une génoise cuite reprend sa forme quand on l'effleure ; un fond de tarte est doré jusque dans le fond."),
    ("Refroidir et démouler", "Laissez tiédir les gâteaux 10 minutes dans leur moule, puis démoulez-les sur une grille pour éviter que la vapeur ne ramollisse le dessous. Les entremets se démoulent bien froids, voire congelés, en chauffant le cercle quelques secondes au chalumeau ou avec un torchon chaud."),
    ("Tempérer le chocolat (simplifié)", "Faites fondre les deux tiers du chocolat à 50 °C, ajoutez hors du feu le tiers restant finement haché et mélangez jusqu'à 31–32 °C pour le noir (30 °C pour le lait, 29 °C pour le blanc). Il sera brillant et cassant une fois figé."),
]


def tech_page(part):
    per = 5

    def f(n, folio, B):
        items = TECH[part * per:(part + 1) * per] if part < 3 else TECH[15:]
        if part == 0:
            items = TECH[:4]
        else:
            items = TECH[4 + (part - 1) * 5: 4 + part * 5]
        blocks = "".join(
            f'<div style="break-inside:avoid;margin-bottom:3.4mm"><div class="h2" style="margin-top:0"><span class="badge-num" style="font-family:Cormorant;font-style:italic;color:#B48E4F;margin-right:2mm">{TECH.index((t, d)) + 1:02d}</span>{t}</div><p>{d}</p></div>'
            for t, d in items)
        if part == 0:
            head = ('<div class="hero" style="position:absolute;left:0;right:0;top:0;height:88mm;overflow:hidden"><img src="img/intro-techniques.jpg" style="width:100%;height:100%;object-fit:cover;object-position:50% 60%"></div>'
                    '<div class="txt fit" style="top:97mm"><div class="kicker">Les fondamentaux</div><h1>Techniques fondamentales</h1>'
                    '<svg class="orn left" viewBox="0 0 200 16"><path d="M0 8 H82 M118 8 H200" stroke="#B48E4F" stroke-width=".8"/><path d="M100 1 L107 8 L100 15 L93 8 Z" fill="none" stroke="#B48E4F" stroke-width=".9"/><circle cx="100" cy="8" r="1.8" fill="#B48E4F"/></svg>'
                    '<p class="lead" style="margin-bottom:3mm">Dix-huit gestes de base, ceux qui reviennent sans cesse dans les recettes. Prenez le temps de les lire une fois : ils deviendront vite des automatismes.</p>')
        else:
            head = ('<div class="runhead"><span>Les fondamentaux</span><span>Techniques</span></div>'
                    '<div class="txt fit"><div class="kicker">Les fondamentaux</div><div class="h-display" style="font-size:28pt;margin-bottom:5mm">Techniques <em style="color:#6E4F3E">(suite)</em></div>')
        return f'<section class="page">{head}<div class="cols2">{blocks}</div></div>{folio(n)}</section>'
    return f


SECTIONS = [
    dict(id="introduction", title="Introduction", pages=[intro1, intro2]),
    dict(id="materiel", title="Le matériel indispensable", pages=[tools_page(0), tools_page(1)]),
    dict(id="ingredients", title="Ingrédients & produits de base", pages=[ingr_page(0), ingr_page(1)]),
    dict(id="techniques", title="Techniques fondamentales", pages=[tech_page(0), tech_page(1), tech_page(2), tech_page(3)]),
]
