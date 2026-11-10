# Les scripts d'expérience

Ce dossier est un peu le carnet d'atelier du projet. Les scripts portent le nom de l'étape où je les ai utilisés : `p0_`, `p1_`, `p1b_`, `p1c_` ou `p1d_`.

Ils ne forment pas une seule commande à lancer dans l'ordre alphabétique. Certains préparent des cas, d'autres analysent une exécution déjà faite ou rédigent un rapport à partir de fichiers précis.

## Où commencer

Pour essayer le pipeline de base, utiliser d'abord les [commandes P0](../docs/reproduire.md). Pour retrouver une analyse, partir du [rapport correspondant](../docs/README.md) : il indique les entrées, les versions et les commandes utilisées.

Quelques points de repère dans ce dossier :

| Script | À regarder pour |
| --- | --- |
| [p1_build.py](p1_build.py) | La préparation du premier plan P1 |
| [p1_analyze.py](p1_analyze.py) | L'analyse de cette série |
| [p1b_confirmed_analysis.py](p1b_confirmed_analysis.py) | L'analyse après confirmation des annotations P1b |
| [p1c_paired_statistics.py](p1c_paired_statistics.py) | Les comparaisons appariées de P1c |
| [p1d_budget_analysis.py](p1d_budget_analysis.py) | Le diagnostic du budget de sortie |
| [p1d_format_analysis.py](p1d_format_analysis.py) | Le diagnostic des chaînes d'arrêt |
| [p1d_fair_retrieval_baselines.py](p1d_fair_retrieval_baselines.py) | Les comparaisons hors ligne de sélection d'historique |

Les baselines de sélection comparent notamment un choix aléatoire, le recouvrement lexical, BM25 et des filtres utilisant des dates ou des entités. Une meilleure sélection ne prouve pas à elle seule que le modèle donnera une meilleure réponse.

## Avant de relancer un ancien script

Regarder ses chemins d'entrée et de sortie. Plusieurs scripts utilisent des fichiers de revue précis ou produisent des résultats qui doivent être conservés tels quels. Certains refusent d'écraser un fichier existant.

Pour un nouvel essai, préparer une nouvelle sortie et noter les paramètres utilisés. Le [journal](../docs/research_development_log.md) sert à retrouver ce qui a réellement été lancé. Un fichier de préparation Instruct, par exemple, n'est pas une preuve qu'une génération Instruct a eu lieu.
