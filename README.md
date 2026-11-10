# PersonaSLM

**Quand un petit modèle adopte un persona, ses réponses restent-elles fiables ?**

J'ai commencé cette petite étude en travaillant sur [MimooPet](https://yaaaxin.itch.io/mimoopet), mon application d'IA locale. Je cherchais à retrouver certaines habitudes de communication dans les réponses du modèle. Assez vite, une autre question est venue : est-ce qu'il répond encore correctement quand on lui ajoute tout ce contexte ?

Ici, je teste ça avec des personnages et des conversations fictifs. Le code et les données sont séparés de MimooPet.

## Ce que je teste

Je fais varier trois choses : le style, les faits personnels et l'historique de conversation. Dans le premier plan à huit conditions, chaque variante reçoit les mêmes faits nécessaires pour répondre.

Je regarde ensuite si la réponse traite la question, respecte les faits et utilise les informations valables à la bonne date. La fidélité au persona reste une mesure à part : bien imiter quelqu'un et donner une réponse fiable, ce n'est pas la même chose.

Le [plan de l'étude](docs/etude.md) explique les comparaisons.

## Ce que j'en retiens pour l'instant

J'ai passé pas mal de temps à vérifier l'évaluation elle-même. Dans le premier pilote, mon vérificateur reconnaissait une réponse simple, mais pouvait manquer la même réponse accompagnée d'une date.

Les essais suivants m'ont aussi montré qu'une phrase vraie ne suffit pas toujours. Sur une série de 192 réponses, 137 ont reçu un jugement factuel positif, mais seulement 110 répondaient complètement et correctement à la demande. Les annotations ont été préparées avec une aide IA puis confirmées par moi, sans deuxième évaluateur indépendant.

J'ai ensuite essayé des chaînes d'arrêt pour empêcher le modèle de continuer toute la conversation. Ça a arrêté la continuation, mais pas amélioré le contenu de la première réponse dans les huit paires testées.

Les [résultats détaillés](docs/resultats.md) reprennent ces essais et leurs limites.

## Où j'en suis

Les essais ont tourné sur CPU avec llama.cpp et Qwen3.5-2B-Base quantifié. Avec mon matériel actuel, j'ai mis la suite à plus grande échelle en pause. Il reste aussi des problèmes de mesure à régler avant l'étude principale.

Un petit essai avec un modèle Instruct est préparé, mais il n'a pas encore été lancé. Je n'ai donc pas encore de conclusion générale sur l'effet du persona.

## Pour aller plus loin

- [Installer et essayer le code](docs/reproduire.md)
- [Lire la documentation](docs/README.md) et retrouver les rapports
- [Se repérer dans le code](src/personaslm/README.md), les [tests](tests/README.md) et les [scripts d'expérience](tools/README.md)
- [Voir les données fictives](data/synthetic/README.md)

J'ai gardé les rapports de travail pour pouvoir revenir sur mes choix et mes erreurs. Les anciennes notes du README sont dans [README.history.md](README.history.md).

Yaxin ZHENG
