# Qualité et validation

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Six tests vérifient les six modes de placement sur un jeu de ratios variés, leurs limites et absence de recouvrement, le cas vide, la rotation et l’invalidation du cache, le clonage, un aller-retour de projet et l’utilisation des pixels originaux lors de l’export. Les cas non déterministes utilisent une graine fixée ; ils ne démontrent pas toutes les combinaisons possibles.

La CI utilise Python 3.11 et les dépendances versionnées. Avant une version Windows, vérifier manuellement la détection des moniteurs, les coordonnées négatives, les DPI mixtes, l’application native et son repli, puis mesurer mémoire et temps d’export avec des images réelles.

Aucun résultat de benchmark, test d’installation ou taux de couverture global n’est revendiqué.
