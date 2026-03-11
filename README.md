[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D21VSKW5)

# 🎨 WallCraft Pro - Multi-Monitor Wallpaper Generator

🌍 **[English](README_en.md)** | **[Français](README.md)** | **[Español](README_es.md)** | **[Deutsch](README_de.md)**

**WallCraft Pro** est une application Python performante conçue pour créer, organiser et appliquer des fonds d'écran sur des configurations multi-écrans complexes. 

Elle résout le problème des résolutions et des bordures de moniteurs disparates grâce à son puissant moteur intelligent : elle permet de fusionner de multiples photos sans **jamais les déformer ni les rogner**, garantissant une **visibilité absolue à 100%** de votre image ("Fit Inside").

![WallCraft Interface](assets/wallcraft_app_ui_1773221294829.png)

---

## 🚀 Fonctionnalités Clés

### 🖥️ Gestion Multi-Écrans Avancée
- **Détection automatique** de la disposition physique de vos écrans (gauche/droite, hauteur).
- **Application native** : Applique un fond d'écran différent par moniteur (via l'API Windows `IDesktopWallpaper`).
- **Mode Secours** : Bascule en mode "Panorama" (Span) si l'API n'est pas supportée.

### 📐 Le Moteur de Visibilité Absolue (Fit Inside)
Le programme garantit la règle du 100% :
- **0 Rognage (Crop)** : Aucune image uploadée ne verra ses bords coupés.
- **0 Superposition** : Aucune photo ne couvre une autre photo.
- **0 Dépassement** : Les images ne déborderont jamais de l'écran.
- **0 Déformation** : Le ratio original est mathématiquement préservé.

### 🧩 6 Algorithmes d'Organisation (Auto-Layout)
- ⭐ **Optimisation Maximale (Lent)** : Le fleuron de l'application. Simule des centaines de milliers de variantes géométriques via un arbre de découpage binaire ("Slicing Floorplan") pour imbriquer vos images sans vide interstitiel, formant un bloc colossal qui réduit statistiquement les bandes noires à néant.
- **Mosaïque Parfaite** : Un arrangement aléatoire de type patchwork (technique BSP).
- **Lignes Justifiées** : Alignement type Flickr/Google Images.
- **Grille Régulière** : Quadrillage mathématique et étendu.
- **Bandes Verticales** et **Bandes Horizontales** : Découpage panoramique pleine hauteur ou largeur.

![Optimisation Maximale Heuristique](assets/wallcraft_optimal_layout_1773221310533.png)

### ⚡ Performance & Édition
- **Système de Proxy** : Utilise des miniatures pour une interface hyper fluide même avec des images 8K.
- **Retouche Intégrée** : Luminosité, Contraste, Saturation, Flou et Rotation.
- **Rendu HD** : L'export final utilise les fichiers Ultra HD originaux pour une qualité absolue.

---

## 📦 Installation

### Prérequis
- Python 3.8 ou supérieur.
- Windows 10/11 (requis en raison de l'API de fond d'écran).

### Dépendances
```bash
pip install pillow screeninfo
```

## 🛠️ Utilisation
1. Lancer l'application : `python main.py`
2. **Ajouter des images** : Cliquez sur le bouton ou glissez des fichiers.
3. **Menu Langue** : Choisissez EN/FR/ES/DE directement depuis l'interface.
4. **Choisir un Layout** : Sélectionnez l'un des 6 modes ("Optimisation Maximale" recommandé pour limiter les bandes noires).
5. **Auto-Organiser** : Appuyez sur le bouton "🎲" et laissez le moteur mathématique faire le reste.
6. **Appliquer** :
    * 💾 Export : Sauvegarde une grande maquette.
    * ✂ Split : Divise la composition en images respectant les écrans physiques.
    * 🖥️ Appliquer : Modifie activement votre bureau Windows.

## 📂 Structure du Projet
* `main.py` : Point d'entrée, gestion High-DPI Windows.
* `ui.py` : Fenêtre, canevas interactif, menus et interactions souris.
* `locales.py` : Registre multilingue des chaînes de caractères.
* `image_tools.py` : Le Cœur logique. Manipulation d'images (Crop/Fit) et moteurs de layout (`AutoLayoutStrategy`).
* `screen_splitter.py` : Appels système ctypes pour l'injection native sur Windows.

## 🐛 Dépannage
* **L'application est floue ?** Lancez via le terminal Windows classique (cmd/powershell) plutôt que via l'IDE pour assurer la gestion High-DPI de Windows.
* **Bandes noires visibles ?** C'est le comportement attendu. L'application refusant tout rognage par conception, les espaces non remplis des boîtes géométriques affichent une bande noire pour conserver l'image 100% visible. L'option "Optimisation Maximale" permet justement de compresser cela.