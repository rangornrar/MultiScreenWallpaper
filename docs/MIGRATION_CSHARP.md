# Migration de WallCraft Pro vers C# / WinUI 3

WallCraft Pro est porté de Python/Tkinter vers C# et WinUI 3. GitHub Releases distribue l’exécutable Python. Le workflow MSIX produit le paquet C# x64 destiné au Microsoft Store. La [procédure Store](MICROSOFT_STORE.md) décrit la recette et la soumission.

## 1. Objectifs

- **Interface Windows 11 native** : effet Mica, barre de titre et menus sombres, coins arrondis, icônes Fluent, mise à l'échelle parfaite sur chaque écran (DPI par écran).
- **Mêmes résultats qu'aujourd'hui** : pour les mêmes images, le même écran et le même numéro de variante, la version C# produit exactement la même disposition que la version Python.
- **Compatibilité des données**. Les deux versions lisent le même format de projet. Le MSIX reprend les réglages au premier lancement et importe les fonds Python à mesure que leurs configurations d’écrans sont utilisées.
- **Distribution autonome**. Le workflow C# produit un exécutable de développement et le workflow Store produit un MSIX que Microsoft signe après certification.

Le portage cible Windows. Les tests du cœur tournent également sous Linux.

## 2. Choix techniques

| Sujet | Choix | Pourquoi |
|---|---|---|
| Runtime | **.NET 10** (LTS) | Support long, performances, AOT possible plus tard |
| Interface | **WinUI 3**, Windows App SDK 2.6.5 | Intégration Windows et compilation autonome, avec ou sans MSIX |
| Architecture UI | MVVM avec **CommunityToolkit.Mvvm** | Vues XAML fines, logique testable |
| Zone de composition | **Win2D** (`CanvasControl`) | Rendu GPU : zoom et glisser fluides même avec de grandes images |
| Rendu HD et enregistrement | Win2D (`CanvasRenderTarget`) | Rendu direct par écran quand la composition dépasse la taille maximale d’une texture |
| Détection de visages | **`Windows.Media.FaceAnalysis.FaceDetector`** (intégré à Windows) | Supprime OpenCV (≈ 70 Mo) ; repli sur la « zone la plus détaillée » comme aujourd'hui |
| Fond d'écran | COM `IDesktopWallpaper` via `[GeneratedComInterface]` | Interop générée à la compilation, compatible AOT |
| Taille réelle des écrans | `EnumDisplayDevicesW` + EDID dans le registre | Portage direct de `display_geometry.py` |
| Zone de notification | **H.NotifyIcon.WinUI** (MIT) | Icône, menu, double-clic, en WinUI 3 |
| Démarrage avec Windows | `StartupTask` sous MSIX, clé `HKCU\…\Run` avec `--tray` hors paquet | Le démarrage Store est désactivé par défaut et se règle aussi dans Windows |
| Traductions | Fichiers `.resw` (en-US, fr-FR, es-ES, de-DE) | Format standard WinUI ; langue changeable sans redémarrage |

## 3. Structure de la solution

```
csharp/
  WallCraft.slnx
  src/
    WallCraft.Core/              net10.0, AUCUNE dépendance : tout ce qui se teste sans Windows
      Geometry/                  rectangles, taille réelle (mm), noms d'écrans, empreinte de configuration
      Layout/                    PythonRandom, moteur de disposition (6 modes), Ajuster/Remplir, variantes
      Model/                     image de composition (taille, rotation, rognage, point d'intérêt, filtres)
      Persistence/               projets JSON et settings.json
      Services/                  fonds mémorisés, reprise Python, suivi des fonds et rotation
    WallCraft.Platform.Windows/  COM IDesktopWallpaper, EDID, identité du paquet et démarrage hors MSIX
    WallCraft.App/               WinUI 3 : fenêtres, dialogues, zone de composition Win2D, icône de notification
  tests/
    WallCraft.Core.Tests/        tests du cœur + comparaison aux résultats de référence Python
    fixtures/                    résultats de référence produits par tools/export_golden.py
```

`WallCraft.Core` n'a volontairement aucune dépendance NuGet : il se compile et se teste partout (y compris sur Linux et dans la CI Ubuntu). Les tests utilisent un petit lanceur maison sans paquet (`dotnet run --project tests/WallCraft.Core.Tests`) ; on pourra passer à xUnit plus tard sans réécrire les tests.

## 4. Garder exactement les mêmes dispositions

La disposition « optimale » et la « mosaïque » utilisent un générateur aléatoire **à graine fixe** (`random.Random` de Python, graine = SHA-1 des images, de la taille et du numéro de variante). Pour obtenir les mêmes résultats :

1. **`PythonRandom`** : portage exact de Mersenne Twister (`init_by_array`) et des fonctions utilisées : `random()`, `getrandbits`, `randint`, `shuffle`, `choice`, `uniform`.
2. **Même graine** : reproduire la chaîne `repr((mode, tw, th, variant, [(chemin, ratio), …]))` de Python au caractère près (guillemets, échappement des `\` des chemins Windows, écriture des nombres comme `1.0` ou `0.5625`), puis `int(sha1[:12], 16)`.
3. **Mêmes calculs, dans le même ordre** : score, tri stable `(-score, essai)`, clés d'arbre distinctes.
4. **Résultats de référence** : `tools/export_golden.py` exécute le code Python sur un jeu fixe de cas et écrit les résultats en JSON ; les tests C# comparent à 0,01 px près.

Risque connu : `x ** 0.15` peut différer au dernier bit entre bibliothèques mathématiques. En cas d'égalité quasi parfaite entre deux arbres, l'ordre peut changer ; les tests le signaleront et on tranchera cas par cas.

## 5. Recette de parité sur le MSIX installé

- [ ] Import d'images (dialogue + glisser-déposer), rotation EXIF, formats JPG/PNG/WebP/BMP/TIFF
- [ ] 6 dispositions, Ajuster/Remplir, variantes, mêmes résultats que Python
- [ ] Déplacer, redimensionner, rogner, aimantation, calques, annuler/rétablir
- [ ] Retouches (luminosité, contraste, saturation, flou)
- [ ] Aperçu sur les écrans, zones hors écran assombries, alerte basse résolution
- [ ] Taille réelle des écrans (EDID, bordures, décalages), noms d'écrans lisibles
- [ ] Application par écran (`IDesktopWallpaper`), repli « Étendre », rapport d'erreurs
- [ ] Reprise des fonds Python par configuration et réapplication après branchement ou changement de thème Windows
- [ ] Choix manuel d’un autre fond dans Windows, attente d’un cycle de surveillance, puis réapplication explicite depuis l’icône
- [ ] Rotation depuis un dossier, icône de notification, fermeture de session puis lancement réel avec Windows
- [ ] Projets : ouverture des projets créés par la version Python
- [ ] Export complet et par écran sur un bureau standard, puis application et export par écran sur un bureau qui dépasse la taille maximale de texture du GPU
- [ ] 4 langues, pluriels, langue changeable à chaud
- [ ] Installation puis mise à jour du MSIX avec l’identité Partner Center et conservation des données

## 6. Diffusion

La recette associe un poste à trois écrans, dont un avec un DPI ou une orientation différente, et une VM propre. Après cette recette, la première soumission peut être distribuée à une audience privée. L’ouverture au public suit la validation de ce paquet. Le canal GitHub distribue l’exécutable Python pendant cette phase.
