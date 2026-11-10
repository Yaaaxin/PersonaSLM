# Les cas fictifs

J'utilise ici des personnages et des conversations inventés pour contrôler les faits que le modèle reçoit. Cela permet, par exemple, de savoir quelle ville est valable à une date donnée.

Ces fichiers ne sont pas des conversations personnelles importées depuis MimooPet.

## Les fichiers

| Fichier | Étape |
| --- | --- |
| [p0_cases.jsonl](p0_cases.jsonl) | Les cas du premier pipeline P0 |
| [p1_development_v1.json](p1_development_v1.json) | Le jeu de développement P1 |
| [p1b_development_proposed_v1.json](p1b_development_proposed_v1.json) | La première proposition P1b |
| [p1b_development_proposed_v2.json](p1b_development_proposed_v2.json) | Sa révision |
| [p1c_development_proposed_v1.json](p1c_development_proposed_v1.json) | La proposition de développement P1c |

Les noms de fichiers gardent leur version d'origine. Pour savoir lequel a été adopté et utilisé, consulter le rapport de la série et son manifeste dans `docs/validation/`.

Les fichiers ne sont donc pas interchangeables. Modifier un cas déjà utilisé changerait la comparaison avec les sorties enregistrées. Pour une nouvelle variante, je conserve une version distincte.

Le [plan de l'étude](../../docs/etude.md) explique ce qui varie entre conditions. Les données et les validations des étapes suivantes se trouvent aussi dans [docs/validation](../../docs/validation/).
