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
| `references/photos/` | **Vos photos, uniquement sur votre ordinateur** (exclues du dépôt public, voir `.gitignore`) |

## Le plan de production
| Phase | Contenu | Statut |
|---|---|---|
| 0 | Analyse des photos, direction artistique, bible, outils | ✅ fait |
| 1 | Installer Blender, lancer l'atelier personnages | 👉 **en cours** |
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

## 👉 ÉTAPE 1 · Installer Blender et ouvrir l'atelier des personnages

**Ce qu'on fait** : installer Blender, puis lancer le script qui installe vos deux maquettes,
la palette officielle, vos photos de référence et le studio lumière.

**Logiciel** : Blender (gratuit). **Durée** : 20 à 30 minutes.

### 1.1 Installer Blender
1. Allez sur **blender.org** › bouton bleu **Download**.
2. Prenez la version proposée pour votre système (Windows / macOS / Linux). Installez-la normalement.
3. Ouvrez Blender. Une fenêtre d'accueil apparaît : cliquez **n'importe où à côté** pour la fermer.
4. Mettez Blender en français : menu **Edit › Preferences › Interface › Translation**,
   *Language* : **Français**. Fermez la fenêtre des préférences.

### 1.2 Récupérer le dossier du film
1. Sur GitHub, ouvrez la branche `claude/adoring-mccarthy-k024xs` de ce dépôt.
2. Bouton vert **Code › Download ZIP**. Décompressez-le.
3. Copiez le dossier **`film`** où vous voulez (par exemple *Documents/film*).
4. Dans `film/references/`, créez un dossier **`photos`** et mettez-y vos 3 photos
   (et toutes celles que vous voulez, en JPG ou PNG). Nommez-les par exemple
   `lena_porte.jpg`, `couple_ascenseur_noir.jpg`…

### 1.3 Lancer le script
1. Dans Blender, tout en haut, cliquez sur l'onglet **Scripting**.
2. Au centre, cliquez sur **Ouvrir** (icône de dossier), choisissez
   `film/blender/01_atelier_personnages.py`.
3. Cliquez sur le bouton **▶** (*Exécuter le script*) en haut de la zone de texte.
4. Revenez sur l'onglet **Layout** (en haut à gauche).
5. Survolez la grande vue 3D avec la souris et appuyez sur la touche **1 du pavé numérique** (vue de face)
   — sans pavé numérique : menu **Vue › Point de vue › Face**.
6. En haut à droite de la vue 3D, cliquez sur la 3ᵉ petite sphère (**Aperçu du matériau**).
7. **Fichier › Enregistrer sous…** › `film/blender/atelier_personnages.blend`.

### Résultat attendu
- Deux silhouettes côte à côte (Léna à gauche, Ruben à droite) qui ressemblent à
  [cette image](bible/images/maquettes_1_face.jpg), avec une toise entre les deux.
- Vos photos affichées à gauche de la scène (elles n'apparaissent pas au rendu).
- À droite de l'écran, dans la liste des objets : les collections **LENA**, **RUBEN**,
  **REFERENCES**, **STUDIO**.

**Envoyez-moi une capture d'écran quand c'est fait**, et répondez aux questions de la
fin de [`bible/personnages.md`](bible/personnages.md) + votre ordinateur. On passera ensuite à l'étape 2.

En cas de problème : copiez-moi le message d'erreur (menu *Fenêtre › Afficher/masquer la console système* sous Windows).
