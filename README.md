# 🤖 Jarvis - Assistant vocal local pour Windows

Assistant vocal en Python. Dis « Jarvis » puis une commande : il ouvre des applications, contrôle le PC et le son, dicte du texte et te répond à voix haute en français.

**Tout reste sur ton PC.** La reconnaissance vocale utilise [Whisper](https://github.com/SYSTRAN/faster-whisper) en local (carte NVIDIA recommandée). Aucun son n'est envoyé sur internet, sauf pour la recherche web que tu demandes.

## ✨ Fonctionnalités

- **Applications** : Chrome, Spotify, YouTube, Bloc-notes, Explorateur, Steam, Discord, Roblox
- **PC** : éteindre / redémarrer (avec confirmation orale, délai et annulation), verrouiller, veille
- **Média** : volume, lecture/pause, piste suivante/précédente
- **Dictée** : Jarvis tape ce que tu dis dans la fenêtre active, accents compris
- **Recherche web** et **capture d'écran**
- **Réponses vocales** en français

## 📦 Installation

Prérequis : Windows, Python 3.11 ou plus, un micro, idéalement une carte NVIDIA avec un pilote à jour. Une voix française doit être installée dans Windows (Paramètres > Heure et langue > Voix).

```bash
git clone https://github.com/karlmarx6917/jarvis-assistant-vocal.git
cd jarvis-assistant-vocal
pip install -r requirements.txt
python -m jarvis
```

Au premier lancement, le modèle Whisper est téléchargé une fois (environ 500 Mo pour `small`).
Sans carte NVIDIA ou si CUDA échoue, Jarvis passe tout seul sur le processeur (plus lent : choisis `base` dans `config.toml`).

## 🎙️ Utilisation

```
"Jarvis, ouvre Chrome"                (une phrase)
"Jarvis" → "Oui ?" → "monte le son"   (deux temps)
```

| Commande vocale | Action |
|---|---|
| `chrome`, `spotify`, `youtube`, `bloc-notes`, `explorateur`, `steam`, `discord`, `roblox` | Ouvre l'application |
| `cherche [sujet]` | Recherche Google |
| `écris` / `dictée` | Dictée, dis « stop » ou « arrête » pour finir |
| `screenshot` | Capture d'écran |
| `monte le son`, `baisse le son`, `coupe le son` | Volume |
| `pause`, `piste suivante`, `piste précédente` | Musique |
| `verrouille`, `veille` | Verrouille / met en veille |
| `éteins`, `redémarre` | Demande confirmation (dis « oui »), puis délai de 10 s |
| `annule` | Annule une extinction ou un redémarrage |

Les mots sont comparés en mots entiers et sans tenir compte des accents : « display » ne déclenche plus « play ».

## 🔧 Configuration

Tout se règle dans `config.toml` : mot d'activation, modèle Whisper (`tiny` à `large-v3`), périphérique (`auto`, `cuda`, `cpu`), délais, voix, confirmation des extinctions. `log_level = "DEBUG"` affiche tout ce que le micro entend. `python -m jarvis --list-devices` liste les micros.

Pour ajouter une commande, écris une fonction dans `jarvis/commands.py` et ajoute une ligne `Command(...)` dans la table `COMMANDES`.

## 🧱 Structure

```
jarvis/
  audio.py     micro + découpage en phrases
  stt.py       Whisper (GPU, repli CPU)
  tts.py       voix française
  matcher.py   texte -> commande (logique pure)
  commands.py  actions et table des commandes
  app.py       boucle principale
  config.py    lecture de config.toml
tests/         pytest, sans micro ni GPU
```

Tests : `python -m pytest`

## 🚀 Lancement au démarrage de Windows

`lancer_jarvis.bat` fonctionne depuis n'importe quel dossier. Ajoute-en un raccourci dans `shell:startup` (touche Windows + R).

## ⚠️ Limites

- Windows uniquement pour les actions système
- Le mot « Jarvis » est détecté par Whisper : chaque phrase est transcrite en local, ce qui utilise un peu le GPU en continu
- Dans une pièce très bruyante ou avec la télé allumée, de fausses détections restent possibles

## 📄 Licence

MIT, voir `LICENSE`.
