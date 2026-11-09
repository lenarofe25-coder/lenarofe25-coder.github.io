# L'Art de la Pâtisserie — 100 recettes gourmandes à réaliser chez soi

Ebook premium de pâtisserie française, au format A4 portrait, prêt à être vendu sur Etsy.

| Fichier | Contenu |
|---|---|
| `dist/L-Art-de-la-Patisserie.pdf` | Le livre complet : 257 pages, environ 15 Mo (limite Etsy : 20 Mo par fichier) |
| `dist/maquette.pdf` | Maquette de 36 pages : charte graphique et pages représentatives |
| `dist/etsy/` | 6 visuels de fiche produit (2000 px) et la couverture seule en PNG |
| `docs/fiche-etsy.md` | Titre, description et mots-clés pour la fiche Etsy |
| `photos/LISTE-DES-PHOTOS.csv` | Nom de fichier attendu pour chaque recette, si vous ajoutez vos photos |

Les PDF ne sont pas versionnés dans Git (voir `.gitignore`). Ils se régénèrent avec `./make.sh`.

## Contenu du livre

1. Couverture, page de bienvenue (« comment lire une fiche », niveaux de difficulté), mentions légales.
2. Sommaire détaillé sur deux pages, cliquable.
3. Introduction et dix règles d'or.
4. Matériel indispensable (18 outils, icônes dessinées).
5. Ingrédients et produits de base (12 fiches).
6. Techniques fondamentales (18 gestes).
7. **18 préparations de base** : pâte sucrée, pâte brisée, pâte feuilletée rapide, pâte à choux, crème pâtissière, crème d'amande, crème anglaise, chantilly, crème mousseline, praliné, ganache, ganache montée, glaçage miroir, caramel au beurre salé, génoise, biscuit joconde, biscuit cuillère, meringues.
8. **9 chapitres, 100 recettes**, avec une double page par recette :
   gâteaux et cakes (12) · tartes et tartelettes (11) · cookies et petits biscuits (11) · entremets (11) · desserts individuels (11) · brownies et gourmandises (11) · desserts sans cuisson (11) · viennoiseries et brioches (11) · desserts fruités et légers (11).
9. Guides : conversions, températures (thermostats, cuisson du sucre, repères au thermomètre), farines, chocolats, crèmes, conservation, lexique (37 termes), index alphabétique, pages de notes et quatrième de couverture.

Chaque fiche contient : une grande image, une description, la difficulté, les temps de préparation, de cuisson et de repos, le nombre de portions, la température du four, les ingrédients en grammes et en millilitres, les ustensiles, des étapes numérotées et titrées, des conseils de réussite, les erreurs à éviter, la conservation et un espace « Mes notes ». Quand une recette utilise une préparation de base, un renvoi « → p. XX » cliquable mène à sa page.

Le PDF contient des signets (le panneau de navigation des liseuses) et des liens internes.

## Personnaliser

- **Nom de l'autrice ou de la boutique** : remplissez `AUTHOR` et `SHOP` dans `src/config.py`. Ils apparaissent sur la couverture, les mentions légales et la quatrième de couverture.
- **Image de couverture** : `COVER_IMAGE` dans `src/config.py` (le nom d'une recette, par exemple `fraisier`).
- **Vos propres photos** : déposez `photos/<nom-de-la-recette>.jpg` (format paysage, 2000 px de large au minimum). Le nom exact attendu pour chaque recette est dans `photos/LISTE-DES-PHOTOS.csv`. La photo remplace automatiquement l'illustration, sur la fiche comme sur l'ouverture de chapitre.
- **Textes** : les recettes sont dans `src/content/recipes/c*.py`, les pages liminaires dans `src/content/front.py`, les bases dans `src/content/bases.py` et les guides dans `src/content/annexes.py`.

## Régénérer

```bash
./make.sh
```

Il faut Python 3 (avec Pillow) et Node.js (avec Playwright et Chromium). Le script :

1. assemble le HTML ;
2. dessine les illustrations ;
3. produit les PDF, en réduisant automatiquement le corps du texte d'une page trop pleine (et signale tout débordement restant) ;
4. crée les visuels Etsy.

## Structure

```
ebook-patisserie/
├── assets/fonts/         polices Google Fonts (licence SIL OFL, usage commercial autorisé)
├── src/
│   ├── config.py         titre, autrice, image de couverture
│   ├── style.css         toute la direction artistique (couleurs, typographie, mises en page)
│   ├── build.py          assemblage du livre, pagination, sommaire, renvois
│   ├── illus.py          générateur d'illustrations (SVG paramétriques)
│   ├── render_images.js  SVG -> JPEG
│   ├── render_pdf.js     HTML -> PDF A4 (ajustement automatique, signets, liens)
│   ├── preview.js        captures PNG de pages, pour le contrôle visuel
│   ├── etsy_mockups.py   visuels de fiche produit
│   └── content/          tous les textes et recettes
├── photos/               vos photos (facultatif)
└── dist/                 fichiers livrables
```

## Droits et points d'attention

- **Textes et recettes** : rédigés pour ce livre, ils ne copient aucun ouvrage. Les grands classiques (quatre-quarts, génoise, pâte à choux…) reprennent des proportions standard du métier, qui ne sont pas protégeables. La rédaction, elle, est originale.
- **Images** : ce sont des illustrations vectorielles originales, générées par le code de ce dossier. Elles ne viennent d'aucune banque d'images, d'aucun livre ni d'aucun site. Ce ne sont pas des photographies. Pour un rendu « photo », remplacez-les par vos propres clichés, ou par des images dont vous détenez les droits commerciaux.
- **Polices** : Cormorant Garamond, EB Garamond, Jost et Pinyon Script, sous licence SIL Open Font License. Leur incorporation dans un PDF vendu est autorisée.
- **Dépôt public** : ce dépôt GitHub est public. Les sources (et donc le texte des recettes) sont lisibles par tous. Avant de commercialiser le livre, déplacez ce dossier dans un dépôt **privé** et ne publiez jamais le PDF dans un dépôt public ni sur GitHub Pages.
- **Avant de vendre** : relisez le livre, imprimez quelques pages pour vérifier le rendu, et testez quelques recettes dans votre four. Les temps de cuisson sont donnés pour un four ménager en chaleur tournante.
