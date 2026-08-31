# 🤖 Jarvis - Assistant vocal local pour Windows

Assistant vocal 100% gratuit et local, écrit en Python. Dis "Jarvis" suivi d'une commande pour ouvrir des applications, contrôler ton PC, dicter du texte, et plus encore — sans API payante, sans limite d'utilisation.

## ✨ Fonctionnalités

**Ouverture d'applications**
- Chrome, Spotify, YouTube, Bloc-notes, Explorateur de fichiers
- Steam, Discord, Roblox

**Contrôle du PC**
- Éteindre / Redémarrer (avec délai de sécurité + annulation possible)
- Verrouiller / Mettre en veille

**Contrôle média**
- Monter / baisser / couper le son
- Lecture / pause, piste suivante / précédente

**Autres**
- 📸 Capture d'écran vocale ("Jarvis screenshot")
- ✍️ Dictée vocale : Jarvis tape en direct ce que tu dis, dans n'importe quelle fenêtre active
- 🔍 Recherche web instantanée ("Jarvis cherche...")

## 🛠️ Technologies utilisées

- **Python 3.11**
- **SpeechRecognition** — reconnaissance vocale (via Google Web Speech API, gratuite)
- **PyAudio** — capture du micro
- **PyAutoGUI** — simulation clavier/souris pour la dictée, les screenshots et le contrôle média

## 📦 Installation

### 1. Prérequis
- Python 3.11 installé ([python.org](https://www.python.org/downloads/))
- Un micro fonctionnel

### 2. Cloner le projet
```bash
git clone https://github.com/ton-pseudo/jarvis-assistant-vocal.git
cd jarvis-assistant-vocal
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

> 💡 Si l'installation de `pyaudio` échoue sous Windows :
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### 4. Lancer Jarvis
```bash
python jarvis.py
```

## 🎙️ Utilisation

Dis simplement **"Jarvis"** suivi d'une commande, en une seule phrase ou en deux temps :

```
"Jarvis ouvre chrome"
```
ou
```
"Jarvis"  →  (attends "Oui ? Je t'écoute...")  →  "ouvre chrome"
```

### Liste des commandes

| Commande vocale | Action |
|---|---|
| `ouvre chrome / spotify / youtube / bloc-notes / explorateur` | Ouvre l'application |
| `ouvre steam / discord / roblox` | Ouvre l'application |
| `écris` / `dictée` | Active le mode dictée vocale (dire "stop" ou "arrête" pour arrêter) |
| `cherche [quelque chose]` | Lance une recherche Google |
| `screenshot` | Prend une capture d'écran |
| `monte le son` / `baisse le son` / `coupe le son` | Contrôle du volume |
| `pause` | Lecture / pause de la musique |
| `piste suivante` / `piste précédente` | Navigation musicale |
| `verrouille` | Verrouille le PC |
| `veille` | Met le PC en veille |
| `éteins` | Éteint le PC (délai de 10s) |
| `redémarre` | Redémarre le PC (délai de 10s) |
| `annule` | Annule une extinction/redémarrage en cours |

## 🚀 Lancement automatique au démarrage de Windows

Un fichier `lancer_jarvis.bat` est inclus. Pour que Jarvis se lance à chaque démarrage de ton PC :

1. Place `lancer_jarvis.bat` dans le même dossier que `jarvis.py`
2. Ouvre le dossier de démarrage Windows : `Windows + R` → tape `shell:startup`
3. Copie un raccourci de `lancer_jarvis.bat` dans ce dossier

## 🔧 Personnalisation

Toutes les commandes sont centralisées dans la liste `COMMANDES` du fichier `jarvis.py`. Pour ajouter une nouvelle commande, il suffit d'ajouter une fonction et une ligne dans cette liste :

```python
def ma_nouvelle_action():
    print("[Action] Faire quelque chose...")
    # ton code ici

COMMANDES = [
    # ...
    (["mon mot-clé"], ma_nouvelle_action),
]
```

## ⚠️ Limitations connues

- Nécessite une connexion internet (utilise l'API de reconnaissance vocale de Google)
- La reconnaissance vocale peut être imprécise avec un accent marqué, du bruit de fond, ou des noms propres peu communs
- Testé uniquement sur Windows

## 📄 Licence

Projet personnel, libre d'utilisation et de modification.
