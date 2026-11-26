# Planner E6 · BTS SIO SISR

Planner de révision sur deux semaines pour l’épreuve E6 *Administration des systèmes et des réseaux*
(BTS SIO, option SISR). En ligne : https://lenarofe25-coder.github.io/revisions/

- **Version interactive** (`index.html`) : cases à cocher, notes, niveau de maîtrise, notes aux quiz et
  aux BTS blancs, barres de progression par bloc. Tout est sauvegardé dans le navigateur ; les boutons
  *Exporter* / *Importer* permettent de garder une copie ou de changer d’ordinateur.
- **Version imprimable** (`planning-e6-sisr.pdf`) : 25 pages A4 paysage, vierges, liens cliquables.
  Le bouton *Imprimer* de la version interactive imprime le planner avec ce que tu as rempli.

## Contenu

| Pages | Contenu |
|---|---|
| 1–2 | Couverture, mode d’emploi, l’épreuve E6 en bref, planning visuel des 14 jours |
| 3–7 | Semaine 1 : une page par jour (programme, méthode, exercices, quiz, ressources, notes, bilan) |
| 8–9 | BTS blanc n°1 (blocs 1 à 4) : sujet complet, puis bilan |
| 10–14 | Semaine 2 : une page par jour |
| 15–16 | BTS blanc n°2 (6 blocs) : sujet complet, puis bilan |
| 17 | Suivi de progression des 6 blocs |
| 18–22 | Catalogue des ressources (titre, sujet, niveau, type, lien direct) |
| 23–25 | Corrigés : quiz express, exercices et corrections détaillées des BTS blancs |

Les samedis sont des jours de repos, les dimanches sont réservés aux BTS blancs.

## Modifier le planner

Tout le contenu (programme, exercices, quiz, ressources, BTS blancs) est dans `data.js` ;
`app.js` ne fait que la mise en page. Après une modification :

```sh
cd revisions
tools/check-links.sh <(grep -oP "u: '\Khttps[^']+" data.js)   # revérifie chaque lien
node tools/build-pdf.mjs                                       # régénère le PDF et contrôle qu'aucune page ne déborde
```

`build-pdf.mjs` utilise Playwright (Chromium) et échoue si un élément sort d’une feuille A4.

Polices : Inter et Fraunces (licence SIL Open Font, voir `fonts/`), embarquées pour un rendu identique
à l’écran et à l’impression.
