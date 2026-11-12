# Migration de WallCraft Pro vers C# / WinUI 3

Plan de migration de la version Python (Tkinter) vers une application Windows native en C#.
La version Python reste la version publiée jusqu'à ce que la version C# fasse tout ce qu'elle fait.

## 1. Objectifs

- **Interface Windows 11 native** : effet Mica, barre de titre et menus sombres, coins arrondis, icônes Fluent, mise à l'échelle parfaite sur chaque écran (DPI par écran).
- **Mêmes résultats qu'aujourd'hui** : pour les mêmes images, le même écran et le même numéro de variante, la version C# produit exactement la même disposition que la version Python.
- **Compatibilité des données** : les projets enregistrés, les réglages (`settings.json`) et les fonds mémorisés par configuration d'écrans (`%LOCALAPPDATA%\WallCraft\configs\…`) restent lisibles par les deux versions.
- **Un exe autonome**, sans installation de .NET ni du Windows App SDK, signé SHA-256 par le workflow de release comme aujourd'hui.

Hors périmètre de la première version : macOS/Linux, Microsoft Store, nouvelles fonctions.

## 2. Choix techniques

| Sujet | Choix | Pourquoi |
|---|---|---|
| Runtime | **.NET 10** (LTS) | Support long, performances, AOT possible plus tard |
| Interface | **WinUI 3** (Windows App SDK), application **non empaquetée**, autonome | Le seul moyen d'avoir le rendu Windows 11 natif ; pas de Store, un simple exe |
| Architecture UI | MVVM avec **CommunityToolkit.Mvvm** | Vues XAML fines, logique testable |
| Zone de composition | **Win2D** (`CanvasControl`) | Rendu GPU : zoom et glisser fluides même avec de grandes images |
| Rendu HD et enregistrement | Win2D (`CanvasRenderTarget`) → PNG | Même pipeline que l'affichage, sans dépendance supplémentaire |
| Détection de visages | **`Windows.Media.FaceAnalysis.FaceDetector`** (intégré à Windows) | Supprime OpenCV (≈ 70 Mo) ; repli sur la « zone la plus détaillée » comme aujourd'hui |
| Fond d'écran | COM `IDesktopWallpaper` via `[GeneratedComInterface]` | Interop générée à la compilation, compatible AOT |
| Taille réelle des écrans | `EnumDisplayDevicesW` + EDID dans le registre | Portage direct de `display_geometry.py` |
| Zone de notification | **H.NotifyIcon.WinUI** (MIT) | Icône, menu, double-clic, en WinUI 3 |
| Démarrage avec Windows | `HKCU\…\Run` avec `--tray` | Identique à la version Python |
| Traductions | Fichiers `.resw` (en-US, fr-FR, es-ES, de-DE) | Format standard WinUI ; langue changeable sans redémarrage |

## 3. Structure de la solution

```
csharp/
  WallCraft.sln
  src/
    WallCraft.Core/              net10.0, AUCUNE dépendance : tout ce qui se teste sans Windows
      Geometry/                  rectangles, taille réelle (mm), noms d'écrans, empreinte de configuration
      Layout/                    PythonRandom, moteur de disposition (6 modes), Ajuster/Remplir, variantes
      Model/                     image de composition (taille, rotation, rognage, point d'intérêt, filtres)
      Persistence/               projets JSON, settings.json, ConfigStore et manifest.json
      Services/                  logique « thème ou choix de l'utilisateur », rotation d'images
    WallCraft.Platform.Windows/  net10.0-windows : COM IDesktopWallpaper, EDID, surveillance des écrans,
                                 démarrage auto, détection de visages, rendu HD
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

## 5. Phases, modèle et effort

| # | Phase | Qui | Modèle · effort | Dépend de |
|---|---|---|---|---|
| 0 | Plan + squelette de la solution | conversation principale | Opus 5.5 · high | — |
| 1 | Résultats de référence Python (`tools/export_golden.py`, `tests/fixtures/`) | agent | Sonnet 5.5 · medium | 0 |
| 2 | Traductions → `.resw` (4 langues) + script de vérification des clés | agent | Sonnet 5.5 · medium | 0 |
| 3 | CI GitHub Actions .NET (cœur sur Ubuntu, application sur Windows, exe en artefact) | agent | Sonnet 5.5 · medium | 0 |
| 4 | Cœur : `PythonRandom`, moteur de disposition, géométrie, projets, ConfigStore | conversation principale | Opus 5.5 · high | 1 |
| 5 | Plateforme Windows : fond d'écran COM, EDID, surveillance des écrans, visages, rendu HD | conversation principale | Opus 5.5 · high | 3, 4 |
| 6 | Interface WinUI 3 : fenêtre principale, zone de composition, dialogues (un agent par écran) | agents | Opus 5.5 · medium | 2, 4, 5 |
| 7 | Icône de notification, démarrage auto, release (exe autonome + SHA-256), site | agent | Sonnet 5.5 · medium | 6 |
| 8 | Recette sur le PC à 3 écrans, comparaison avec la version Python, bascule | conversation principale + Patrick | Opus 5.5 · high | 7 |

Chaque phase livre une PR. Les phases 1, 2 et 3 tournent en parallèle dès que le squelette existe. Le code des agents est relu dans la conversation principale avant fusion.

## 6. Liste de parité (à cocher avant de publier la version C#)

- [ ] Import d'images (dialogue + glisser-déposer), rotation EXIF, formats JPG/PNG/WebP/BMP/TIFF
- [ ] 6 dispositions, Ajuster/Remplir, variantes, mêmes résultats que Python
- [ ] Déplacer, redimensionner, rogner, aimantation, calques, annuler/rétablir
- [ ] Retouches (luminosité, contraste, saturation, flou)
- [ ] Aperçu sur les écrans, zones hors écran assombries, alerte basse résolution
- [ ] Taille réelle des écrans (EDID, bordures, décalages), noms d'écrans lisibles
- [ ] Application par écran (`IDesktopWallpaper`), repli « Étendre », rapport d'erreurs
- [ ] Un fond par configuration d'écrans, réapplication au branchement et après un thème Windows, jamais par-dessus un choix de l'utilisateur
- [ ] Rotation depuis un dossier, icône de notification, démarrage avec Windows
- [ ] Projets : ouverture des projets créés par la version Python
- [ ] Export de l'image complète et par écran
- [ ] 4 langues, pluriels, langue changeable à chaud
- [ ] Exe autonome, release GitHub avec SHA-256, site mis à jour

## 7. Bascule

1. Les deux versions coexistent ; la version C# est publiée en « préversion » sur GitHub.
2. Recette sur le poste à 3 écrans (phase 8) avec les mêmes projets dans les deux versions.
3. Quand la liste de parité est complète : la version C# devient la version principale, le code Python est conservé dans un dossier `legacy/` le temps d'une version, puis retiré.
