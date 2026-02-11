# 🎨 WallCraft Pro - Multi-Monitor Wallpaper Generator

**WallCraft Pro** est une application Python performante conçue pour créer, organiser et appliquer des fonds d'écran sur des configurations multi-écrans complexes. 

Elle résout le problème des résolutions différentes et des bordures d'écrans en permettant de positionner précisément des images ou de générer des mosaïques intelligentes (Grilles, Maçonnerie, Style Lapis Lazuli) sans déformer vos photos.

---

## 🚀 Fonctionnalités Clés

### 🖥️ Gestion Multi-Écrans Avancée
- **Détection automatique** de la disposition physique de vos écrans (gauche/droite, hauteur).
- **Application native** : Applique un fond d'écran différent par moniteur (via l'API Windows `IDesktopWallpaper`).
- **Mode Secours** : Bascule automatiquement en mode "Panorama" (Span) si l'API multi-écran n'est pas supportée.

### 📐 Algorithmes de Mise en Page (Auto-Layout)
- **Grid (Cover)** : Grille classique remplissant les cases.
- **Masonry** : Colonnes type Pinterest.
- **Smart BSP** : Partitionnement binaire de l'espace (optimisation de la surface).
- **Justified (No Crop)** : Alignement type Flickr/Google Photos. Respecte 100% du ratio de l'image (pas de rognage).
- **Lapis Lazuli (Weighted)** : Mosaïque aléatoire organique ("Opus Incertum"). Mélange tailles variées et placement intelligent pour minimiser les vides.

### ⚡ Performance & Édition
- **Système de Proxy** : Utilise des miniatures pour une interface fluide (60fps) même avec des images 8K.
- **Rendu HD** : L'export final utilise les fichiers originaux pour une qualité maximale.
- **Retouche** : Luminosité, Contraste, Saturation, Flou et Rotation par image.
- **Drag & Drop** : Déplacement, Zoom (Molette) et Panoramique (Clic molette).

---

## 📦 Installation

### Prérequis
- Python 3.8 ou supérieur.
- Windows 10 ou 11 (pour l'API de fond d'écran).

### Dépendances
Installez les bibliothèques nécessaires via pip :

```bash
pip install pillow screeninfo
```
(Note : L'application utilise ctypes et winreg (natifs) pour communiquer avec Windows, donc pas besoin de pywin32 ou comtypes lourds).

## 🛠️ Utilisation
1. Lancer l'application :

```Bash
python main.py
```
2. Importer des images : Cliquez sur + Ajouter ou glissez des fichiers.

3. Choisir un Layout :

    * Sélectionnez un mode (ex: lapis, justified) dans la liste déroulante.
    * Cliquez sur Auto.

4. Ajuster :

    * Cliquez sur une image pour la sélectionner.
    * Utilisez les curseurs (Luminosité, Flou...) en haut.
    * Déplacez-la à la souris.

5. Appliquer :

    * 💾 Export : Sauvegarde une image PNG géante.
    * ✂ Split : Sauvegarde une image par écran dans un dossier.
    * 🖥️ Appliquer : Change immédiatement votre fond d'écran Windows.

## 📂 Structure du Projet
* main.py : Point d'entrée. Configure la fenêtre et la gestion High-DPI pour éviter le flou.
* ui.py : Gestion de l'interface graphique (Tkinter), des événements souris et des panneaux de contrôle.
* image_tools.py : Cœur logique. Contient la classe LoadedImage (gestion proxy/HD) et tous les algorithmes mathématiques de mise en page (AutoLayoutStrategy).
* screen_splitter.py : Interface bas niveau avec Windows. Gère la détection des écrans, le découpage des images et l'injection du wallpaper via les appels système ctypes.

## 🏗️ Compiler en .EXE (Optionnel)
Pour créer un exécutable autonome à partager ou à placer sur le bureau :

1. Installez PyInstaller :

```Bash
pip install pyinstaller
```
2. Lancez la compilation :

```Bash
pyinstaller --noconsole --onefile --name="WallCraft" main.py
```
3. L'exécutable sera dans le dossier dist/.



## 🐛 Dépannage fréquent
* L'application est floue ? Le script main.py force le mode "DPI Aware". Assurez-vous de lancer via python main.py et non via un IDE qui pourrait brider l'affichage.

* Les écrans sont dans le mauvais ordre ? L'algorithme trie les écrans par leur position physique (coordonnée X) de gauche à droite, et non par leur numéro Windows (1, 2, 3). Assurez-vous que vos écrans sont bien disposés dans les "Paramètres d'affichage" de Windows.

* Bandes noires en mode "Lapis" ou "Justified" ? C'est normal. Ces modes sont conçus pour ne jamais rogner une photo. Si la somme des photos ne correspond pas exactement au ratio de l'écran, des bandes noires sont ajoutées pour combler le vide ("Fit Inside").