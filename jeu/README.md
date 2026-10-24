# MDR : le jeu des memes entre copines

Jeu multijoueur en ligne : une salle privée, un code à partager, une situation par manche,
10 cartes par joueuse, une carte jouée en secret, un vote anonyme, 1 point pour la carte la plus votée.
10 manches par défaut (5 ou 15 au choix de l’hôte).

- Jeu : `https://lenarofe25-coder.github.io/jeu/`
- Invitation : `https://lenarofe25-coder.github.io/jeu/?code=MDR482`

## Architecture

Le site reste un site statique GitHub Pages. Le jeu est découpé en deux parties.

| Partie | Rôle | Où |
| --- | --- | --- |
| Interface | Pages statiques en HTML, CSS et JS sans étape de build, comme le portfolio | `jeu/` |
| Serveur temps réel | Cloudflare Worker et un Durable Object par salle : source de vérité, WebSocket, chronos | `server/` |
| Bibliothèques | `situations.json` et `cards.json`, deux fichiers indépendants et versionnés | `jeu/data/` |

Pourquoi Cloudflare Durable Objects ? GitHub Pages ne peut pas exécuter de serveur. Un Durable Object
par salle donne exactement ce qu’il faut à un jeu en salles privées :

- un seul acteur qui traite les messages l’un après l’autre, donc pas de double vote ni de double attribution de points en cas de requêtes simultanées ;
- des WebSockets ;
- un stockage persistant, qui survit aux redémarrages ;
- des alarmes pour les chronos, les déconnexions et l’expiration.

C’est disponible sur l’offre gratuite (Durable Objects à stockage SQLite). Supabase aurait demandé
d’écrire la machine à états en PL/pgSQL et d’ajouter une tâche planifiée pour les chronos.

### Ce que le serveur décide (jamais le navigateur)

`server/src/engine.js` est une machine à états pure, testée à part :

- **Salon** : pseudos uniques (insensibles à la casse et aux accents), 2 à 10 joueuses, statut « prête », réglages modifiables uniquement par l’hôte.
- **Manche, phase « pick »** : la même situation est tirée pour toutes, jamais répétée dans la partie. Chaque joueuse reçoit 10 cartes distinctes, tirées indépendamment, en évitant les cartes qu’elle a déjà eues. Le serveur vérifie que la carte jouée appartient bien à la main de la joueuse, et le choix est verrouillé.
- **Phase « vote »** : les réponses sont mélangées et numérotées 1, 2, 3… Le lien entre une réponse et sa propriétaire reste côté serveur. Pas d’auto-vote, un seul vote par joueuse.
- **Phase « results »** : 1 point pour chaque carte au nombre maximal de votes ; en cas d’égalité, chaque carte à égalité marque. C’est seulement à ce moment que les propriétaires sont révélées.
- **Vue par joueuse** : `viewFor()` est la seule fonction qui produit ce qui part vers un navigateur. Elle n’y met que la main de la joueuse, et jamais les propriétaires ni les votes avant les résultats.

### Règles de temps (annoncées dans le salon)

| Situation | Comportement |
| --- | --- |
| Chrono de sélection écoulé | Les joueuses qui n’ont pas validé passent leur tour. Toutes peuvent voter, et le nom des retardataires est affiché. |
| Moins de 2 cartes jouées | Manche sans vote ni point. |
| Chrono de vote écoulé | On compte les votes reçus. |
| Chrono désactivé | L’hôte peut « passer au vote » ou « clore le vote ». |
| Déconnexion | La joueuse est attendue 45 s, puis n’est plus attendue. En revenant avec son jeton (stocké dans le navigateur), elle retrouve sa main, ses points et sa place. |
| Moins de 2 joueuses présentes | Pause automatique, puis reprise automatique quand elles reviennent. |
| L’hôte quitte la partie ou est absente | Ses droits passent à une joueuse connectée. |
| Moins de 2 joueuses restantes | Fin de partie propre, avec le classement. |
| Salle inactive | Fermée après 30 min sans personne connectée, et au plus tard après 12 h. |

### Modèle de données

L’état d’une salle est un document unique, persisté par le Durable Object. Cela suffit pour 10 joueuses
et 15 manches, et rend chaque action atomique. Correspondance avec les entités demandées :

| Entité | Champ |
| --- | --- |
| Partie | `room` : `code`, `hostId`, `status` (lobby, playing, finished, closed), `config`, `createdAt`, `lastActivity` (expiration), `game.id` |
| Joueuse | `room.players[id]` : `name`, `tokenHash` (SHA-256 du jeton de reconnexion), `connected`, `absent`, `ready`, `score`, `roundsWon` |
| Manche | `game.round` : `n`, `situationId`, `phase`, `startedAt`, `deadline` |
| Cartes distribuées | `round.hands[joueuse] = [10 identifiants]` |
| Réponses | `round.answers = [{ aid, label, owner, cardId }]`, où `aid` est l’identifiant public anonyme |
| Votes | `round.votes[votante] = aid` |
| Historique | `game.history` : cartes gagnantes de chaque manche |

