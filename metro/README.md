# Quai : départs en temps réel (métro, RER, Transilien, tram)

En ligne : `https://lenarofe25-coder.github.io/metro/` (à ajouter à l’écran d’accueil du téléphone).

## Ce que fait l’appli

- **Itinéraire** : tape une adresse, une gare ou un lieu ; départ depuis ta position (ou une gare choisie),
  maintenant ou à l’heure voulue. Chaque itinéraire montre les lignes, la marche, les perturbations.
- **Détail d’un trajet** : pour chaque ligne, la direction, la mission (RER), le nombre d’arrêts,
  les **3 prochains passages en temps réel avec la voie**, et un bouton « Panneau en temps réel ».
- **Phrase directe** : `nation rer a vers val de fontenay`, `chatelet ligne 14 direction saint-denis`,
  `gare de lyon m1 -> la défense`. L’appli ouvre le panneau de la gare, filtré sur la ligne,
  et **surligne les trains qui vont vraiment à ta destination** (utile sur les branches du RER).
- **Panneau d’une gare** : toutes les lignes ou une seule, destination, code mission, voie, retard,
  « à quai », trains supprimés, train court/long. Actualisation toutes les 30 s.
- **Gares autour de moi**.
- **Où se mettre sur le quai** : pour chaque trajet, un repère avant / milieu / arrière (sens de la marche)
  pour la correspondance suivante ou la sortie, avec un détail libre (voiture, porte, n° de sortie).

### À propos du placement sur le quai

Aucune donnée ouverte d’Île-de-France Mobilités ne dit dans quelle voiture monter (Citymapper constitue
ses propres relevés). L’appli ne l’invente donc pas : tu enregistres tes repères une fois, ils
réapparaissent ensuite à chaque trajet identique. Les repères partagés pour tout le monde vont dans
[`data/quais.json`](data/quais.json) (Réglages → « Copier (JSON) », puis coller dans `conseils`).

## Données

[PRIM](https://prim.iledefrance-mobilites.fr), la plateforme gratuite d’Île-de-France Mobilités :

| Besoin | API PRIM |
| --- | --- |
| Recherche de lieux, itinéraires, lignes d’une gare | Navitia (`v2/navitia/places`, `journeys`, `stop_areas/…/lines`) |
| Panneau temps réel | SIRI Lite `stop-monitoring` (secours : `stop_areas/…/departures` de Navitia) |

## Mise en route (une seule fois)

1. Crée un compte sur prim.iledefrance-mobilites.fr, puis **Mon compte → Mon jeton** pour générer ta clé.
2. Dans GitHub : **Settings → Secrets and variables → Actions → New repository secret**,
   nom `PRIM_API_KEY`, valeur = ta clé. Les secrets Cloudflare du jeu MDR servent aussi ici.
3. Fusionne sur `main` (ou lance le workflow « Relais PRIM » à la main) : le relais `metro-proxy/`
   est déployé sur Cloudflare et son adresse est écrite dans `metro/config.js`.

Le relais garde la clé côté serveur, n’accepte que le site et ne laisse passer que les routes utiles.

**Sans relais**, tu peux aussi coller ta clé dans les réglages de l’appli (⚙︎) : elle reste sur ton téléphone
et l’appli appelle PRIM directement.

## Développement local

```sh
cd metro-proxy && echo "PRIM_API_KEY=ta-clé" > .dev.vars && npx wrangler dev --port 8788
# autre terminal, à la racine du dépôt
python3 -m http.server 8080   # puis http://127.0.0.1:8080/metro/
```
