# Lire la documentation

Si vous découvrez le projet, je vous conseille de commencer par ces trois pages :

1. [L'étude](etude.md) explique ce que je cherche à mesurer.
2. [Les résultats](resultats.md) rassemble les observations utiles et les questions encore ouvertes.
3. [Reproduire les vérifications](reproduire.md) présente le code, l'installation et les commandes.

## Comment le travail a avancé

| Étape | Question principale | Rapport à lire |
| --- | --- | --- |
| P0 | Est-ce que je conserve et évalue correctement les sorties du modèle ? | [Validation du pipeline](P0_final_scientific_acceptance_report.md) |
| P1 | Que se passe-t-il quand je combine style, faits personnels et historique ? | [Premier pilote](P1_pilot_wave1_report.md) |
| P1b | Les réponses sont-elles correctes, complètes et réellement utiles pour la tâche ? | [Analyse de la réponse à la demande](P1b_task_completion_analysis.md) |
| P1c | Que change un historique selon son contenu et sa période de validité ? | [Analyse exploratoire confirmée](P1c_researcher_confirmed_exploratory_analysis_v1.md) |
| P1d | Le budget de sortie et le format permettent-ils de mesurer correctement la réponse ? | [Diagnostic de format](P1d_format_diagnostic_scientific_report_v1.md) |

Les séries n'ont pas toutes les mêmes tâches ni les mêmes conditions. Je ne les additionne pas pour produire un seul taux de réussite.

## Les rapports détaillés

Les rapports en anglais sont les documents de travail conservés au fil des expériences. Un ancien fichier peut encore indiquer qu'une décision est en attente, alors qu'un rapport ultérieur enregistre cette décision. Le [catalogue](catalogue.md) les regroupe par étape pour faciliter la recherche.

Pour l'état technique le plus récent du travail expérimental, voir le [rapport de décision P1d](P1d_next_scientific_decision_packet_v1.md). Il distingue les essais déjà réalisés, le petit essai Instruct proposé et l'étude principale qui n'a pas encore été lancée.

Le [protocole v1.1](research_protocol_v1.1.md) reste le point de départ méthodologique. Les propositions de protocole et les modifications adoptées sont des documents distincts : la présence d'un fichier nommé « proposed » ne signifie pas que son contenu a été appliqué.

## Retrouver les données d'une analyse

Les rapports renvoient aux tableaux, annotations et configurations dans `validation/`. Le [journal de développement](research_development_log.md) décrit les commandes, les problèmes rencontrés et les changements. Les anciens textes sont conservés à leur emplacement pour que ces références et les empreintes des fichiers restent utilisables.

Je garde une distinction entre une annotation proposée avec une aide IA, une décision que j'ai confirmée et une évaluation indépendante. Les rapports précisent laquelle a été utilisée.
