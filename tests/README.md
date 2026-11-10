# Ce que vérifient les tests

Ces tests portent sur le code de l'expérience : préparer les bonnes entrées, conserver la sortie brute, traiter les erreurs et appliquer la mesure prévue.

Je les garde séparés de l'évaluation des réponses du modèle. Un test logiciel peut passer alors que le modèle ne répond toujours pas à la question.

## Lancer les tests

Après l'[installation](../docs/reproduire.md), depuis la racine du dépôt :

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Pour regarder seulement le parcours P0 et les limites de réponse :

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_runner.py tests/test_response_boundary.py tests/test_response_status.py
```

Sous Linux ou macOS, utiliser `.venv/bin/python` à la place du chemin Windows.

## Quelques fichiers pour commencer

- [test_conditions.py](test_conditions.py) : les variantes du contexte.
- [test_runner.py](test_runner.py) : le déroulement d'une exécution, avec un serveur et un client simulés, y compris des erreurs injectées.
- [test_response_boundary.py](test_response_boundary.py) : les limites de réponse et les risques de couper au mauvais endroit.
- [test_evaluation.py](test_evaluation.py), [v2](test_evaluation_v2.py) et [v3](test_evaluation_v3.py) : les versions successives des vérificateurs.
- [test_run_audit.py](test_run_audit.py) : la relecture des données enregistrées.
- Les fichiers `test_p1*` : les contrôles propres aux séries et à leurs analyses.

Les exemples simulés aident à reproduire un problème précis. Pour juger les sorties réellement produites par le modèle, il faut aussi lire les [rapports expérimentaux](../docs/README.md) et leurs annotations.
