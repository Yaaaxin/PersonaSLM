# Se repérer dans le code

Le code a grandi au fil des essais. Il y a un petit pipeline de génération et d'évaluation, puis des modules propres aux différentes étapes de l'étude.

Pour commencer, je conseille de suivre une exécution P0 dans [cli.py](cli.py), puis [runner.py](runner.py). C'est le chemin le plus court pour comprendre ce que le programme enregistre.

## Le parcours d'une réponse

1. [fixtures.py](fixtures.py) charge les cas fictifs. [conditioning.py](conditioning.py) construit les prompts et les variantes de contexte.
2. [configuration.py](configuration.py) vérifie les paramètres et les fichiers locaux. [server.py](server.py) gère le serveur, et [inference.py](inference.py) les échanges HTTP.
3. [runner.py](runner.py) organise l'exécution. La réponse brute est conservée avant son analyse.
4. [diagnostics.py](diagnostics.py) traite la sortie, puis [evaluation.py](evaluation.py) applique le vérificateur P0.
5. [journal.py](journal.py) enregistre les étapes ; [run_audit.py](run_audit.py) permet de les réexaminer.

Le vérificateur de départ reconnaît des réponses très limitées, notamment sur la ville d'un personnage. Ce n'est pas un juge général de la qualité d'un dialogue.

## Pourquoi plusieurs versions ?

[evaluation_v2.py](evaluation_v2.py) et [evaluation_v3.py](evaluation_v3.py) correspondent à des évolutions de la mesure. Je garde les anciennes versions pour pouvoir comprendre les résultats produits avec elles.

Même principe pour les modules `p1*` et `control_*` : ils suivent les étapes de préparation, de contrôle et de revue des expériences. Leur présence ne veut pas dire que chaque proposition a été exécutée.

Les limites du segment évalué ont pris une place importante dans le travail. [response_boundary.py](response_boundary.py) et [response_status.py](response_status.py) sont utiles pour examiner cette partie, avec les tests associés.

Pour voir les commandes de lancement, lire [reproduire les vérifications](../../docs/reproduire.md). Pour comprendre pourquoi une mesure a changé, partir des [résultats](../../docs/resultats.md) puis du rapport concerné.
