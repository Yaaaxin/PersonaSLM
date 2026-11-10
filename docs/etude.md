# Ce que je cherche à comprendre

Le point de départ est simple : ajouter un persona peut rendre une réponse plus personnelle. Je veux savoir ce que cela change pour sa fiabilité.

Par exemple, un personnage peut avoir vécu dans une ville puis déménagé. Le modèle doit tenir compte de la date de la question. Reprendre un détail de l'historique ne suffit pas si ce détail n'est plus valable.

Cet exemple illustre le problème ; les conditions exactes et les réponses attendues sont définies dans chaque jeu de données.

## Trois éléments du contexte

Le premier plan expérimental fait varier :

- **S, le style** : des indications sur la manière de parler.
- **F, les faits personnels** : des informations supplémentaires sur le personnage.
- **H, l'historique** : des échanges contrôlés, avec des dates.

Chaque élément est présent ou absent, ce qui donne huit conditions.

| Condition | Style S | Faits F | Historique H |
| --- | --- | --- | --- |
| C0 | Non | Non | Non |
| C1 | Oui | Non | Non |
| C2 | Non | Oui | Non |
| C3 | Non | Non | Oui |
| C4 | Oui | Oui | Non |
| C5 | Oui | Non | Oui |
| C6 | Non | Oui | Oui |
| C7 | Oui | Oui | Oui |

Dans cette partie de l'étude, toutes les conditions reçoivent les mêmes faits de référence, suffisants pour répondre. Je peux ainsi examiner ce que change l'ajout de contexte personnel.

Une autre question serait de retirer une information nécessaire, ou de ne donner qu'une mémoire périmée. Le protocole prévoit aussi ce type d'étude, mais je le sépare de la première comparaison.

Les essais P1c et P1d utilisent des plans plus ciblés sur l'historique. Le tableau ci-dessus décrit le plan initial, pas toutes les expériences du dépôt.

## Ce que je mesure

| Dimension | Question posée |
| --- | --- |
| Pertinence | La réponse traite-t-elle la dernière demande ? |
| Cohérence factuelle | Ce qu'elle affirme est-il compatible avec les faits de référence ? |
| Cohérence temporelle | Utilise-t-elle les faits valables à la date demandée ? |
| Cohérence conversationnelle | S'accorde-t-elle avec les échanges précédents ? |
| Fidélité au persona | Reprend-elle le style et le comportement attendus ? |

La fidélité au persona reste séparée des autres dimensions. Les essais de développement ne mesurent pas tous cette fidélité.

J'examine aussi si le modèle livre réellement la réponse demandée. Une phrase vraie mais incomplète, une promesse de répondre et une réponse complète ne doivent pas recevoir le même jugement de réussite.

## Comment je compare les réponses

Je compare les conditions sur les mêmes cas. Plusieurs cas peuvent appartenir au même personnage : ils ne représentent donc pas autant de personnes indépendantes.

Les analyses tiennent compte de ces regroupements et des cas incertains. Une réponse « invérifiable » n'est pas automatiquement correcte ou incorrecte. Si la limite de la réponse est ambiguë, je conserve cette incertitude au lieu de choisir silencieusement le morceau de texte le plus favorable.

Les contrôles de longueur servent à examiner l'effet de la quantité de texte. Deux textes de même longueur peuvent cependant différer par leur sens. Les rapports expliquent les différences restantes.

## Ce que ces expériences permettent de dire

Les premiers essais servent à vérifier les tâches et les mesures avant une étude plus grande. Ils reposent sur des personnages fictifs et des configurations précises. Ils ne suffisent pas à conclure sur toutes les personnes, tous les modèles ou toutes les conversations.

Le [protocole](research_protocol_v1.1.md) détaille les hypothèses, les comparaisons et les règles d'analyse. Les [consignes d'annotation](annotation_guidelines.md) donnent les définitions utilisées pour examiner les réponses.
