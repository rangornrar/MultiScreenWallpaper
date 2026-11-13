# Publier WallCraft Pro sur le Microsoft Store

C'est la **version C# (WinUI 3)** qui est publiée sur le Store, sous forme de **paquet MSIX** :

- le Store **signe le paquet lui-même**, il n'y a pas de certificat à acheter ;
- le Store héberge le paquet et installe les mises à jour ;
- l'exe de GitHub (version Python) reste disponible à côté.

**Avant la première soumission** : tester la version C# sur un vrai PC à plusieurs écrans et cocher la liste de parité de `MIGRATION_CSHARP.md`. Une application qui plante à l'ouverture est refusée à la certification.

## Ce qui est déjà prêt dans le dépôt

| Élément | Où |
|---|---|
| Manifeste du paquet | `csharp/src/WallCraft.App/Package.appxmanifest` |
| Icônes du paquet | `csharp/src/WallCraft.App/Images/` (générées par `tools/make_msix_assets.py`) |
| Construction du paquet | workflow **Microsoft Store (MSIX)** (`.github/workflows/store.yml`) |
| Vérification automatique | Le workflow installe le paquet sur un PC Windows de GitHub et vérifie : le dossier de données, le fond d'écran, la tâche de démarrage et l'ouverture de la fenêtre. |
| Politique de confidentialité | https://wallcraft.archi-it.fr/fr/privacy/ (et `/en/privacy/`, `/es/privacy/`, `/de/privacy/`), en ligne après l'envoi du site |
| Logo carré 300 × 300 | `docs/store/logo-300.png` |
| Captures pour la fiche | **à faire** sur votre PC une fois la version C# validée : 4 par langue, PNG, 1366 × 768 au minimum (Win + Maj + S) |

Ce qui change dans un paquet, et que l'application gère :

- **Fonds d'écran** (`AppPaths`) : ils sont enregistrés dans le dossier réel du paquet, pour que Windows les affiche.
- **Lancement au démarrage** (`StoreStartup`) : il passe par la tâche de démarrage du paquet. L'utilisateur la retrouve aussi dans Paramètres > Applications > Démarrage, et WallCraft s'ouvre alors directement dans la zone de notification.
- **Réglages** : ceux de l'exe GitHub sont repris au premier lancement.

## Étapes (une seule fois)

1. **Créer le compte développeur** (gratuit pour un particulier) : https://aka.ms/storedeveloper
   - Connectez-vous avec votre compte Microsoft personnel.
   - La vérification d'identité se fait avec une pièce d'identité et un selfie.
   - Le **nom d'éditeur** choisi ici apparaîtra sous l'application dans le Store.
2. **Réserver le nom** : dans Partner Center, choisissez Applications et jeux > Nouveau produit > Application MSIX ou PWA, puis entrez « WallCraft Pro ».
3. **Recopier l'identité du produit** : dans WallCraft Pro, ouvrez Gestion des produits > Identité du produit, puis créez trois variables dans GitHub (dépôt > Settings > Secrets and variables > Actions > Variables) :

   | Variable GitHub | Valeur à recopier depuis Partner Center |
   |---|---|
   | `MSIX_IDENTITY_NAME` | `Package/Identity/Name` (ex. `12345Rangorn.WallCraftPro`) |
   | `MSIX_PUBLISHER` | `Package/Identity/Publisher` (ex. `CN=1A2B3C4D-…`) |
   | `MSIX_PUBLISHER_DISPLAY_NAME` | `Package/Properties/PublisherDisplayName` |

   Ces valeurs ne sont pas secrètes.
4. **Construire le paquet** : dans Actions > Microsoft Store (MSIX) > Run workflow, entrez la version (ex. `2026.11.13`).
   - Une fois le workflow terminé, téléchargez l'artefact `wallcraft-store-msix` et dézippez-le pour obtenir `WallCraft-Pro-v2026.11.13-Store.msix`.
   - Pour les versions suivantes, il est construit automatiquement à chaque tag `Tag_v…`.
5. **Créer la soumission** dans Partner Center, section par section :
   - **Tarification et disponibilité** : Gratuit, tous les marchés, visibilité publique.
   - **Propriétés** :
     - Catégorie *Personnalisation*, sous-catégorie *Fonds d'écran et écrans de verrouillage*.
     - Politique de confidentialité : https://wallcraft.archi-it.fr/en/privacy/
     - Site web : https://wallcraft.archi-it.fr/
     - Contact support : https://github.com/rangornrar/MultiScreenWallpaper/issues
   - **Classification par âge** : remplissez le questionnaire en répondant « non » partout ; le résultat attendu est 3+ ou PEGI 3.
   - **Paquets** : déposez le fichier `.msix`.
   - **Fiches du Store** : ajoutez les 4 langues (fr-FR, en-US, es-ES, de-DE), puis copiez les textes ci-dessous et ajoutez les captures de la langue.
   - **Options de soumission** :
     - Collez la justification de `runFullTrust` et les notes pour la certification (ci-dessous).
