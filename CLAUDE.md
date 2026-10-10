# Jarvis — assistant vocal local (Windows)

## Démarrage de session
1. Lire `tasks/lessons.md` et appliquer les leçons.
2. Lire `tasks/todo.md` pour l'état courant.
3. Lire ce fichier.

## Projet
- Paquet `jarvis/` : `audio` (micro + segmentation), `stt` (faster-whisper), `tts` (pyttsx3),
  `matcher` (logique pure), `commands` (actions), `app` (boucle), `config` (config.toml).
- Lancer : `python -m jarvis` (ou `lancer_jarvis.bat`). Réglages dans `config.toml`.
- Tests : `python -m pytest` (aucun micro ni GPU requis).

## Règles
- `matcher.py` et `audio.Segmenter` restent purs et testables, sans import matériel.
- Imports lourds (sounddevice, pyautogui, pyttsx3, faster_whisper) faits à l'usage, pas au chargement du module.
- Aucune entrée vocale n'est passée à un shell : arguments en liste, jamais `shell=True`.
- Windows uniquement pour les actions système. Les tests doivent passer sous Linux.
