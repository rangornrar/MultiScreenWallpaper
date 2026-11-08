# Qualité et validation

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Les tests de `tests/test_image_tools.py` vérifient les six modes de placement sur un jeu de ratios variés, leurs limites et absence de recouvrement, le cas vide, la rotation et l’invalidation du cache, le clonage, un aller-retour de projet et l’utilisation des pixels originaux lors de l’export. Les cas non déterministes utilisent une graine fixée ; ils ne démontrent pas toutes les combinaisons possibles.

`tests/test_audit_fixes.py` couvre l’orientation EXIF, le chargement différé des originaux, les erreurs de chargement signalées, le ratio après rognage, l’équilibre du mode optimal, l’absence de liseré à l’export, le découpage par écran, l’appariement des écrans empilés et la validation des projets JSON.

La CI exécute pyflakes et les tests sous Ubuntu et Windows, avec Python 3.11 et 3.14 (version embarquée dans l’exécutable). Avant une version Windows, vérifier manuellement la détection des moniteurs, les coordonnées négatives, les DPI mixtes, l’application native et son repli, puis mesurer mémoire et temps d’export avec des images réelles.

Aucun résultat de benchmark, test d’installation ou taux de couverture global n’est revendiqué.
