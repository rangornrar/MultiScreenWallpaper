[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D21VSKW5)

# 🎨 WallCraft Pro - Multi-Monitor Wallpaper Generator

🌍 **[English](README_en.md)** | **[Français](README.md)** | **[Español](README_es.md)** | **[Deutsch](README_de.md)**

**WallCraft Pro** est une application Python conçue pour créer, organiser et appliquer des fonds d'écran sur des configurations multi-écrans complexes.

Elle résout le problème des résolutions et des bordures de moniteurs disparates grâce à son moteur de placement : elle permet de fusionner de multiples photos sans **jamais les déformer ni les rogner**, en conservant l’intégralité de chaque image dans les modes de placement décrits ("Fit Inside").

![WallCraft Interface](assets/wallcraft_app_ui_1773221294829.png)

---

## 🚀 Fonctionnalités Clés

### 🖥️ Gestion Multi-Écrans Avancée
- **Détection automatique** de la disposition physique de vos écrans (gauche/droite, hauteur).
- **Application native** : Applique un fond d'écran différent par moniteur (via l'API Windows `IDesktopWallpaper`).
- **Mode Secours** : Bascule en mode "Panorama" (Span) si l'API n'est pas supportée.

### 📐 Le Moteur de Visibilité Absolue (Fit Inside)
Le programme garantit la règle du 100% :
- **0 Rognage (Crop)** : les modes automatiques ne coupent jamais les bords d'une image ; le rognage reste un choix manuel (mode *Rogner*).
- **0 Superposition** : Aucune photo ne couvre une autre photo.
- **0 Dépassement** : Les images ne déborderont jamais de l'écran.
- **0 Déformation** : Le ratio original est mathématiquement préservé.

### 🧩 6 Algorithmes d'Organisation (Auto-Layout)
- ⭐ **Optimisation Maximale (Lent)** : Recherche heuristique bornée à environ 0,85 seconde, utilisant des arbres de découpage binaires. Elle cherche à réduire les espaces libres ; le résultat dépend des images et ne garantit pas un optimum global.
- **Mosaïque Parfaite** : Un arrangement aléatoire de type patchwork (technique BSP).
- **Lignes Justifiées** : Alignement type Flickr/Google Images.
- **Grille Régulière** : Quadrillage mathématique et étendu.
- **Bandes Verticales** et **Bandes Horizontales** : Découpage panoramique pleine hauteur ou largeur.

![Optimisation Maximale Heuristique](assets/wallcraft_optimal_layout_1773221310533.png)

### ⚡ Performance & Édition
- **Système de Proxy** : Utilise des miniatures pour une interface plus réactive grâce à des miniatures de 1 024 pixels maximum.
- **Retouche Intégrée** : Luminosité, Contraste, Saturation, Flou et Rotation.
- **Rendu HD** : L'export final utilise les fichiers Ultra HD originaux pour préserver la résolution disponible.

---

## 📦 Installation

### Prérequis
- Python 3.10 ou supérieur.
- Windows 10/11 (requis en raison de l'API de fond d'écran).

### Dépendances
```bash
python -m pip install -r requirements.txt
```

## 📥 Télécharger
L'exécutable Windows est publié sur la page [GitHub Releases](https://github.com/rangornrar/MultiScreenWallpaper/releases/latest). Son empreinte SHA-256 figure dans les notes de chaque version.

## 🛠️ Utilisation
1. Lancer l'application : `python main.py` (ou l'exécutable de la [dernière release](https://github.com/rangornrar/MultiScreenWallpaper/releases/latest)).
2. **Ajouter des images** : bouton « + Ajouter des images » ou menu *Fichier*. Les photos de smartphone sont automatiquement remises dans le bon sens.
3. **Langue** : choisissez EN/FR/ES/DE directement depuis l'interface.
4. **Choisir une disposition** : sélectionnez l'un des 6 modes (« Optimisation Maximale » recommandé pour limiter les bandes noires).
5. **Auto-Organiser**, puis ajustez à la main : modes *Déplacer*, *Redimensionner* et *Rogner*, calques avant/arrière, *Pivoter 90°* et *Retouches…* (luminosité, contraste, saturation, flou).
6. **Menu Fichier** :
    * Enregistrer / ouvrir un projet (`Ctrl+S` / `Ctrl+O`).
    * Exporter l'image complète (`Ctrl+E`) ou une image par écran.
    * 🖥️ Appliquer en fond : modifie votre bureau Windows, écran par écran.

## 📂 Structure du Projet
* `main.py` : Point d'entrée, gestion High-DPI Windows.
* `ui.py` : Fenêtre, canevas interactif, menus et interactions souris.
* `locales.py` : Registre multilingue des chaînes de caractères.
* `image_tools.py` : Le Cœur logique. Manipulation d'images (Crop/Fit) et moteurs de layout (`AutoLayoutStrategy`).
* `screen_splitter.py` : Appels système ctypes pour l'injection native sur Windows.

## 🐛 Dépannage
* **L'application est floue ?** Lancez via le terminal Windows classique (cmd/powershell) plutôt que via l'IDE pour assurer la gestion High-DPI de Windows.
* **Bandes noires visibles ?** C'est le comportement attendu. L'application refusant tout rognage par conception, les espaces non remplis des boîtes géométriques affichent une bande noire pour conserver l'image 100% visible. L'option "Optimisation Maximale" permet justement de compresser cela.

## 📄 Licence
Distribué sous licence [MIT](LICENSE).

## Architecture & validation

[Architecture and trade-offs](docs/ARCHITECTURE.md) · [Quality and test scope](docs/QUALITY.md).
