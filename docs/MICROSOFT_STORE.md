# Publier WallCraft Pro sur le Microsoft Store

Le dossier de la version **2026.11.22** est prêt à renseigner dans Partner Center : [champs de soumission](store/SOUMISSION.md), [textes français](store/FICHE_fr-FR.md), [anglais](store/FICHE_en-US.md), [espagnols](store/FICHE_es-ES.md), [allemands](store/FICHE_de-DE.md), captures PNG et [rapport de validation](store/VALIDATION_2026-11-22.md).

WallCraft Pro est une application **C# / WinUI 3**, distribuée en **MSIX x64 autonome**. Le minimum technique déclaré est Windows 10 version 2004, build 19041 ; Windows 11 est recommandé. .NET 10 et Windows App SDK sont embarqués. L’utilisateur n’a besoin ni de Python, ni d’une installation séparée de ces runtimes. Python reste utilisé pour la maintenance du dépôt et les références de migration.

## Identité et version

| Champ | Valeur |
| --- | --- |
| Nom public | WallCraft Pro |
| Package/Identity/Name | `Rangorn.WallCraftPro` |
| Package/Identity/Publisher | `CN=16653A68-8E9A-4C36-AC6F-C99EE31C0592` |
| Package/Properties/PublisherDisplayName | `Rangorn` |
| Product ID | `9PLQ23PGJHGH` |
| Version MSIX préparée | `2026.11.22.0` |
| Prix décidé par l’éditeur | Gratuit |

Ces valeurs d’identité ne sont pas secrètes. Elles sont intégrées au manifeste et au workflow Store. Les variables GitHub `MSIX_IDENTITY_NAME`, `MSIX_PUBLISHER` et `MSIX_PUBLISHER_DISPLAY_NAME` peuvent les remplacer ; pour ce produit, conserver les valeurs du tableau.

## Construire et vérifier

Dans GitHub Actions > **Microsoft Store (MSIX)** > **Run workflow**, indiquer la version et cocher **Construire avec l’identité définitive de Partner Center**. Les tags `Tag_vAAAA.MM.JJ` ou `vAAAA.MM.JJ` utilisent aussi l’identité de production. Les PR et les lancements manuels sans cette option gardent `WallCraftPro.Dev`.

Le workflow construit le MSIX, installe une copie signée pour les tests et vérifie le rendu au-delà de la limite GPU, l’application par écran, le repli Étendre, la tâche de démarrage et l’ouverture de l’interface. Après succès, télécharger `wallcraft-store-msix` et déposer le fichier `WallCraft-Pro-v<version>-store.msix` dans Partner Center. Le Store signe le paquet distribué ; la copie autosignée de contrôle ne doit pas être envoyée.

Le kit Microsoft apporte un contrôle local complémentaire, avec ses limites documentées dans le rapport. Il ne remplace pas la certification effectuée par Microsoft. Poursuivre la [recette matérielle](MIGRATION_CSHARP.md) pour les changements réels de branchement, les DPI mixtes, l’ouverture de session et une VM propre.

## Données et comportements propres au MSIX

- Les fonds appliqués sont enregistrés dans le dossier réel du paquet afin que Windows puisse les lire.
- Le lancement avec Windows utilise la tâche de démarrage du paquet, désactivée par défaut et contrôlable dans les paramètres Windows.
- Les réglages de l’ancienne installation sont repris au premier lancement. Les fonds mémorisés sont importés pour chaque configuration d’écrans à sa première utilisation. Les projets existants s’ouvrent depuis l’application.
- L’application et l’export par écran rendent chaque écran séparément. L’export en une image et le repli Étendre restent limités par la taille maximale de texture du GPU.
- Les photos sont traitées localement. La détection des visages utilise Windows.Media.FaceAnalysis, sans reconnaissance d’identité. Les projets peuvent conserver un point de cadrage.
- Les fichiers originaux, projets et exports enregistrés dans les dossiers choisis par l’utilisateur ne sont pas supprimés avec le paquet.

## Soumettre et mettre à jour

Renseigner les sections indiquées dans le [dossier de soumission](store/SOUMISSION.md). Un test auprès d’une audience privée est recommandé avant une ouverture publique ; il n’est pas une certification déjà obtenue. Après publication, vérifier l’installation depuis le Store, puis activer le lien de téléchargement public sur le site.

Pour une mise à jour, augmenter la version, reconstruire et tester le paquet, remplacer le MSIX dans une nouvelle soumission et renseigner les nouveautés. La quatrième composante de version reste `0` pour les paquets soumis au Store.
