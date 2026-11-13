# Traductions (`Strings/`)

Les fichiers `<culture>/Resources.resw` (en-US, fr-FR, es-ES, de-DE) sont **générés** à partir des textes de l'application Python : `locales.py` (dictionnaire `_STRINGS`) et `ui_text.py` (dictionnaire `UI_TEXT`). Ne les modifiez pas à la main : vos changements seraient écrasés à la prochaine génération.

## Régénérer et vérifier

Depuis la racine du dépôt :

```
python3 tools/export_resw.py
python3 tools/check_resw.py
```

La sortie est déterministe (ressources triées par nom, UTF-8 avec BOM) : relancer le script sans changer les textes ne modifie aucun fichier. `check_resw.py` vérifie que les 4 langues ont les mêmes clés, le même nombre de marqueurs, aucune valeur vide, et que le XML est valide ; il retourne 1 en cas de problème.

## Conventions

- **Noms** : les clés Python telles quelles (snake_case), par exemple `btn_apply`. Si une clé existe dans les deux fichiers Python, `ui_text.py` l'emporte et un `<comment>` le signale.
- **Pluriels** : une entrée Python `(singulier, pluriel)` devient deux ressources, `<clé>_One` et `<clé>_Other`. Le code C# choisit la ressource selon le nombre.
- **Marqueurs** : les `{}` de Python deviennent `{0}`, `{1}`… dans l'ordre d'apparition, pour `string.Format`. Les accolades littérales restent doublées (`{{` et `}}`).
- **Langue manquante** : le texte anglais est repris et un `<comment>MISSING:<langue></comment>` est ajouté.
- `AppDisplayName` (« WallCraft Pro ») est ajouté dans chaque langue par le script.

## Source de vérité

Tant que l'application Python existe, la source de vérité reste `locales.py` / `ui_text.py`. Toute nouvelle chaîne ou correction s'y fait, puis on régénère les `.resw`. Après la bascule vers C#, les `.resw` deviendront la source et ce script pourra être retiré.
