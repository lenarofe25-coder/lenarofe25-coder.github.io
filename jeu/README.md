# MDR : le jeu des memes entre copines

Jeu multijoueur en ligne : une salle privée, un code à partager, une situation par manche,
10 memes par joueuse, un meme joué en secret, un vote anonyme, 1 point pour le meme le plus voté.
10 manches par défaut (5 ou 15 au choix de l’hôte).

- Jeu : `https://lenarofe25-coder.github.io/jeu/`
- Invitation : `https://lenarofe25-coder.github.io/jeu/?code=MDR482`

## Architecture

Le site reste un site statique GitHub Pages. Le jeu est découpé en deux parties.

| Partie | Rôle | Où |
| --- | --- | --- |
| Interface | Pages statiques en HTML, CSS et JS sans étape de build, comme le portfolio | `jeu/` |
| Serveur temps réel | Cloudflare Worker et un Durable Object par salle : source de vérité, WebSocket, chronos | `server/` |
| Bibliothèques | `situations.json` et `memes.json`, deux fichiers indépendants et versionnés | `jeu/data/` |

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

Deux fichiers indépendants, versionnés dans `jeu/data/` :

| Fichier | Contenu |
| --- | --- |
| `situations.json` | Les 500 situations de Léna, 10 catégories de 50, tirées au hasard sans répétition dans une partie. |
| `memes.json` | La bibliothèque de memes visuels réels (seules cartes du jeu ; aucune phrase, aucun emoji). |

Chaque manche : une situation commune, 10 memes différents par joueuse (tirés indépendamment,
renouvelés à chaque manche, en évitant les memes déjà reçus dans la partie), un meme joué
en secret, puis le vote anonyme.

### Modifier les situations

Les situations s’écrivent dans `server/scripts/content-src/situations.mjs`, une phrase par ligne
entre guillemets, rangées en 10 catégories de 50. Après une modification, `npm run content`
(dans `server/`) régénère `jeu/data/situations.json` ; les tests vérifient qu’il y en a bien 500.
Une situation retirée reste dans le fichier avec `active: false` et n’est plus jamais tirée.
Une fois la modification fusionnée dans `main`, le jeu en ligne la prend en compte tout seul
(redéploiement automatique, puis rechargement des fichiers publiés sous 10 minutes).

### D’où viennent les memes

Trois API publiques et gratuites, conçues pour que des applications affichent leurs modèles :

| Source | API | Conditions relevées (archivées dans `server/memes/report/terms/`) |
| --- | --- | --- |
| Imgflip | `api.imgflip.com/get_memes` (100 modèles populaires) | Affichage des images hébergées autorisé à condition de mettre un lien vers imgflip.com |
| memegen.link | `api.memegen.link/templates` | API libre (code MIT), images servies par URL, pas de restriction d’affichage |
| Memeboat | `memebo.at/api/templates?search=` | Affichage autorisé avec un lien vers memebo.at ; usage automatisé modéré (1 requête/s) |

**Droits** : ces images (Drake, Distracted Boyfriend, Pikachu…) appartiennent à leurs auteurs.
Aucune source n’accorde de licence de redistribution, et aucune ne prétend en avoir. MDR ne copie
donc pas les images : il les affiche depuis les serveurs des sources, comme leurs conditions le
permettent, avec les liens retour exigés (pied de page de chaque écran de jeu, et lien vers la page
du meme dans la loupe). L’usage repose sur l’exception de parodie et de pastiche (art. L122-5 4° du
Code de la propriété intellectuelle) dans le cadre d’un jeu privé et non commercial. Si un ayant
droit le demande, désactive le meme (`active: false`).

### Import automatisé et vérifications

Le workflow `.github/workflows/memes-import.yml` (GitHub Actions, réseau ouvert) lance
`server/memes/collect.py`, qui :

1. récupère les catalogues Imgflip et memegen, puis cherche dans Memeboat chaque nom de
   `server/memes/wanted.txt` (≈ 470 memes connus) absent des deux premiers ;
2. télécharge chaque image et vérifie le statut HTTP, le type, le décodage et une taille minimale de 150 px ;
3. écarte les doublons, même sous un autre nom : empreinte SHA-256 et empreinte perceptuelle
   (pHash, distance ≤ 8) ;
4. conserve les identifiants d’un import à l’autre ; un meme nouveau arrive désactivé
   (`pendingReview`) jusqu’à sa vérification visuelle ;
5. produit des planches contact numérotées (artefact « planches-memes » du workflow, onglet
   Actions de GitHub ; elles ne sont pas publiées sur le site) pour la vérification à l’œil, qui alimente `server/memes/rejected.txt` (variantes, photos qui ne
   sont pas des memes, sujets politiques ou sensibles, modèles vides) ;
6. ouvre enfin chaque meme actif dans Chromium pour vérifier qu’il s’affiche réellement
   (`server/memes/report/navigateur.json`).

Le workflow « Partie test avec les vrais memes » joue en plus une partie complète dans Chromium à
chaque changement de l’interface ; ses captures d’écran sont dans l’artefact « captures-partie ».

Pour ajouter des memes : ajoute des noms dans `wanted.txt` et pousse. Ensuite, relis les planches
(entrées « [À VÉRIFIER] »), ajoute les refus éventuels dans `rejected.txt`, puis retire
`pendingReview` des memes validés dans `jeu/data/memes.json`. Le Worker recharge la bibliothèque
publiée sur le site toutes les 10 minutes.

## Mise en ligne (une seule fois, environ 5 minutes)

Le site est déjà servi par GitHub Pages ; il ne manque que le serveur du jeu, hébergé gratuitement
chez Cloudflare. Tout le reste est automatique.

1. Crée un compte gratuit sur https://dash.cloudflare.com/sign-up, puis ouvre une fois
   **Workers & Pages** : Cloudflare te propose alors ton sous-domaine `*.workers.dev` (accepte-le).
2. Dans Cloudflare, **My Profile → API Tokens → Create Token**, modèle **Edit Cloudflare Workers** :
   copie le jeton. Note aussi ton **Account ID** (affiché dans la colonne de droite de Workers & Pages).
3. Dans GitHub, dépôt `lenarofe25-coder.github.io` → **Settings → Secrets and variables → Actions →
   New repository secret** : crée `CLOUDFLARE_API_TOKEN` et `CLOUDFLARE_ACCOUNT_ID`.
4. Fusionne la branche du jeu dans `main` (ou relance le workflow « Jeu MDR » sur `main`).

Le workflow `.github/workflows/mdr-server.yml` teste tout, déploie le Worker, puis écrit lui-même
son adresse dans `jeu/config.js` et la publie : le jeu est jouable sur
https://lenarofe25-coder.github.io/jeu/ quelques minutes plus tard. Tant que le serveur n’est pas
déployé, la page du jeu l’indique clairement au lieu de proposer des parties qui échoueraient.

Si le site change d’adresse, mets à jour `ALLOWED_ORIGINS` et `CONTENT_URL` dans `server/wrangler.toml`.

## Développement et tests

```sh
cd server && npm ci
npm run dev                                        # Worker local sur :8787 (copier .dev.vars.example en .dev.vars)
python3 -m http.server 8080 --directory ..          # le site sur :8080 → http://localhost:8080/jeu/
npm test                                           # règles du jeu et bibliothèques (28 tests)
npm run test:e2e                                   # vrais clients WebSocket contre le Worker local (9 tests)
node test/ui.mjs                                   # partie complète dans Chromium : 2 iPhone + 1 ordinateur
                                                   # (MDR_OFFLINE_IMAGES=1 si les images de memes sont injoignables)
```
