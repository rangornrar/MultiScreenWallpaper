# Release Checklist

Les exécutables ne sont plus versionnés dans Git : ils sont construits par GitHub Actions
(`.github/workflows/release.yml`) depuis le code du tag (dossier `python/`), puis joints à la release avec leur SHA-256.

## Avant de publier
- Mettre à jour `PRODUCT_VERSION`, `RELEASE_TAG` et `TODAY` dans `site/site_builder.py`.
- Vérifier que les tests passent (`cd python && python -m unittest discover -s tests -v`).
- Si l'interface a changé, refaire les captures du site et des README dans les 4 langues :
  `xvfb-run -a -s "-screen 0 1920x1080x24" python tools/make_screenshots.py` (Linux).
- Tester sur Windows 10 et 11 : détection des écrans, écrans de tailles et DPI différents,
  coordonnées négatives, application par écran et repli « Étendre ».

## Publier
- Pousser un tag `vAAAA.M.J` (par exemple `git tag v2026.11.7 && git push origin v2026.11.7`).
- Attendre la fin du workflow **Release** : il crée la release avec l'exe et son fichier `.sha256`.
- Compléter les notes de version avec `RELEASE_NOTES_TEMPLATE.md`.
- Microsoft Store (version C#) : le workflow **Microsoft Store (MSIX)** construit et vérifie le paquet du même tag.
  Télécharger l'artefact `wallcraft-store-msix` et le déposer dans Partner Center (voir `MICROSOFT_STORE.md`).

## Après publication
- Régénérer le site : `python site/site_builder.py`, puis publier le contenu de `site/html/` sur l'hébergeur. Le lien de téléchargement est construit à partir de
  `RELEASE_TAG` et `PRODUCT_VERSION` ; vérifier qu'il répond bien.
- Vérifier la page de téléchargement sur https://wallcraft.archi-it.fr/.