6. **Envoyer à la certification** : il faut compter de quelques heures à 3 jours ouvrés.

## Justification de la capacité restreinte `runFullTrust`

> WallCraft Pro is a WinUI 3 desktop application (.NET) packaged with MSIX. It needs full trust to set a different wallpaper on each monitor through the IDesktopWallpaper COM interface, to read the physical size of each monitor (EDID in the registry) and to show a notification-area icon. It makes no network connections and collects no data.

## Notes pour la certification

> No account or sign-in is needed. To test: click "Add images" and pick two or more pictures, choose a layout, then click "Apply wallpaper": each monitor receives its own part of the composition. The app works with one monitor too. "Start with Windows" (menu Screens > Automatic wallpaper…, or the notification-area icon) uses the package startup task; it is off by default.

## Textes de la fiche

Mots-clés (7 au maximum) : wallpaper, multi-monitor, dual monitor, triple monitor, ultrawide, background, desktop.

### Français (fr-FR)

**Description courte**
Composez un fond d'écran pour plusieurs écrans, même de tailles et de résolutions différentes, sans déformation ni image coupée.

**Description**
WallCraft Pro compose et applique des fonds d'écran sur les bureaux multi-écrans : double, triple, écran vertical, ultrawide, écrans de tailles différentes.

Ajoutez vos images, choisissez une disposition, et WallCraft les place sur l'ensemble de vos écrans. Chaque écran reçoit exactement sa partie, à sa résolution.

- Six dispositions, dont une optimisation qui essaie des milliers d'arrangements.
- Ajuster (images entières) ou Remplir (recadrage automatique autour des visages).
- Quatre variantes par disposition, toujours identiques pour les mêmes images.
- Taille réelle des écrans : une ligne d'horizon reste droite entre un 27 et un 24 pouces, espace entre les dalles compris.
- Retouches à la souris : déplacer, redimensionner, rogner, calques, luminosité, contraste, saturation, flou.
- Aperçu sur les écrans avant d'appliquer.
- Fond automatique : WallCraft réapplique votre fond quand les écrans changent et peut faire tourner les images d'un dossier.

Tout se passe sur votre PC : aucun compte, aucune publicité, aucune donnée collectée.

**Fonctionnalités** (une par ligne dans Partner Center)
- Un fond d'écran par écran, à la résolution de chaque écran
- Six dispositions automatiques, dont une optimisation maximale
- Ajuster ou Remplir avec recadrage autour des visages
- Prise en compte de la taille réelle des écrans
- Déplacer, redimensionner, rogner et retoucher à la souris
- Aperçu sur les écrans avant d'appliquer
- Fond réappliqué automatiquement quand les écrans changent
- Rotation automatique des images d'un dossier
- Interface en français, anglais, espagnol et allemand

### English (en-US)

**Short description**
Compose one wallpaper across several monitors, even with different sizes and resolutions, without stretching or cut-off images.

**Description**
WallCraft Pro composes and applies wallpapers for multi-monitor desks: dual, triple, vertical, ultrawide and mixed-size screens.

Add your images, pick a layout, and WallCraft arranges them across all your monitors. Each monitor gets exactly its own part, at its own resolution.

- Six layouts, including an optimizer that tries thousands of arrangements.
- Fit (whole images) or Fill (automatic cropping around faces).
- Four variants per layout, always the same for the same images.
- Real screen size: a horizon stays straight between a 27-inch and a 24-inch monitor, bezel gap included.
- Mouse editing: move, resize, crop, layers, brightness, contrast, saturation, blur.
- Preview on your monitors before applying.
- Automatic wallpaper: WallCraft re-applies your wallpaper when monitors change and can rotate the images of a folder.

Everything happens on your PC: no account, no ads, no data collected.

**Features**
- One wallpaper per monitor, at each monitor's resolution
- Six automatic layouts, including maximum optimization
- Fit or Fill with face-aware cropping
- Real physical screen size support
- Move, resize, crop and edit with the mouse
- Preview on your monitors before applying
- Wallpaper re-applied automatically when monitors change
- Automatic rotation of the images in a folder
- English, French, Spanish and German interface