Aucune donnée personnelle hormis le pseudo. Tout est effacé à la fermeture de la salle.

### Sécurité

- Jeton de reconnexion aléatoire de 256 bits. Seule son empreinte SHA-256 est stockée. Le jeton est envoyé dans le premier message WebSocket, pas dans l’URL.
- Codes de salle au format `ABC123`, tirés avec `crypto.getRandomValues` (environ 12 millions de combinaisons), combinés au limiteur de débit ci-dessous et à l’expiration des salles.
- Limiteur par adresse IP : 10 créations de salle et 40 tentatives pour rejoindre par tranche de 10 minutes. Limiteur par connexion : 30 actions par tranche de 10 secondes.
- CORS et WebSocket limités aux origines de `ALLOWED_ORIGINS`.
- Toutes les entrées sont validées : taille des messages, pseudos (caractères invisibles retirés), réglages restreints à une liste de valeurs.
- Aucun secret côté client. Le Worker n’a besoin d’aucune clé.

## Bibliothèques de contenu

| | Nombre | Détail |
| --- | --- | --- |
| Situations | 504 | 11 catégories, dont « Humour noir » qui reste désactivée tant que l’hôte ne l’active pas |
| Cartes réponses | 621 | 294 phrases, 120 illustrations de réaction, 207 illustrations avec légende |

Les phrases, légendes et situations sont des textes originaux écrits pour le jeu. Les illustrations
viennent de [Fluent Emoji](https://github.com/microsoft/fluentui-emoji) (Microsoft, licence MIT) : il
y en a 209 dans `jeu/cards/img/`, avec la licence MIT.

**Pourquoi pas de « vrais » memes ?** Les modèles de memes connus (Imgflip, Know Your Meme…) sont des
images protégées par le droit d’auteur. L’API Imgflip ne donne aucun droit de redistribution sur
ses modèles. Le jeu n’en contient donc pas. Pour ajouter des photos de réaction sous licence libre,
utilise l’import Wikimedia Commons décrit plus bas.

### Ajouter ou modifier des cartes

1. Modifie `server/scripts/content-src/situations.mjs` ou `cards.mjs`.
2. Lance `npm run content` dans `server/`. Le script :
   - conserve les identifiants existants ;
   - garde les entrées retirées en `active: false` ;
   - détecte les doublons exacts et les quasi-doublons ;
   - vérifie chaque illustration, puis régénère `jeu/data/*.json`.
3. Commite et pousse. Le Worker recharge la bibliothèque publiée (`CONTENT_URL`) toutes les 10 minutes : **pas besoin de le redéployer**.

Pour désactiver une carte défectueuse sans la supprimer, passe son `active` à `false` dans `jeu/data/cards.json`.

### Importer des photos de réaction libres (Wikimedia Commons)

```sh
cd server
node scripts/import-commons.mjs --category "Category:Yawning cats" --game-category absurde --limit 30 --dry-run
node scripts/import-commons.mjs --category "Category:Yawning cats" --game-category absurde --limit 30
npm run content
```

Le script :

- ne garde que les licences domaine public, CC0, CC BY et CC BY-SA (pas de NC ni de ND) ;
- vérifie le type et la taille de chaque image ;
- écarte les doublons grâce à une empreinte SHA-256 ;
- enregistre l’auteur, la licence et l’URL source. L’attribution s’affiche sur la carte.

Relis les images avant de publier. Ce script n’a pas pu être exécuté contre l’API réelle depuis
l’environnement de développement (réseau bloqué). Seule sa logique de filtrage est testée.

## Mise en ligne (à faire une fois)

1. Crée un compte Cloudflare gratuit.
2. Dans `server/`, lance `npm ci`, puis `npx wrangler login`, puis `npx wrangler deploy`. Note l’URL affichée, par exemple `https://mdr-memes.<ton-compte>.workers.dev`.
3. Mets cette URL dans `jeu/config.js` (`server: '…'`), puis commite et pousse.
4. Facultatif, pour un déploiement automatique : crée les secrets GitHub `CLOUDFLARE_API_TOKEN` (modèle « Edit Cloudflare Workers ») et `CLOUDFLARE_ACCOUNT_ID`. Le workflow `.github/workflows/mdr-server.yml` testera puis déploiera à chaque push sur `main`.

Si le site change d’adresse, mets à jour `ALLOWED_ORIGINS` et `CONTENT_URL` dans `server/wrangler.toml`.

## Développement et tests

```sh
cd server && npm ci
npm run dev                                        # Worker local sur :8787 (copier .dev.vars.example en .dev.vars)
python3 -m http.server 8080 --directory ..          # le site sur :8080 → http://localhost:8080/jeu/
npm test                                           # règles du jeu, contenu, import (31 tests)
npm run test:e2e                                   # vrais clients WebSocket contre le Worker local (9 tests)
node test/ui.mjs                                   # partie complète dans Chromium : 2 iPhone + 1 ordinateur (Playwright)
```
