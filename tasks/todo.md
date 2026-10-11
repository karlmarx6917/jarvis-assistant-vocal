# Todo

Plan complet : voir la description de la branche. État :

- [x] Étape 0 : tasks/lessons.md, tasks/todo.md, CLAUDE.md
- [x] 1. Matcher testable (mots entiers, sans accents, mot d'activation tolérant)
- [x] 2. Écoute locale : Segmenter (seuil adaptatif) + MicListener + faster-whisper GPU avec repli CPU
- [x] 3. Mot d'activation en local
- [x] 4. Voix française (pyttsx3, bloquante, micro vidé ensuite)
- [x] 5. Actions robustes (try/except, confirmation extinction, dictée par presse-papiers)
- [x] 6. config.toml, logging, erreur claire sans micro
- [x] 7. requirements, .gitignore, LICENSE, README, .bat portable

## À valider sur le PC Windows (impossible ici)
- [ ] Vraie transcription Whisper sur la carte NVIDIA (6 Go, modèle large-v3-turbo : vérifier que le nom est accepté par la version installée de faster-whisper, sinon `medium`) (téléchargement du modèle bloqué dans le bac à sable)
- [ ] Voix française pyttsx3
- [ ] Actions système : chrome, extinction + annulation, dictée avec accents
- [ ] Fausses détections avec la télé / un fond sonore, réglage de silence_ms
