# Plan technique : un film d'animation 3D de 30 à 45 minutes pour 0 €

*Document de travail du projet. Version 1, novembre 2026.*

Ce document sert de « bible technique » du film. Il dit quels outils utiliser, dans quel ordre,
et ce qu'on peut raisonnablement atteindre seule avec du matériel personnel et des logiciels gratuits.

> **Note de confidentialité** : ce dépôt est public. Garder ici uniquement la technique.
> Les souvenirs, photos, voix et le scénario intime doivent rester dans un dossier privé
> (disque dur, Google Drive privé…), pas sur GitHub.

---

## 1. Le constat honnête

**Ce qui est vraiment gratuit et de niveau professionnel :**

- **Blender** (modélisation, sculpture, rig, animation, rendu, compositing) : logiciel libre, gratuit pour toujours, utilisé dans des films primés (*Flow*, Oscar 2025 du meilleur film d'animation, a été rendu avec Blender).
- **DaVinci Resolve** (version gratuite) : montage, étalonnage, mixage son. Largement suffisant pour un film en 1080p ou 4K.
- **DCP-o-matic** : logiciel libre qui fabrique le DCP, le format des salles de cinéma.

**Ce qui n'est pas réaliste :**

Une équipe Disney compte des centaines de personnes pendant 4 à 5 ans pour 90 minutes. Un animateur
professionnel de long métrage produit **3 à 5 secondes d'animation finie par semaine**.
Seule, débutante ou intermédiaire, 40 minutes de jeu d'acteur 3D image par image en qualité *Raiponce*
demanderaient plusieurs années.

**Le calcul de rendu :** 40 min × 60 s × 24 images/s = **57 600 images**.
- En Eevee (moteur temps réel de Blender) à ~15 s par image : ~240 heures de calcul. **Faisable.**
- En Cycles (moteur photoréaliste) à ~3 min par image : ~2 900 heures, soit 4 mois de PC allumé jour et nuit. **À réserver à quelques plans.**

**Conclusion :** on ne cherche pas à faire « un Disney de 40 minutes ». On fabrique **un conte
de 30 à 40 minutes conçu dès l'écriture pour être réalisable**, où l'énergie va aux scènes qui
comptent émotionnellement, et où la mise en scène (lumière, musique, caméra, montage) fait le reste.
C'est ce que font tous les films indépendants réussis.

---

## 2. Les deux méthodes demandées, comparées

### Méthode A : images générées par IA, mises en profondeur et en mouvement

**Principe :** générer chaque plan en image fixe (ChatGPT, ou Stable Diffusion/Flux en local), puis
l'animer : parallaxe 2.5D dans Blender (carte de profondeur), ou IA « image vers vidéo » en local
(FramePack, Wan 2.2, LTX-Video).

| | |
|---|---|
| **Avantages** | Images très belles immédiatement ; décors magnifiques ; pas besoin d'apprendre la 3D en profondeur ; rapide pour les paysages. |
| **Inconvénients** | **Les visages changent d'un plan à l'autre** (le défaut majeur) ; vêtements qui varient ; mouvements « flottants » ; pas de vrai jeu d'acteur (dialogues, regards, gestes précis) ; mains et corps déformés ; résultat qui ressemble vite à un diaporama. |
| **Temps** | 200 à 400 h pour 40 min. |
| **Difficulté** | Facile à moyenne (moyenne à difficile si on installe l'IA vidéo en local). |
| **Limite de qualité** | Plans de 3 à 5 s, cohérence faible, peu de dialogues filmés. Fatigue du spectateur au-delà de 10 min. |
| **Limites du gratuit** | ChatGPT gratuit : quota d'images non publié, de l'ordre de quelques images par jour (souvent cité : ~3/jour), qui varie selon la charge. Les sites de vidéo IA (Kling, Hailuo, Runway…) fonctionnent par **crédits** : gratuits en petite quantité, filigrane, résolution réduite, conditions qui changent. **On ne bâtit pas un film dessus.** |
| **Vidéo IA en local (vraiment gratuite)** | FramePack : fonctionne dès 6 Go de VRAM (cartes RTX 30/40/50) mais lent (exemple mesuré : ~1 h pour 5 s sur un portable RTX 4060). Wan 2.2 : 8 à 16 Go de VRAM en version quantifiée. Sans carte NVIDIA correcte : inutilisable. |

### Méthode B : vrais personnages et décors 3D dans Blender

| | |
|---|---|
| **Avantages** | **Visages 100 % cohérents** (c'est le même modèle partout) ; vraies expressions et vrais dialogues ; caméra libre ; vêtements et coiffures identiques d'un plan à l'autre ; qualité qui progresse avec ton niveau ; le résultat t'appartient entièrement. |
| **Inconvénients** | Courbe d'apprentissage réelle (2 à 3 mois pour être à l'aise) ; l'animation des personnages est très longue ; il faut un PC correct. |
| **Temps** | 1 500 à 3 000 h pour 40 min entièrement animées. Trop. |
| **Difficulté** | Difficile. |
| **Limite de qualité** | Avec le style « conte stylisé », très beau rendu possible. Le point faible sera la fluidité du jeu d'acteur, pas l'image. |

### Méthode C (recommandée) : « Le Conte Vivant », hybride

**Idée centrale :** le film est raconté comme un **livre de conte qui s'ouvre**. Ce choix narratif
justifie plusieurs textures visuelles dans le même film, ce qui permet de répartir l'effort :

| Niveau | Part du film | Technique | Effort |
|---|---|---|---|
| **1. Scènes de cœur** (rencontre, premier regard, dispute, déclaration, final) | ~25 % (8 à 10 min) | 3D Blender, jeu d'acteur complet, gros plans, expressions, synchro labiale | Maximum |
| **2. Scènes de récit** (voyages, marches, danses, plans larges) | ~35 % | Mêmes personnages 3D mais animation légère : cycles de marche (Mixamo), poses tenues, personnages de dos ou en silhouette, **la caméra et la lumière font le mouvement** | Moyen |
| **3. Pages du livre** (transitions, souvenirs, passé, ellipses) | ~25 % | Illustrations peintes (ChatGPT ou Stable Diffusion local) animées en 2.5D dans Blender : parallaxe, particules, brume, lucioles, voix de la narratrice | Faible |
| **4. Merveilleux et paysages** (royaume vu du ciel, saisons, magie) | ~15 % | Décors 3D procéduraux Blender, ou IA image-vers-vidéo en local si ton PC le permet | Faible à moyen |

**Pourquoi c'est la meilleure option :** les visages restent cohérents (seuls les modèles 3D jouent
les scènes de dialogue), les plus beaux décors viennent de l'IA, et la charge d'animation
passe de ~40 min à ~10 min de jeu d'acteur complet.

**Temps estimé :** 800 à 1 200 heures, soit **12 à 18 mois à 15-20 h par semaine**.
Pour un délai plus court : viser 30 minutes, ou réduire le niveau 1 à 6 minutes.

---

## 3. La boîte à outils 100 % gratuite

Statut vérifié en novembre 2026. Les offres « freemium » sont signalées : ne jamais en dépendre.

### Indispensables (gratuits et sans limite)

| Outil | Rôle | Statut |
|---|---|---|
| **Blender 4.x / 5.x** | Tout le travail 3D, rendu Eevee/Cycles, compositing | Libre (GPL) |
| **Human Base Meshes** (blender.org, fichiers de démo) | Bases de corps et de têtes humaines propres | CC0, gratuit |
| **Rigify** (inclus dans Blender) | Squelette d'animation corps + visage | Inclus |
| **Mixamo** (Adobe) | Animations de base (marche, course, danse) à retoucher | Gratuit avec un compte Adobe gratuit |
| **Rhubarb Lip Sync** + extension Blender | Synchronisation automatique des lèvres à partir de la voix | Libre |
| **DaVinci Resolve** (gratuit) | Montage, étalonnage, mixage (Fairlight) | Gratuit (la version Studio payante est inutile ici) |
| **Audacity** | Enregistrement et nettoyage des voix | Libre |
| **MuseScore 4 + Muse Sounds** | Composer une musique orchestrale avec de beaux sons d'orchestre | Gratuit |
| **Freesound.org** | Bruitages (pas, vent, magie, cheval…) | Gratuit, licences CC (vérifier CC0/CC-BY) |
| **Poly Haven / ambientCG** | Textures, ciels HDRI, modèles de décor | CC0 |
| **Krita** | Peinture numérique, retouches d'illustrations, storyboard | Libre |
| **DCP-o-matic** | Fichier DCP pour le cinéma | Libre |
| **Upscayl** | Agrandir des images IA en haute résolution | Libre |

### Utiles avec un bon PC (gratuits, en local)

| Outil | Rôle | Matériel conseillé |
|---|---|---|
| **ComfyUI** ou **Forge** + SDXL / Flux schnell | Générer décors et illustrations sans quota | Carte NVIDIA 8 Go+ |
| **Depth Anything V2** | Cartes de profondeur pour animer les illustrations en 2.5D | 4 Go+ |
| **FramePack / Wan 2.2 / LTX-Video** | Image vers vidéo pour paysages et magie | 6 à 16 Go de VRAM, 16 à 32 Go de RAM |
| **Hunyuan3D-2 / TRELLIS** | Transformer une image en objet 3D (accessoires, pas les héros) | 8 à 16 Go ; aussi en démo sur Hugging Face, avec quota quotidien |
| **SheepIt Render Farm** | Ferme de rendu communautaire gratuite : ton PC calcule pour les autres, les autres pour toi | Gratuit, échange de points |

### Assistants IA (versions gratuites)

- **Claude** : scénario, dialogues, découpage, fiches de plans, prompts, scripts Python pour Blender, résolution de problèmes techniques.
- **ChatGPT** : fiches personnages stylisées, planches de décors, croquis de storyboard. Quota d'images limité : **chaque image doit être réfléchie** (le prompt est préparé avec Claude avant).

### Écartés (payants ou pièges)

- FaceBuilder (KeenTools), Auto-Rig Pro, Human Generator, Character Creator : payants.
- Kling, Runway, Hailuo, Pika, Sora : crédits, filigrane. Au mieux un plan d'appoint, jamais la base.
- **Suno** : depuis l'accord avec Warner, le compte gratuit ne permet qu'un nombre très limité de téléchargements, et les morceaux du plan gratuit sont réservés à un usage non commercial. Risqué pour une projection publique : à éviter pour la bande originale.

---

## 4. Matériel minimum

| | Minimum | Confortable |
|---|---|---|
| Carte graphique | GTX 1660 / RTX 2060 6 Go | RTX 3060 12 Go ou mieux |
| Mémoire vive | 16 Go | 32 Go |
| Stockage | 500 Go libres | SSD 1 To + disque de sauvegarde |
| Écran | 1080p | Écran calibré |
| Son | Smartphone récent dans un placard rempli de vêtements | Micro USB d'occasion |

Un Mac Apple Silicon fonctionne très bien avec Blender et Resolve, mais l'IA vidéo locale y est
lente et limitée. Si ton PC est trop faible : **Eevee uniquement, SheepIt pour les rendus, et
illustrations via ChatGPT.**

---

## 5. Les choix artistiques qui rendent le projet possible

1. **Style « conte stylisé »**, comme *Raiponce* : grands yeux, formes simples, peau douce, éclairage chaud. Plus beau et **beaucoup plus facile** que le réalisme.
2. **Ressemblance par les signatures**, pas par la photo : forme du visage, coiffure, couleur et texture des cheveux, sourcils, grain de beauté, sourire, différence de taille, gestes typiques, un accessoire fétiche.
3. **Peu de personnages animés** : la princesse, le prince, un compagnon animal (énorme ressource comique et émotionnelle), 2 ou 3 personnages secondaires. Les foules en silhouettes.
4. **4 à 6 décors principaux**, réutilisés sous différentes lumières (aube, nuit, neige, fête).
5. **Une narratrice** (ta voix, ou celle d'un proche) : elle relie les scènes et permet les ellipses.
6. **Grammaire de caméra lente** : travellings, grues, plans longs. Ça fait « cinéma » et ça cache les limites d'animation.
7. **Lumière et musique d'abord** : un plan simple, bien éclairé, sur une belle musique, émeut plus qu'un plan complexe mal éclairé.

---

## 6. Feuille de route par phase

| Phase | Contenu | Livrable | Durée indicative |
|---|---|---|---|
| **0. Formation** (en parallèle des phases 1-2) | Blender : interface, modélisation, sculpture, matériaux, lumière, animation. Tutoriels gratuits (Blender Guru « Donut », Grant Abbitt, CG Boost, chaîne officielle Blender) | Un premier petit personnage animé de 10 s | 6 à 10 semaines |
| **1. Notre histoire** | Questionnaire, souvenirs, photos, objets, chansons | Chronologie réelle | 1 à 2 semaines |
| **2. Le conte** | Transposer les souvenirs en symboles féeriques | Synopsis + bible du monde | 2 semaines |
| **3. Personnages** | Fiches stylisées (ChatGPT), modélisation, cheveux, vêtements, rig, expressions | Princesse + prince + compagnon prêts à animer | 8 à 12 semaines |
| **4. Décors** | Concept art, maquettes 3D, matériaux, lumière | 4 à 6 décors réutilisables | 6 à 8 semaines |
| **5. Scénario** | Séquencier, dialogues, découpage technique avec niveau 1/2/3/4 par plan | Scénario + liste des plans | 3 à 4 semaines |
| **6. Storyboard + animatique** | Croquis + voix témoins + musique provisoire, montés dans Resolve | Le film entier en version brouillon chronométrée | 4 semaines |
| **7. Production** | Enregistrement des voix, animation, rendu plan par plan | Plans rendus en séquences d'images | 6 à 9 mois |
| **8. Montage, son, musique** | Montage final, étalonnage, bruitages, mixage | Master du film | 4 à 6 semaines |
| **9. Projection** | DCP, test en salle, droits | DCP vérifié en salle | 2 semaines |

**Règle d'or :** l'**animatique** (phase 6) est la vraie première version du film. Si elle émeut en
croquis, le film émouvra. Elle permet de couper avant de produire, ce qui économise des mois.

---

## 7. Pipeline détaillé d'un personnage (phase 3)

1. **Photos de référence** : face, profil, trois-quarts, sourire, cheveux de dos, en pied. Lumière douce.
2. **Fiche stylisée avec ChatGPT** : planche de référence (face / trois-quarts / profil) en style conte 3D. Plusieurs essais, on garde la meilleure. *Elle sert de plan d'architecte, pas d'image finale.*
3. **Base** : tête et corps à partir des Human Base Meshes (CC0).
4. **Sculpture** dans Blender, avec la fiche et les photos en images de référence derrière le modèle.
5. **Retopologie** propre autour des yeux et de la bouche (indispensable pour les expressions).
6. **Yeux** : globes séparés avec iris, cornée et reflet (la vie du personnage passe par là).
7. **Cheveux** : système de courbes de Blender (Hair Curves + nœuds de géométrie intégrés).
8. **Vêtements** : modélisés, puis simulation de tissu pour capes et jupes.
9. **Rig** : Rigify corps + visage, et **shape keys** pour 12 à 15 expressions clés (sourire, rire, surprise, tristesse, colère, timidité, voyelles A E I O U, M B P, F V).
10. **Test de validation** : le personnage dit une phrase, sourit, cligne des yeux, tourne la tête. Si ça marche, on passe à la suite.

## 8. Pipeline d'un plan (phase 7)

1. Fiche du plan (générée avec Claude) : numéro, durée, niveau 1-4, cadrage, mouvement de caméra, action, dialogue, lumière, musique.
2. **Référence vidéo** : tu joues la scène devant ton téléphone. Indispensable pour un mouvement naturel.
3. Blocage (poses clés) → animation fine → expressions → synchro labiale (Rhubarb + retouches).
4. Caméra : focale, profondeur de champ, légère vibration à la main si besoin.
5. Rendu Eevee en **séquence PNG/EXR** (jamais directement en vidéo : en cas de plantage on ne perd rien).
6. Import dans Resolve, à la place du plan d'animatique.

## 9. Méthode « pages du livre » (niveau 3)

1. Illustration générée (ChatGPT ou local), cohérente avec la palette du film.
2. Découpage en 3 à 6 calques (fond, plans intermédiaires, premier plan) dans Krita, ou carte de profondeur via Depth Anything.
3. Calques sur des plans dans Blender, espacés en profondeur.
4. Caméra lente, brume volumétrique, particules (lucioles, neige, pétales), lumière animée.
5. Les héros, s'ils apparaissent, sont en silhouette ou en modèle 3D posé (pour garder les visages cohérents).

---

## 10. Son et musique

- **Voix** : jouées par vous-mêmes et vos proches. C'est ce qui rendra le film unique. Enregistrement : pièce feutrée, téléphone à 20 cm, plusieurs prises, nettoyage dans Audacity ou Resolve.
- **Musique** : trois options gratuites et sûres :
  1. Composer les thèmes principaux dans **MuseScore + Muse Sounds** (je peux aider à écrire mélodies et harmonies).
  2. Musique classique du domaine public (Musopen), à condition que l'enregistrement aussi soit libre.
  3. Musiques sous licence Creative Commons (Free Music Archive, Kevin MacLeod) en respectant la licence (crédit au générique).
- **Bruitages** : Freesound + enregistrements maison (tissu, pas, verres).
- **Droits** : si la projection est publique ou payante, toute chanson commerciale (même « votre chanson ») doit être déclarée (SACEM en France). En projection privée, demander les règles à la salle.

## 11. Préparation de la projection

- Format : **1998×1080 (Flat 1.85) ou 2048×858 (Scope 2.39), 24 images/s**. Décider dès la phase 3.
- Export master depuis Resolve (séquence TIFF ou ProRes/DNxHR), son stéréo ou 5.1 à 48 kHz.
- **DCP-o-matic** pour le DCP, livré sur disque USB (format ext2/ext3 souvent demandé par les salles).
- **Test en salle obligatoire** quelques jours avant : couleurs, volume, sous-titres.
- Beaucoup de salles acceptent aussi un simple fichier MP4/ProRes pour un événement privé : à demander.

---

## 12. Méthode de travail avec les IA gratuites

- **Une conversation Claude par phase**, en collant au début ce document et la « bible » du film, pour éviter de perdre le contexte.
- Les prompts d'images sont **préparés avant** pour ne pas gaspiller le quota ChatGPT.
- On garde un fichier « bible visuelle » avec les images de référence validées : chaque nouvelle image doit être générée à partir d'elles.
- **Confidentialité** : avant d'envoyer des photos à ChatGPT, désactiver « Améliorer le modèle pour tout le monde » dans les paramètres. Demander l'accord de Ruben pour utiliser ses photos.
