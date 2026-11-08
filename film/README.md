# Film d'animation 3D · Léna & Ruben

Un film d'animation 3D de 30 à 45 minutes sur votre histoire, fait avec des outils 100 % gratuits.

## Où trouver quoi
| Dossier / fichier | Contenu |
|---|---|
| [`bible/personnages.md`](bible/personnages.md) | Analyse des photos, fiches de Léna et Ruben, palette mesurée, proportions, expressions, gestes, costumes |
| [`bible/direction_artistique.md`](bible/direction_artistique.md) | Style, lumière, motif magique, couleurs par chapitre, règles de cohérence |
| [`bible/outils_gratuits.md`](bible/outils_gratuits.md) | Chaque outil, ses limites vérifiées, ce qui est indispensable ou non |
| [`bible/prompts_concept_art.md`](bible/prompts_concept_art.md) | Prompts pour les dessins de recherche dans ChatGPT gratuit |
| [`blender/01_atelier_personnages.py`](blender/01_atelier_personnages.py) | Script testé : palette, maquettes de proportions, toise, photos de référence, studio lumière, caméras |
| `references/photos/` | **Vos photos, uniquement sur votre ordinateur** (exclues du dépôt par `.gitignore`, même privé) |

## Le plan de production
| Phase | Contenu | Statut |
|---|---|---|
| 0 | Analyse des photos, direction artistique, bible, outils | ✅ fait |
| 1 | Dépôt privé, installer Blender, lancer l'atelier personnages | 👉 **en cours** |
| 2 | Installer MPFB2, créer la base du corps de Léna puis de Ruben | |
| 3 | Sculpter les visages d'après les photos (ressemblance) | |
| 4 | Cheveux, yeux, peau, vêtements | |
| 5 | Squelette, expressions officielles, gestes signatures | |
| 6 | Planches de référence finales (face, profil, 3/4, dos, expressions, pied) | |
| 7 | Scénario (validé avec vous, faits réels non modifiés) | |
| 8 | Story-board 3D (animatique) avec les maquettes | |
| 9 | Décors, puis animation chapitre par chapitre | |
| 10 | Voix, musique, rendu, montage dans DaVinci Resolve | |

### Le réalisme, franchement
40 minutes = 57 600 images. Un grand studio met des années avec des centaines de personnes.
Avec une personne débutante et des outils gratuits, c'est faisable **si** :
- on travaille **chapitre par chapitre** (chaque chapitre de 3 à 5 minutes est un vrai petit film terminé) ;
- on réutilise beaucoup (mêmes personnages liés, studio lumière commun, animations Mixamo pour le corps) ;
- on concentre l'animation fine sur les **visages et les moments clés**.
Compter **plusieurs mois** pour le film complet. Le premier chapitre terminé est le vrai jalon.

---

## 👉 ÉTAPE 1 · Préparer l'atelier des personnages

L'étape 1 est découpée en 4 petites parties. **On valide chaque partie avant la suivante.**

| Partie | Quoi | Statut |
|---|---|---|
| 1.A | Mettre le projet à l'abri dans un dépôt GitHub **privé** | 👉 maintenant |
| 1.B | Installer Blender (en français) | 👉 maintenant |
| 1.C | Télécharger le dossier du film et y ranger vos photos | après validation |
| 1.D | Lancer le script de l'atelier et enregistrer le fichier | après validation |

---

### 1.A · Créer un dépôt privé pour le film (5 minutes)

**Pourquoi un nouveau dépôt, et pas passer `lenarofe25-coder.github.io` en privé ?**
Ce dépôt-là fait tourner votre portfolio et le jeu MDR. Avec un compte GitHub gratuit,
**un site GitHub Pages ne peut être publié que depuis un dépôt public** : si on le passe
en privé, votre portfolio et le jeu disparaissent d'Internet (sauf à payer GitHub Pro).
Solution gratuite : le film part dans **son propre dépôt privé**, le portfolio reste public.

1. Ouvrez **github.com** et connectez-vous.
2. En haut à droite, cliquez sur le **+**, puis **New repository**.
3. *Repository name* : tapez `film-lena-ruben`.
4. Cochez **Private** (cadenas). Ne cochez **rien d'autre** (pas de README, pas de .gitignore, pas de licence).
5. Cliquez sur le bouton vert **Create repository**.
6. Donnez-moi l'accès : ouvrez https://github.com/apps/claude/installations/select_target ,
   choisissez votre compte `lenarofe25-coder`, puis dans **Repository access** :
   - si « All repositories » est coché : rien à faire ;
   - sinon, cliquez **Select repositories**, ajoutez `film-lena-ruben`, puis **Save**.

**Résultat attendu** : une page « Quick setup » vide, avec un cadenas 🔒 à côté du nom `film-lena-ruben`.

Ensuite, c'est moi qui y transfère tout le dossier `film`, puis je le retire du dépôt public.

### 1.B · Installer Blender (15 minutes)

1. Allez sur **blender.org**, cliquez sur le gros bouton bleu **Download**.
2. Le site propose automatiquement la bonne version :
   - **Windows** : téléchargez le fichier *Installer (.msi)*, double-cliquez dessus,
     puis *Next › Next › Install › Finish* sans rien changer.
   - **Mac** : vérifiez qu'il est écrit *Apple Silicon* (Mac M1, M2, M3, M4…) ou *Intel*
     (menu  › *À propos de ce Mac* pour savoir). Ouvrez le fichier `.dmg` et glissez
     l'icône Blender dans le dossier **Applications**.
3. Lancez Blender. Au premier lancement, une fenêtre **Quick Setup** apparaît :
   - *Language* : choisissez **Français** ;
   - laissez le reste tel quel, cliquez sur **Next** / **Continuer** jusqu'à la fin.
   - Si la fenêtre n'apparaît pas : menu **Edit › Preferences › Interface › Translation**,
     *Language* : **Français**, puis fermez la fenêtre (les préférences s'enregistrent seules).
4. Vérifiez la version : menu **Aide › À propos de Blender** (ou le grand écran d'accueil).
   Le numéro doit être **4.2 ou plus** (5.x, c'est parfait).
5. Fermez la fenêtre d'accueil en cliquant à côté. Vous voyez un **cube gris** au centre :
   c'est normal, le script le supprimera.

**Résultat attendu** : Blender ouvert, menus en français, un cube au centre.

### ✋ Avant de continuer, envoyez-moi :
- « 1.A fait » + le nom exact du dépôt privé ;
- « 1.B fait » + le **numéro de version** de Blender (ou une capture d'écran) ;
- votre ordinateur : **PC ou Mac**, et si possible la mémoire vive et la carte graphique
  (Windows : *Paramètres › Système › Informations système* ; Mac :  › *À propos de ce Mac*).

En cas de blocage à n'importe quel moment : envoyez une capture d'écran, on règle ça ensemble.

---

### 1.C · Télécharger le dossier du film *(instructions détaillées données après validation de 1.A et 1.B)*
### 1.D · Lancer le script de l'atelier *(instructions détaillées données après validation de 1.C)*
