# Qualité et validation

## Application C#

Depuis la racine du dépôt, avec le SDK .NET 10 sous Windows ou Linux, lancez les tests du moteur de composition.

```bash
dotnet run --project csharp/tests/WallCraft.Core.Tests -c Release
```

Les tests couvrent les six dispositions, les variantes, la géométrie multi-écrans, l’appariement des moniteurs, les projets, les retouches et la reprise des fonds mémorisés. Les fichiers dans `csharp/tests/fixtures/` permettent de comparer le cœur C# aux résultats de l’ancienne implémentation.

La CI compile l’application WinUI 3 sur Windows et publie le dossier autonome x64. Le workflow MSIX installe une copie signée, teste un bureau synthétique plus large que la limite GPU, vérifie l’application par écran et en mode « Étendre », puis contrôle la tâche de démarrage et l’ouverture de la fenêtre.

Sur un poste de test Windows, lancez `WallCraft.exe --selftest rapport.json --render-only` pour contrôler le rendu synthétique sans changer le fond ni le démarrage. La [recette matérielle](MIGRATION_CSHARP.md) couvre les DPI mixtes, les coordonnées négatives, le branchement réel et le démarrage à l’ouverture de session.

## Traductions et site

Python sert à exécuter les scripts de maintenance ci-dessous. Le site généré est vérifié par la CI.

```bash
python tools/check_resw.py
python site/site_builder.py
```
