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

**Placement sans rognage.** Les modes testés placent les images dans les limites de la surface et conservent leurs ratios, à l’arrondi pixel près. Les espaces libres sont un compromis acceptable pour éviter de couper les photos. Ne pas confondre cette propriété avec un remplissage garanti de tout l’écran.

**Recherche heuristique bornée.** Le mode optimal explore des arbres de découpage pendant environ 0,85 seconde. La qualité dépend des images, de l’aléatoire et de la machine. Ce n’est pas une preuve d’optimum global ; un benchmark reproductible serait nécessaire avant d’annoncer des gains chiffrés.

**Intégration Windows localisée.** Les appels COM et registre restent dans `screen_splitter.py`. Les tests géométriques fonctionnent indépendamment de cette intégration ; ils ne valident pas l’application réelle du papier peint.

## Distribution

Les exécutables déjà suivis dans `dist/` sont conservés pour ne pas casser les liens existants. `dist/` est ignoré pour les nouveaux fichiers ; les prochains exécutables doivent être joints à des GitHub Releases. Le dépôt reste la source du code, les Releases le canal prévu pour les binaires. L’historique n’est pas réécrit.

## Évolutions utiles

Extraire les algorithmes de placement de `image_tools.py` si leur évolution devient indépendante des opérations d’image ; mesurer temps de calcul et mémoire sur des jeux représentatifs ; définir les versions de schéma avant toute évolution incompatible des projets JSON.
