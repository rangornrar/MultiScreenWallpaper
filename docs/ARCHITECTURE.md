# Architecture de WallCraft Pro

## Besoin et contraintes

Composer des images pour des écrans de dimensions et de positions différentes, préserver l’intégralité des photos dans les modes de placement et appliquer le résultat au bureau Windows.

| Composant | Rôle |
| --- | --- |
| `main.py` | Démarrage et gestion DPI |
| `ui.py` | Interface Tkinter et orchestration |
| `image_tools.py` | Images, filtres, géométrie, placement et sauvegarde JSON |
| `screen_splitter.py` | Disposition des moniteurs et appels Windows COM / registre |
| `locales.py` | Textes d’interface |

## Choix et compromis

**Miniatures pour l’interface, originaux pour l’export.** `LoadedImage` conserve une image originale et une miniature limitée à 1 024 pixels. Les filtres et prévisualisations utilisent la miniature ; l’export reprend l’original. Cela réduit le travail d’affichage mais conserve un coût mémoire proportionnel aux originaux chargés. Le cache de prévisualisation est invalidé lors des transformations prévues.

**Placement sans rognage.** Les modes testés placent les images dans les limites de la surface et conservent le ratio de leur zone visible, à l’arrondi pixel près ; un rognage manuel est respecté par les modes automatiques. Les espaces libres sont un compromis acceptable pour éviter de couper les photos. Ne pas confondre cette propriété avec un remplissage garanti de tout l’écran.

**Recherche heuristique bornée.** Le mode optimal explore des arbres de découpage pendant environ 0,85 seconde. Son score multiplie le remplissage par l’équilibre des tailles (rapport plus petite / plus grande image, à la puissance 0,15) pour éviter les images minuscules. La qualité dépend des images, de l’aléatoire et de la machine. Ce n’est pas une preuve d’optimum global ; un benchmark reproductible serait nécessaire avant d’annoncer des gains chiffrés.

**Intégration Windows localisée.** Les appels COM et registre restent dans `screen_splitter.py`. Les tests géométriques fonctionnent indépendamment de cette intégration ; ils ne valident pas l’application réelle du papier peint.

## Distribution

Les exécutables ne sont plus suivis dans Git. Le workflow `release.yml` construit l'exe Windows depuis le code d'un tag et le publie en GitHub Release avec son empreinte SHA-256 ; le site pointe vers `releases/latest`. L'historique n'est pas réécrit : les anciens binaires restent accessibles dans les commits passés.

## Intégration Windows

`IDesktopWallpaper` reçoit une image par écran. L'appariement se fait par recouvrement de rectangles (`match_monitors`) et non par rang de gauche à droite, ce qui gère les écrans empilés et les coordonnées négatives ; les écrans dont `GetMonitorRECT` échoue (inactifs) sont ignorés. Les mesures passent temporairement en DPI Per-Monitor V2 pour rester justes avec des écrans à mises à l'échelle différentes. Si l'appel COM échoue entièrement, l'image complète est appliquée en mode « Étendre ». Les fichiers appliqués sont écrits dans `%LOCALAPPDATA%\WallCraft\wallpapers`, que Windows relit au démarrage.

## Mémoire

Seule la miniature (1 024 px) reste en mémoire ; l'original est relu depuis le disque au moment de l'export. L'orientation EXIF est appliquée à chaque lecture.

## Évolutions utiles

Extraire les algorithmes de placement de `image_tools.py` si leur évolution devient indépendante des opérations d’image ; mesurer temps de calcul et mémoire sur des jeux représentatifs ; définir les versions de schéma avant toute évolution incompatible des projets JSON.
