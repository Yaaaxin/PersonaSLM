# Ce que les expériences m'ont appris

Cette page reprend les observations des rapports. Elle ne présente pas une nouvelle analyse et ne remplace pas les annotations enregistrées.

## Premier pilote : vérifier le vérificateur

Le premier pilote a produit **96 réponses**, à partir de 12 cas et des huit conditions S/F/H.

Le vérificateur automatique avait une limite importante. Il reconnaissait une forme simple de réponse sur la ville actuelle, mais certaines réponses ajoutaient une date. Elles nommaient la ville attendue tout en restant hors de la grammaire reconnue par le vérificateur.

Parmi les 72 réponses éligibles à la mesure factuelle, les étiquettes enregistrées étaient 15 correctes et 57 invérifiables. Cela ne signifie ni que les 57 étaient fausses, ni que les 15 autres prouvaient un effet positif du persona.

Ce premier essai m'a surtout montré qu'il fallait examiner la couverture de la mesure avant de comparer les scores.

Source : [rapport du premier pilote](P1_pilot_wave1_report.md).

## P1b : une affirmation vraie peut laisser la tâche inachevée

Cette série comprend **192 réponses** sur 24 cas, issus de 12 personnages fictifs. Les propositions d'annotation ont été préparées avec une aide IA puis confirmées par moi. Il n'y avait pas de deuxième évaluateur indépendant.

Les jugements factuels comptent 137 réponses correctes, 34 incorrectes et 21 invérifiables. Le critère exploratoire de tâche réussie exige davantage : une réponse complète, correcte et couvrant les éléments demandés. **110 réponses** satisfont ce critère dans l'analyse utilisant les segments confirmés.

Un segment reste ambigu. L'analyse conservatrice garde donc 109 réussites connues, 82 non-réussites connues et un cas incertain, sur le même total de 192.

Un groupe de tâches rend cette différence particulièrement visible : 24 réponses sur 24 reçoivent un jugement factuel positif, mais seules quatre donnent la réponse complète demandée. C'est pourquoi je regarde séparément la vérité des affirmations et la réussite de la tâche.

Sources : [annotations confirmées](P1b_researcher_confirmed_annotation_report.md), [analyse de la tâche](P1b_task_completion_analysis.md).

## P1c : garder visibles les cas incertains

P1c comporte **72 réponses**, pour 12 cas rattachés à six personnages fictifs. Le plan examine des variantes d'historique, notamment leur contenu et leur période de validité.

Dans l'analyse principale confirmée, le diagnostic de réussite de la tâche donne **43 réussites, 20 échecs et neuf cas incertains**. Une analyse de sensibilité sur les limites de réponse donne d'autres comptes sur ces mêmes 72 sorties. Ce n'est pas une deuxième série d'expériences.

Cette étape m'a amenée à regarder de plus près la définition du morceau de texte évalué. Changer sa limite peut changer le score sans changer la sortie originale du modèle.

Les variantes d'historique modifient plusieurs aspects du contexte. Les résultats ne permettent donc pas d'attribuer chaque différence à un mécanisme unique.

Source : [analyse exploratoire confirmée](P1c_researcher_confirmed_exploratory_analysis_v1.md).

## P1d : plus de tokens, puis des chaînes d'arrêt

J'ai ensuite testé trois budgets de sortie : **96, 192 et 256 tokens**, sur huit cas de développement et six conditions, soit **144 générations**.

Aucun de ces budgets n'a rempli le critère provisoire de réponse complète utilisé dans ce diagnostic. Les jugements sémantiques de cette série restent des propositions assistées par IA, sans confirmation humaine enregistrée.

L'essai suivant a comparé deux formats sur huit cas : sans chaîne d'arrêt et avec des chaînes d'arrêt, soit **16 générations**. Les chaînes d'arrêt ont empêché la continuation vers d'autres tours de dialogue. Mais, dans les huit paires, le contenu de la première réponse était identique après normalisation des espaces.

L'analyse provisoire n'a pas trouvé les éléments de réponse demandés dans ces sorties. Le changement de format a donc contrôlé la continuation sans résoudre la livraison de la réponse dans cet essai.

Sources : [diagnostic du budget](P1d_budget_calibration_scientific_report_v1.md), [diagnostic du format](P1d_format_diagnostic_scientific_report_v1.md).

## La suite

Je dois d'abord obtenir une configuration qui fournisse des réponses évaluables, puis terminer la vérification des mesures et des annotations. Un petit essai Instruct a été préparé, mais le dernier rapport ne contient pas encore de générations avec ce modèle.

L'étude principale reste à faire. Mon matériel limite les essais à plus grande échelle ; les problèmes de mesure et la revue restante doivent aussi être résolus.

À ce stade, je retiens surtout des leçons pour construire l'évaluation : vérifier ce que le score reconnaît, distinguer une phrase vraie d'une tâche réussie et conserver l'incertitude quand la réponse est ambiguë. Je n'en déduis pas encore un effet général du persona.

Le [rapport de décision P1d](P1d_next_scientific_decision_packet_v1.md) précise le prochain essai envisagé et ce qui manque avant l'étude principale.