### Español (es-ES)

**Descripción corta**
Componga un fondo de pantalla para varios monitores, incluso de tamaños y resoluciones distintos, sin deformar ni cortar las imágenes.

**Descripción**
WallCraft Pro compone y aplica fondos de pantalla en escritorios con varios monitores: doble, triple, vertical, ultrawide y pantallas de distinto tamaño.

Añada sus imágenes, elija una disposición y WallCraft las coloca en todas sus pantallas. Cada monitor recibe exactamente su parte, con su resolución.

- Seis disposiciones, entre ellas una optimización que prueba miles de combinaciones.
- Ajustar (imágenes completas) o Rellenar (recorte automático alrededor de las caras).
- Cuatro variantes por disposición, siempre iguales para las mismas imágenes.
- Tamaño real de las pantallas: el horizonte queda recto entre un monitor de 27 y uno de 24 pulgadas, incluido el marco.
- Edición con el ratón: mover, redimensionar, recortar, capas, brillo, contraste, saturación, desenfoque.
- Vista previa en las pantallas antes de aplicar.
- Fondo automático: WallCraft vuelve a aplicar el fondo cuando cambian las pantallas y puede rotar las imágenes de una carpeta.

Todo ocurre en su PC: sin cuenta, sin publicidad, sin recopilación de datos.

**Características**
- Un fondo por monitor, con la resolución de cada pantalla
- Seis disposiciones automáticas, incluida la optimización máxima
- Ajustar o Rellenar con recorte alrededor de las caras
- Tamaño físico real de las pantallas
- Mover, redimensionar, recortar y retocar con el ratón
- Vista previa en las pantallas antes de aplicar
- Fondo aplicado de nuevo cuando cambian las pantallas
- Rotación automática de las imágenes de una carpeta
- Interfaz en español, inglés, francés y alemán

### Deutsch (de-DE)

**Kurzbeschreibung**
Gestalten Sie ein Hintergrundbild über mehrere Monitore, auch mit unterschiedlichen Größen und Auflösungen, ohne Verzerrung oder abgeschnittene Bilder.

**Beschreibung**
WallCraft Pro gestaltet und setzt Hintergrundbilder für Multi-Monitor-Arbeitsplätze: zwei, drei, hochkant, Ultrawide und unterschiedlich große Bildschirme.

Fügen Sie Ihre Bilder hinzu, wählen Sie eine Anordnung, und WallCraft verteilt sie über alle Monitore. Jeder Monitor erhält genau seinen Teil in seiner Auflösung.

- Sechs Anordnungen, darunter eine Optimierung, die Tausende Varianten testet.
- Einpassen (ganze Bilder) oder Füllen (automatischer Zuschnitt um Gesichter).
- Vier Varianten pro Anordnung, bei gleichen Bildern immer gleich.
- Reale Bildschirmgröße: Der Horizont bleibt zwischen einem 27- und einem 24-Zoll-Monitor gerade, inklusive Rahmen.
- Bearbeitung mit der Maus: verschieben, skalieren, zuschneiden, Ebenen, Helligkeit, Kontrast, Sättigung, Unschärfe.
- Vorschau auf den Bildschirmen vor dem Anwenden.
- Automatischer Hintergrund: WallCraft setzt das Bild erneut, wenn sich die Monitore ändern, und kann Bilder aus einem Ordner wechseln.

Alles geschieht auf Ihrem PC: kein Konto, keine Werbung, keine Datenerhebung.

**Funktionen**
- Ein Hintergrundbild pro Monitor in dessen Auflösung
- Sechs automatische Anordnungen, inklusive maximaler Optimierung
- Einpassen oder Füllen mit Zuschnitt um Gesichter
- Berücksichtigung der realen Bildschirmgröße
- Verschieben, skalieren, zuschneiden und bearbeiten mit der Maus
- Vorschau auf den Bildschirmen vor dem Anwenden
- Hintergrund wird bei Monitorwechsel automatisch erneut gesetzt
- Automatischer Bildwechsel aus einem Ordner
- Oberfläche auf Deutsch, Englisch, Französisch und Spanisch

## Versions suivantes

1. Créez le tag `Tag_vAAAA.MM.JJ` comme d'habitude.
   - Le workflow Release publie l'exe sur GitHub.
   - Le workflow Microsoft Store (MSIX) construit le paquet.
2. Dans Partner Center, sur WallCraft Pro, ouvrez **Mettre à jour** puis **Paquets**, déposez le nouveau `.msix` et envoyez.
