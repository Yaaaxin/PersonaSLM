# Essayer le code

J'ai fait les essais locaux sous Windows, sur CPU. Les commandes ci-dessous utilisent PowerShell et se lancent à la racine du dépôt, avec Python 3.10 ou plus récent.

On peut commencer sans modèle : les données fictives et les tests permettent déjà de regarder comment les réponses sont préparées, découpées et évaluées.

## Installer et vérifier

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m personaslm validate
.\.venv\Scripts\python.exe -m personaslm smoke
.\.venv\Scripts\python.exe -m pytest -q
```

Sous Linux ou macOS, le chemin de Python dans cet environnement est `.venv/bin/python`.

`validate` vérifie les cas P0, les faits partagés entre conditions et les chemins du projet. `smoke` montre quelques cas de découpage sur des réponses écrites à l'avance. Aucune de ces deux commandes ne génère de texte avec un modèle.

Les [tests](../tests/README.md) vérifient le logiciel. Leur réussite ne dit pas si les réponses d'un modèle seront bonnes.

## Faire une génération locale P0

Cette commande est le point d'entrée du premier pipeline, P0. Les expériences suivantes ont leurs propres scripts et configurations ; elles ne se relancent pas toutes avec `run-local`.

Il faut un fichier GGUF et un exécutable `llama-server` compatibles. Ils ne sont pas fournis par l'installation Python. Les chemins doivent rester dans le dossier du projet ; le programme ne va pas chercher un modèle ailleurs sur la machine.

Copier la configuration d'exemple :

```powershell
Copy-Item configs/p0_runtime.example.json configs/p0_runtime.local.json
```

Dans cette copie, renseigner `model_file`, `model_sha256` et `server_file`, puis indiquer le modèle et la révision de llama.cpp dans `model_label` et `engine_revision`. Les autres champs fixent notamment la graine, le budget de sortie et la taille du contexte.

L'empreinte SHA-256 sert à vérifier le fichier utilisé. Calculer une empreinte locale avec `hash-model` ne prouve pas à lui seul l'origine du modèle : il faut la comparer à une référence de confiance.

```powershell
.\.venv\Scripts\python.exe -m personaslm preflight --config configs/p0_runtime.local.json
.\.venv\Scripts\python.exe -m personaslm run-local --config configs/p0_runtime.local.json --condition C0
```

`preflight` vérifie les fichiers sans démarrer le serveur. `run-local` démarre son propre serveur CPU sur l'adresse locale configurée, puis l'arrête à la fin. Si le port est déjà occupé, le lancement est refusé. Les sorties sont enregistrées dans un nouveau dossier sous `results/p0/`.

Le pipeline conserve les entrées, les réponses brutes et les étapes de traitement. C'est ce qui permet de revenir sur une erreur de découpage sans perdre la sortie originale.

## Réexaminer une exécution enregistrée

Remplacer `YOUR_RUN_ID` par le dossier d'une exécution locale :

```powershell
.\.venv\Scripts\python.exe -m personaslm audit-run --run-dir results/p0/YOUR_RUN_ID
.\.venv\Scripts\python.exe -m personaslm replay-run --run-dir results/p0/YOUR_RUN_ID --output results/replay_check_01.json
```

Choisir un nouveau nom de fichier pour chaque rapport de replay. Il doit se trouver hors du dossier de l'exécution d'origine.

Le replay reprend les données enregistrées pour refaire le traitement et l'évaluation hors ligne. Il ne redemande pas une réponse au modèle. Pour une ancienne exécution sans copie du jeu de données, l'option `--cases` permet de fournir le fichier correspondant, dont l'empreinte doit être identique.

## Retrouver une expérience plus récente

Pour P1 à P1d, partir du [rapport de la série](README.md), puis suivre ses références vers les scripts, les configurations et les fichiers dans `docs/validation/`. Le dossier [tools](../tools/README.md) donne quelques points d'entrée.

J'ai conservé les versions des mesures et les fichiers utilisés à chaque étape. Une nouvelle version du code peut interpréter différemment une réponse ; elle ne remplace pas automatiquement la mesure d'une ancienne expérience.
