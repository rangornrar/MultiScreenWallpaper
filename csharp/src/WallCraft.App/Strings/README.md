# Traductions (`Strings/`)

L’interface WinUI 3 utilise les ressources `<culture>/Resources.resw` (en-US, fr-FR, es-ES, de-DE). Le générateur lit encore les catalogues de l’ancienne implémentation dans `python/locales.py` et `python/ui_text.py`. Modifiez ces catalogues puis régénérez les `.resw`. Python est utilisé pour cette étape de maintenance.

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

Les catalogues `python/locales.py` et `python/ui_text.py` restent les entrées du générateur. Après une modification de texte, versionnez les catalogues modifiés et les quatre fichiers `.resw` régénérés.
