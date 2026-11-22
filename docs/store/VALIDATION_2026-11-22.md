# Validation de WallCraft Pro — 22 novembre 2026

Le MSIX **2026.11.22.0 x64** porte l’identité officielle `Rangorn.WallCraftPro`. Il est construit et installable. Les tests fonctionnels automatisés passent sur ce poste à trois écrans. **Le contrôle WACK retourne WARNING : ce n’est pas un rapport entièrement réussi et ce n’est pas une certification Microsoft.**

## Paquet contrôlé

| Élément | Résultat |
| --- | --- |
| Fichier Store non signé | `WallCraft-Pro-2026.11.22-Store-x64.msix` |
| Taille | 98 644 978 octets |
| SHA-256 | `71f0f9457d503aa3ea4f431b8ff9a15a5a97ca8d4335d2a6824877f0aa0ff161` |
| Publisher | `CN=16653A68-8E9A-4C36-AC6F-C99EE31C0592` |
| Éditeur affiché | Rangorn |
| Version / architecture | 2026.11.22.0 / x64 |
| Famille / minimum déclaré | Windows.Desktop / 10.0.19041.0 |
| Runtimes | .NET 10 et Windows App SDK embarqués |
| Code Python ou clé privée dans le MSIX | Aucun fichier .py, .pfx ou .key |

Compilation Release réussie : zéro erreur. Un avertissement indique l’absence de `mspdbcmf.exe` pour la production des symboles `.appxsym` ; le MSIX est généré. La livraison est un MSIX autonome, sans fichier de symboles d’envoi `.msixupload`.

## Vérifications réussies

- **54/54 tests C#** du cœur : dispositions, géométrie, formats de projet, retouches, migration des fonds et résultats de référence.
- **51/51 tests Python historiques** réussis : références de migration conservées, sans dépendance Python pour utiliser le MSIX.
- **153 ressources identiques dans les quatre langues**, vérifiées par `tools/check_resw.py`.
- Construction du site régénéré avec les pages de confidentialité révisées et la démonstration sur les huit pages concernées.
- Identité, version et architecture relues dans `AppxManifest.xml` du MSIX final ; paquet Store conservé non signé.
- Installation d’une copie du même MSIX signée avec un certificat de contrôle temporaire.
- `--selftest` en contexte MSIX : `packaged=true`, `wide_render=true`, `native_status=Ok`, aucune erreur native, **3 écrans appliqués sur 3 attendus**.
- Mode Étendre : `wallpaper_set=true`.
- Tâche de démarrage : désactivée avant, activation réussie, état activé confirmé, puis désactivation confirmée. Cela ne prouve pas un lancement après une vraie ouverture de session.
- Fonds d’écran précédents sauvegardés puis restaurés après le test.
- Certificat de contrôle retiré de `LocalMachine/TrustedPeople`, `CurrentUser/TrustedPeople` et `CurrentUser/My` ; absence confirmée par le script de nettoyage.
- **16 captures PNG réelles de l’interface C#**, quatre par langue, 1522 × 818. Une copie de capture utilise des réglages isolés et un panorama de démonstration sans photo privée.
- Bande-annonce 28 secondes, H.264, 1920 × 1080, yuv420p, sans audio, décodée sans erreur. Export agrandi depuis le montage web 1280 × 720 ; la résolution supplémentaire n’ajoute pas de détail.

Les rapports techniques locaux sont conservés dans le dossier de livraison. Les résumés destinés au partage omettent les chemins privés de l’utilisateur.

## Rapport Windows App Certification Kit

Environnement : Windows 11 Professionnel build **26300**, WACK **10.0.26100.9457**, analyse du paquet installé. Résultat global : **WARNING**. Total : **21 PASS, 2 FAIL facultatifs, 1 WARNING**.

| Contrôle restant signalé | Résultat | Éléments constatés et portée |
| --- | --- | --- |
| Exactitude des métadonnées générales | FAIL, facultatif | GUID partagés entre des types Microsoft.UI et Windows.UI, et métadonnées MethodImpl dans Microsoft.Windows.Internal.AI.Generative.winmd. Les messages désignent des fichiers du Windows App SDK embarqué. L’application n’utilise pas ces fonctions d’IA générative. |
| Fichiers exécutables bloqués | FAIL, facultatif | Analyse statique de Process.Start, ShellExecute et CreateProcess dans l’application et les runtimes ; références textuelles à cmd/reg/etc. dans plusieurs bibliothèques. Le code applicatif ouvre des URL externes. Ce contrôle ne constitue pas à lui seul une observation d’exécution de commandes ; aucune trace exhaustive des processus enfants n’a été réalisée. |
| DPIAwarenessValidation | WARNING | Le kit indique ne pas pouvoir traiter WallCraft.exe puis le considère incompatible DPI. Le manifeste RT_MANIFEST extrait du binaire installé contient bien `dpiAware=true/PM` et `dpiAwareness=PerMonitorV2`. Cela explique une divergence, sans suffire à garantir le passage du test Microsoft. |

Tous les autres contrôles, notamment manifeste du paquet, ressources, capacités, absence de clé privée et configuration de débogage, retournent PASS. Le test de débogage émet aussi des diagnostics de chargement de bibliothèques .NET malgré son résultat PASS ; le rapport brut les conserve.

Ne pas supprimer arbitrairement les bibliothèques du Windows App SDK pour masquer ces résultats. Joindre l’explication aux notes de certification. En cas de refus Microsoft, exploiter le motif exact et produire un nouveau paquet versionné avec la correction requise.

## Limites et dernière recette

Ces étapes restent à réaliser avant une ouverture publique :

- Installation sur une VM propre et test de la version minimale de Windows revendiquée.
- Installation d’une mise à jour MSIX et conservation des réglages et fonds réels ; cette première installation ne prouve pas la mise à jour.
- Branchement/débranchement d’une station d’accueil, dispositions avec coordonnées négatives, écrans à DPI ou orientations différents, retour d’un thème Windows.
- Fermeture puis ouverture réelle de session avec le démarrage activé.
- Recette complète des imports/exports, des formats d’images, de la reprise des projets Python et de la rotation de dossier, selon la [liste de parité](../MIGRATION_CSHARP.md).
- Vérification du changement de langue à chaud : un texte de sélection déjà affiché peut garder sa langue précédente jusqu’à la prochaine modification de sélection. Les captures reflètent cette limite de l’interface actuelle.
- Déploiement du site régénéré : vidéo et révision du 22 novembre de la politique de confidentialité ; validation des URL publiques après déploiement.
- Questionnaire IARC et coordonnées réelles de contact de l’éditeur, récapitulatif Partner Center, envoi à la certification puis installation depuis le Store.

La recommandation est de déposer ce paquet pour une validation auprès d’une audience privée, avec les avertissements documentés, puis de terminer cette recette avant l’ouverture publique. Le dépôt de fichiers et les tests locaux ne valent pas acceptation par Microsoft.

## Sources

[Contrôle local WACK](https://learn.microsoft.com/windows/uwp/debug-test-perf/windows-app-certification-kit), [configuration DPI](https://learn.microsoft.com/windows/win32/hidpi/setting-the-default-dpi-awareness-for-a-process), code du manifeste et rapports locaux du 22 novembre 2026.
