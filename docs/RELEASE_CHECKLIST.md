# Liste de publication

## Préparer la version C#

- Exécuter `dotnet run --project csharp/tests/WallCraft.Core.Tests -c Release` et `python tools/check_resw.py`.
- Vérifier le build Windows x64 et dérouler la [recette sur le MSIX installé](MIGRATION_CSHARP.md), notamment l’import des données, les écrans de tailles et DPI différents, le branchement et le démarrage à l’ouverture de session.
- Prendre les captures de la version WinUI 3 dans les langues de la fiche. Publier les pages de confidentialité et vérifier leur URL publique.

## Construire et soumettre le MSIX

- Renseigner les variables `MSIX_*` avec l’identité du produit Partner Center.
- Dans GitHub Actions, lancer **Microsoft Store (MSIX)** avec la version prévue et l’option de construction avec l’identité Partner Center. Un tag `Tag_vAAAA.MM.JJ` construit aussi ce paquet lorsque les variables sont renseignées.
- Attendre le succès des vérifications. Télécharger `wallcraft-store-msix` et contrôler son identité et sa version. Exécuter le Windows App Certification Kit et suivre le [guide Microsoft Store](MICROSOFT_STORE.md).
- Compléter les [notes de version](RELEASE_NOTES_TEMPLATE.md) et vérifier l’installation depuis la fiche après certification.

## Site et autres téléchargements

- Mettre à jour la page de téléchargement avec l’URL Store après publication. Depuis la racine du dépôt, générer le site avec `python site/site_builder.py`, déployer `site/html/` et vérifier les liens.
- Pour un téléchargement de développement C#, utiliser l’artefact `WallCraft-win-x64` du [workflow C#](../.github/workflows/csharp.yml). Le workflow historique [Release](../.github/workflows/release.yml) construit encore l’ancien exécutable Python à partir des tags. Les liens qui pointent vers ces archives doivent l’indiquer.
