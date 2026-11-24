# Dossier de soumission — WallCraft Pro

Préparé le 22 novembre 2026. Ce document rassemble les valeurs à copier dans Partner Center. Il ne signifie pas que Microsoft a certifié ou publié l’application.

## Produit et paquet

| Champ | Valeur |
| --- | --- |
| Nom réservé et nom affiché | WallCraft Pro |
| Éditeur affiché | Rangorn |
| Package Identity Name | `Rangorn.WallCraftPro` |
| Publisher | `CN=16653A68-8E9A-4C36-AC6F-C99EE31C0592` |
| Version | `2026.11.22.0` |
| Architecture / famille | x64 / Windows.Desktop |
| Product ID | `9PLQ23PGJHGH` |
| Package family name | `Rangorn.WallCraftPro_g1kxcrhhexrfa` |
| Type | Application MSIX C# / WinUI 3 |

Déposer le **MSIX Store non signé** du kit de livraison, pas le paquet autosigné du sous-dossier de contrôle. Microsoft applique sa signature lors de la distribution. L’empreinte SHA-256 du fichier livré est fournie à côté du paquet.

[Ouvrir la soumission Partner Center](https://partner.microsoft.com/en-us/dashboard/products/9PLQ23PGJHGH/submissions/1152921505702475049/).

## Tarification et disponibilité

- Prix : **Free / Gratuit**, conformément au choix de l’éditeur.
- Aucun essai, abonnement ni achat intégré ; aucune fonction payante à débloquer.
- Le lien Ko-fi est un soutien volontaire ouvert dans le navigateur et ne débloque aucune fonction.
- Audience privée recommandée pour la dernière recette ; audience publique pour la diffusion finale. Le choix de gratuité ne valide pas à lui seul les marchés ou la date de sortie.
- Disponibilité et date : conserver les marchés souhaités par l’éditeur et vérifier le récapitulatif avant envoi. Ne pas annoncer une date avant la certification.

## Propriétés

| Champ | Valeur ou choix conseillé |
| --- | --- |
| Catégorie principale | Personalization / Personnalisation |
| Catégorie secondaire | Facultative ; Photo + video si pertinente dans le formulaire |
| Site web | https://wallcraft.archi-it.fr/ |
| Support | https://github.com/rangornrar/MultiScreenWallpaper/issues |
| Confidentialité | https://wallcraft.archi-it.fr/en/privacy/ |
| URL française de confidentialité | https://wallcraft.archi-it.fr/fr/privacy/ |
| Modes immersifs / VR | Non concernés |
| Produit utilisant une IA générative | Non ; la détection locale des visages ne génère aucun contenu |
| Revendication d’accessibilité testée | Ne pas cocher sans audit et recette dédiés |

À la question **« Does this product access, collect, or transmit personal information? »**, sélectionner **Yes** : l’application accède aux photos choisies par l’utilisateur, qui peuvent contenir des personnes. Cela ne signifie pas qu’elle les téléverse. Elle ne possède aucun service de collecte, aucune télémétrie et aucun compte utilisateur. La politique décrit le traitement local, les points de cadrage enregistrés, les fichiers conservés et les liens externes.

Les pages publiques de confidentialité répondent, mais la révision du 22 novembre doit être déployée avec le site avant l’envoi final. Vérifier ensuite que le texte en ligne correspond à `site/content_privacy.py`.

Les déclarations facultatives sur l’installation sur d’autres lecteurs et les sauvegardes doivent correspondre aux tests réellement effectués. Ne pas affirmer une compatibilité de sauvegarde ou une certification d’accessibilité sur la seule base d’une case présélectionnée.

## Configuration requise

- PC Windows **x64**, Windows 10 version 2004 / build 19041 minimum technique déclaré ; **Windows 11 recommandé**.
- Une souris pour la composition ; clavier recommandé pour les raccourcis et la saisie.
- Un écran suffit. Plusieurs écrans sont recommandés pour l’usage panoramique ; dimensions physiques modifiables lorsque l’EDID est absent ou imprécis.
- .NET et Windows App SDK inclus ; aucune installation de Python ou d’OpenCV.
- Ne pas inventer de seuil de RAM, VRAM ou processeur : aucune mesure ne permet actuellement de garantir un tel minimum.
- Pas de revendication ARM64 ou x86 pour ce paquet x64.

## Classification par âge et coordonnées

Remplir le questionnaire IARC selon les fonctions du paquet : outil local de création de fonds d’écran, sans catalogue distant, chat, partage public ni contenu adulte fourni par l’éditeur. Les images personnelles choisies par l’utilisateur ne constituent pas une galerie en ligne de l’application.

Renseigner **l’adresse de contact réelle de l’éditeur** demandée par IARC/Partner Center. Elle n’est pas fournie dans le dépôt et ne doit pas être inventée. Laisser le questionnaire produire les classifications régionales ; ne pas saisir une note PEGI/ESRB supposée. Vérifier les déclarations sur les liens externes et le soutien volontaire Ko-fi selon le libellé exact des questions.

## Fiches localisées et visuels

Créer les quatre langues, puis copier les champs et légendes correspondants :

- [Français — fr-FR](FICHE_fr-FR.md)
- [English — en-US](FICHE_en-US.md)
- [Español — es-ES](FICHE_es-ES.md)
- [Deutsch — de-DE](FICHE_de-DE.md)

Chaque langue comporte quatre captures PC PNG réelles de l’interface WinUI 3, dans `captures/<langue>/` : aperçu, composition, taille physique et retouches. Elles proviennent d’une copie de capture avec réglages isolés ; l’interface est celle de l’application. Le panorama de démonstration ne contient aucune photographie privée. Les anciennes illustrations du site ne sont pas utilisées comme captures du Store.

Utiliser `logo-300.png` pour l’icône carrée de la fiche. Laisser les champs Xbox et HoloLens vides : ce paquet cible le bureau Windows.

Une bande-annonce 1920 × 1080 dérivée de la démonstration du site est fournie dans le kit, avec miniature PNG et quatre fichiers VTT. Elle est facultative. La vidéo de 28 secondes montre l’interface française ; les textes VTT sont localisés. Ne pas utiliser directement la version web 1280 × 720 dans le champ bande-annonce.

Les descriptions sont du texte brut, sans liens HTML. Saisir chaque fonctionnalité dans un champ séparé sans ajouter de puce. Laisser **What’s new** vide pour cette première soumission. Les fichiers Markdown servent au copier-coller, pas à un import CSV Partner Center.

## Capacité restreinte runFullTrust — texte à copier

```text
WallCraft Pro is a WinUI 3 desktop application built with .NET and packaged as MSIX. Full trust is required to set per-monitor wallpapers through the Windows IDesktopWallpaper COM API, read monitor physical dimensions from EDID in the registry, and show a notification-area icon. Startup uses the package startup task and is disabled by default. The app processes user-selected images locally. It does not upload images, collect telemetry, or download or execute external code. Website, support and optional donation links open in the user's browser.
```

## Notes pour la certification — texte à copier

```text
No account, sign-in, purchase or network connection is required to use the application. It works with one monitor and is designed for multiple monitors.

1. Add local JPG or PNG images. Select a layout and click Auto-arrange. Mosaic places one image per monitor when the number of images does not exceed the number of monitors. For a single panorama across the whole desktop, use Horizontal strips.
2. Switch between Fit and Fill, then inspect Preview on screens. Apply wallpaper to set the result through IDesktopWallpaper.
3. In Screens > Real screen size, check EDID dimensions and adjust bezel gaps or vertical offsets if needed.
4. Save/open a project or export the result. Originals are not overwritten by these operations.
5. Screens > Automatic wallpaper controls re-application, folder rotation and optional Start with Windows. Startup is disabled by default, uses the package startup task and can also be disabled in Windows Settings.

The package includes .NET and Windows App SDK runtimes. No Python or separate runtime installation is needed. There is no generative AI, account, advertising, subscription or in-app purchase. The optional Ko-fi link opens an external donation page and unlocks no functionality.

Local WACK 10.0.26100.9457 on Windows build 26300 returned overall WARNING: 21 PASS, 2 optional FAIL (metadata in Microsoft runtime winmd files, static blocked-executable/API references in runtime libraries and browser-link launch code), and DPIAwarenessValidation WARNING (could not process the executable). The embedded executable manifest was extracted and contains dpiAware=true/PM and dpiAwareness=PerMonitorV2. These findings are disclosed, not claimed as a clean WACK pass. Installed-package self-tests passed on three actual monitors, including per-monitor application, Span fallback, wide rendering and startup-task enable/disable.
```

## Dernière vérification avant Envoyer

Consulter le [rapport de validation](VALIDATION_2026-11-22.md) et terminer la recette physique restante. Vérifier que les quatre langues, le prix gratuit, le paquet, les URL, la classification IARC et les coordonnées sont enregistrés. L’envoi final et la publication restent à effectuer dans Partner Center ; aucune certification Microsoft n’est acquise à ce stade.

Après publication, le lien du produit sera [Microsoft Store](https://apps.microsoft.com/detail/9PLQ23PGJHGH), et le lien d’ouverture dans l’application Store sera `ms-windows-store://pdp/?productid=9PLQ23PGJHGH`.

## Références vérifiées le 22 novembre 2026

- [Champs d’une fiche MSIX](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msix/add-and-edit-store-listing-info) : description, fonctionnalités, langues et nouveautés.
- [Captures et bandes-annonces](https://learn.microsoft.com/windows/apps/publish/publish-your-app/msix/screenshots-and-images) : formats et dimensions des fichiers.
- [Windows App Certification Kit](https://learn.microsoft.com/windows/uwp/debug-test-perf/windows-app-certification-kit) : contrôle local du paquet.
- [Manifestes DPI](https://learn.microsoft.com/windows/win32/hidpi/setting-the-default-dpi-awareness-for-a-process) : déclarations du manifeste embarqué.
