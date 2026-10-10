# Leçons

Format : [date] | ce qui a mal tourné | règle pour l'éviter

[2026-10-10] | Le code d'origine faisait la reconnaissance Google avant le test du mot d'activation, donc tout le micro partait en ligne | Tester le mot d'activation en local avant tout envoi réseau.
[2026-10-10] | Les mots-clés par sous-chaîne déclenchaient de fausses commandes ("play" dans "display") | Toujours comparer par mots entiers, sur du texte normalisé sans accents.
[2026-10-10] | Une exception dans une action arrêtait tout le programme | Entourer chaque action d'un try/except et annoncer l'échec à voix haute.
