# Architecture de WallCraft Pro

WallCraft Pro est une application Windows en C# et WinUI 3. Elle compose un fond sur un bureau multi-écrans et génère une image à la résolution native de chaque moniteur.

## Composants

| Projet | Rôle |
| --- | --- |
| `csharp/src/WallCraft.App` | Fenêtre WinUI 3, édition et aperçu Win2D, décodage et export HD, automatisation et zone de notification |
| `csharp/src/WallCraft.Core` | Géométrie, algorithmes de placement, édition, projets JSON, réglages et fonds mémorisés |
| `csharp/src/WallCraft.Platform.Windows` | Détection des moniteurs et lecture EDID, intégration `IDesktopWallpaper`, identité du paquet et démarrage hors MSIX |
| `csharp/tests/WallCraft.Core.Tests` | Tests du cœur et cas de référence pour la compatibilité avec l’ancienne implémentation |

## Composition et rendu

Chaque écran possède un rectangle dans la composition. En mode pixels, ces rectangles suivent le bureau Windows. En mode Taille réelle, la géométrie utilise les dimensions physiques fournies par l’EDID ou saisies par l’utilisateur, l’espace entre les dalles et les décalages. Le rendu par écran utilise ces mêmes rectangles, puis produit une image à la résolution native de la dalle.

Le mode Ajuster conserve l’intégralité de la zone visible de chaque photo. Le mode Remplir couvre la zone de placement par recadrage autour des visages détectés ou de la région la plus détaillée. Le moteur d’optimisation explore des dispositions à l’aide d’une graine fixe. Les variantes se reproduisent pour les mêmes entrées et la recherche reste heuristique.

Win2D dessine les aperçus à partir de miniatures limitées à 1 024 pixels. L’export recharge les originaux avec leur orientation EXIF, puis applique les retouches, la rotation et le recadrage. Lorsque la composition dépasse la taille maximale d’une texture du GPU, l’export par écran et l’application du fond rendent les écrans séparément. L’export en une seule image et le repli « Étendre » utilisent une texture à l’échelle du bureau.

## Intégration Windows

`IDesktopWallpaper` associe les fichiers aux moniteurs par recouvrement de rectangles. Cela couvre les écrans empilés et les coordonnées négatives. Si l’application par écran échoue entièrement, WallCraft tente le mode « Étendre ».

WallCraft conserve un fond par configuration d’écrans. Il détecte les changements de moniteurs toutes les quatre secondes et vérifie le fond actif environ une fois par minute lorsque le maintien du fond est activé. La tâche de démarrage du paquet est désactivée par défaut. La version autonome utilise la clé `HKCU\…\Run` lorsque l’utilisateur active le démarrage automatique.

Sous MSIX, les réglages et les fonds mémorisés sont dans le dossier de données du paquet. WallCraft reprend les fichiers compatibles de l’ancienne installation. Les détails sont dans la [documentation de migration](MIGRATION_CSHARP.md).

## Distribution

Le [workflow C#](../.github/workflows/csharp.yml) publie un artefact de développement autonome pour Windows x64. Le [workflow MSIX](../.github/workflows/store.yml) construit et vérifie le paquet destiné au Microsoft Store. Les deux embarquent .NET et le Windows App SDK. Le [guide Microsoft Store](MICROSOFT_STORE.md) décrit l’identité du paquet et la soumission.
