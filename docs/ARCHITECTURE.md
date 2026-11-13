# Architecture de WallCraft Pro

## Besoin et contraintes

Composer des images pour des écrans de dimensions et de positions différentes, préserver l’intégralité des photos dans les modes de placement et appliquer le résultat au bureau Windows.

La version [C# et WinUI 3](MIGRATION_CSHARP.md) cible le Microsoft Store. La version Python, décrite dans le tableau ci-dessous, est distribuée par GitHub Releases.

| Composant | Rôle |
| --- | --- |
| `main.py` | Démarrage, gestion DPI, option `--tray` (lancement au démarrage de Windows) |
| `ui.py` | Fenêtre principale : barre d'outils sur une ligne, bibliothèque compacte, zone de travail unique (Composition / Aperçu sur les écrans), barre d'état |
| `ui_views.py` | Dessin de la zone de composition (zones hors écran assombries, alerte basse résolution) et de l'aperçu des écrans |
| `ui_automation.py` | Détection des écrans, taille réelle, fond automatique, rotation, icône de notification |
| `dialogs.py` | Fenêtres secondaires : retouches, taille réelle, variantes, fond automatique |
| `ui_text.py`, `locales.py` | Textes d'interface en 4 langues |
| `image_tools.py` | Images, filtres, dispositions automatiques (Ajuster / Remplir, variantes), projets JSON, rendu HD |
| `facefocus.py` | Point d'intérêt d'une image : visages (OpenCV), sinon zone la plus détaillée |
| `display_geometry.py` | Rectangles de composition des écrans (pixels ou taille réelle), EDID, réglages persistants |
| `screen_splitter.py` | Disposition des moniteurs, découpe, appels Windows COM / registre |
| `services.py` | Fond par configuration d'écrans, détection d'un thème remis, rotation, démarrage, icône pystray |

## Choix et compromis

**Miniatures pour l’interface, originaux pour l’export.** `LoadedImage` garde une miniature limitée à 1 024 pixels ; l’original est relu depuis le disque au moment de l’export. Les filtres et prévisualisations utilisent la miniature.

**Rectangles de composition.** Chaque écran porte une clé `canvas` (x, y, largeur, hauteur) dans l’espace de composition. En mode pixels, c’est la grille du bureau Windows. En mode taille réelle, `display_geometry` place les écrans selon leur taille en millimètres (EDID ou saisie), l’espace entre les dalles et un décalage vertical, à l’échelle de l’écran le plus dense : aucun écran n’est agrandi, la partie de l’image derrière les bordures est perdue. Interface, découpe et rendu n’utilisent que ces rectangles.

**Ajuster ou Remplir.** Ajuster place chaque image entière dans sa case (bandes noires possibles). Remplir couvre la case et recadre l’image autour de son point d’intérêt ; il n’y a jamais de déformation. Le point d’intérêt est calculé à la demande sur la miniature et enregistré dans le projet.

**Placement sans rognage.** Les modes testés placent les images dans les limites de la surface et conservent le ratio de leur zone visible, à l’arrondi pixel près ; un rognage manuel est respecté par les modes automatiques. Les espaces libres sont un compromis acceptable pour éviter de couper les photos. Ne pas confondre cette propriété avec un remplissage garanti de tout l’écran.

**Recherche heuristique reproductible.** Le mode optimal explore des arbres de découpage avec un nombre d’essais fixe et une graine dérivée des images et de l’écran : le résultat ne dépend ni de la machine ni du hasard. Les variantes sont les k meilleurs arbres distincts. Le score multiplie le remplissage par l’équilibre des tailles (rapport plus petite / plus grande image, à la puissance 0,15) pour éviter les images minuscules. Ce n’est pas une preuve d’optimum global ; un benchmark reproductible serait nécessaire avant d’annoncer des gains chiffrés.

**Fond automatique.** Après chaque application réussie, les images par écran et un manifeste sont rangés dans `%LOCALAPPDATA%\WallCraft\configs\<empreinte>` (une empreinte par ensemble d’écrans branchés). Toutes les 4 s, l’application vérifie si les écrans ont changé ; toutes les 60 s, si Windows affiche encore ces fichiers. Dans les deux cas elle réapplique les images mémorisées, sans nouveau rendu. L’icône de notification (pystray) tourne dans son propre thread et transmet les clics par une file d’attente au thread Tk.

**Intégration Windows localisée.** Les appels COM et registre restent dans `screen_splitter.py`, `display_geometry.py` (EDID) et `services.py` (démarrage). Les tests géométriques fonctionnent indépendamment de cette intégration ; ils ne valident pas l’application réelle du papier peint.

## Distribution

Le workflow `release.yml` publie l’exécutable Python et son empreinte SHA-256. Le workflow `store.yml` construit et vérifie le MSIX C# x64. Le paquet destiné à Partner Center est produit avec l’identité de l’éditeur et Microsoft le signe après certification. [Procédure Store](MICROSOFT_STORE.md)

## Intégration Windows

`IDesktopWallpaper` reçoit une image par écran. L'appariement se fait par recouvrement de rectangles (`match_monitors`) et non par rang de gauche à droite, ce qui gère les écrans empilés et les coordonnées négatives ; les écrans dont `GetMonitorRECT` échoue (inactifs) sont ignorés. Les mesures passent temporairement en DPI Per-Monitor V2 pour rester justes avec des écrans à mises à l'échelle différentes. Si l'appel COM échoue entièrement, l'image complète est appliquée en mode « Étendre ». Les fichiers appliqués sont écrits dans `%LOCALAPPDATA%\WallCraft\wallpapers`, que Windows relit au démarrage.

## Mémoire

Seule la miniature (1 024 px) reste en mémoire ; l'original est relu depuis le disque au moment de l'export. L'orientation EXIF est appliquée à chaque lecture.

## Évolutions utiles

Extraire les algorithmes de placement de `image_tools.py` si leur évolution devient indépendante des opérations d’image ; mesurer temps de calcul et mémoire sur des jeux représentatifs ; définir les versions de schéma avant toute évolution incompatible des projets JSON.

## Ergonomie de la fenêtre principale

- Une seule zone de travail : on bascule entre **Composition** (édition) et **Aperçu sur les écrans** au lieu d'empiler deux petites vues.
- Les écrans portent un nom lisible (`monitor_labels` : position + fabricant EDID + diagonale), jamais `\\.\DISPLAYn`.
- `upscale_factor` mesure l'agrandissement d'une image ; au-delà de ×1,3 une alerte apparaît dans la liste, sur l'image et dans la barre d'état.
- À fort zoom, seule la partie visible d'une image est rendue, et une seule taille est gardée en cache par image.
- La largeur minimale de la fenêtre suit la barre d'outils, qui dépend de la langue.
