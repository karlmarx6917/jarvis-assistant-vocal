"""
Jarvis - Assistant vocal local pour Windows
100% gratuit, aucune API payante.

Fonctionnement :
1. Écoute le micro en continu.
2. Détecte le mot d'activation "jarvis".
3. Écoute la commande qui suit.
4. Exécute l'action correspondante (pattern matching simple).
"""

import os
import time
import glob
import subprocess
import webbrowser
import speech_recognition as sr

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------

WAKE_WORD = "jarvis"

# Délai de sécurité (en secondes) avant extinction/redémarrage,
# pour pouvoir annuler en cas de fausse détection.
SHUTDOWN_DELAY = 10

recognizer = sr.Recognizer()
microphone = sr.Microphone()


# ----------------------------------------------------------------------
# FONCTIONS D'ACTION (ce que Jarvis peut faire)
# ----------------------------------------------------------------------

def ouvrir_chrome():
    print("[Action] Ouverture de Chrome...")
    os.startfile("chrome")


def ouvrir_spotify():
    print("[Action] Ouverture de Spotify...")
    os.startfile("spotify")


def ouvrir_youtube():
    print("[Action] Ouverture de YouTube...")
    webbrowser.open("https://youtube.com")


def ouvrir_bloc_notes():
    print("[Action] Ouverture du Bloc-notes...")
    os.startfile("notepad")


def ouvrir_explorateur():
    print("[Action] Ouverture de l'explorateur de fichiers...")
    os.startfile("explorer")


def ouvrir_steam():
    print("[Action] Ouverture de Steam...")
    # Le protocole steam:// fonctionne si Steam est installé (il l'enregistre automatiquement)
    chemins_possibles = [
        r"C:\Program Files (x86)\Steam\Steam.exe",
        r"C:\Program Files\Steam\Steam.exe",
    ]
    for chemin in chemins_possibles:
        if os.path.exists(chemin):
            subprocess.Popen([chemin])
            return
    # Solution de secours : protocole Steam
    os.system('start "" "steam://open/main"')


def ouvrir_discord():
    print("[Action] Ouverture de Discord...")
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    update_exe = os.path.join(local_appdata, "Discord", "Update.exe")
    if os.path.exists(update_exe):
        subprocess.Popen([update_exe, "--processStart", "Discord.exe"])
    else:
        # Solution de secours : protocole Discord
        os.system('start "" "discord://"')


def ouvrir_roblox():
    print("[Action] Ouverture de Roblox...")
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    motif = os.path.join(local_appdata, "Roblox", "Versions", "*", "RobloxPlayerBeta.exe")
    correspondances = glob.glob(motif)
    if correspondances:
        subprocess.Popen([correspondances[0]])
    else:
        # Solution de secours : ouvre le site Roblox dans le navigateur
        webbrowser.open("https://www.roblox.com/games")


def eteindre_pc():
    print(f"[Action] Extinction du PC dans {SHUTDOWN_DELAY} secondes...")
    print("         Dis 'jarvis annule' pour annuler.")
    os.system(f"shutdown /s /t {SHUTDOWN_DELAY}")


def annuler_extinction():
    print("[Action] Annulation de l'extinction/redémarrage.")
    os.system("shutdown /a")


def redemarrer_pc():
    print(f"[Action] Redémarrage du PC dans {SHUTDOWN_DELAY} secondes...")
    print("         Dis 'jarvis annule' pour annuler.")
    os.system(f"shutdown /r /t {SHUTDOWN_DELAY}")


def verrouiller_pc():
    print("[Action] Verrouillage du PC...")
    os.system("rundll32.exe user32.dll,LockWorkStation")


def mettre_en_veille():
    print("[Action] Mise en veille du PC...")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")


# ----------------------------------------------------------------------
# TABLE DES COMMANDES (mot-clé -> fonction)
# Ajoute simplement une ligne ici pour ajouter une nouvelle commande.
# ----------------------------------------------------------------------

COMMANDES = [
    (["chrome"], ouvrir_chrome),
    (["spotify"], ouvrir_spotify),
    (["youtube"], ouvrir_youtube),
    (["bloc-notes", "bloc note", "notepad"], ouvrir_bloc_notes),
    (["explorateur", "fichiers"], ouvrir_explorateur),
    (["steam"], ouvrir_steam),
    (["discord"], ouvrir_discord),
    (["roblox"], ouvrir_roblox),
    (["éteins", "eteins", "shutdown", "arrête le pc", "arrete le pc"], eteindre_pc),
    (["annule", "stop shutdown", "annuler"], annuler_extinction),
    (["redémarre", "redemarre", "restart"], redemarrer_pc),
    (["verrouille", "lock"], verrouiller_pc),
    (["veille", "sleep"], mettre_en_veille),
]


def executer_commande(texte):
    """Compare le texte reconnu aux mots-clés et exécute l'action trouvée."""
    texte = texte.lower()
    for mots_cles, action in COMMANDES:
        for mot in mots_cles:
            if mot in texte:
                action()
                return
    print(f"[Info] Commande non reconnue : '{texte}'")


# ----------------------------------------------------------------------
# BOUCLE PRINCIPALE D'ÉCOUTE
# ----------------------------------------------------------------------

def ecouter_et_transcrire(timeout=5, phrase_time_limit=5):
    """Écoute le micro et renvoie le texte transcrit (ou None si échec)."""
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            return None

    try:
        texte = recognizer.recognize_google(audio, language="fr-FR")
        return texte
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"[Erreur] Problème avec le service de reconnaissance : {e}")
        return None


def main():
    print("=" * 50)
    print("  Jarvis est prêt. Dis 'Jarvis' pour l'activer.")
    print("  (Ctrl+C pour quitter le programme)")
    print("=" * 50)

    while True:
        texte = ecouter_et_transcrire(timeout=None, phrase_time_limit=4)

        if texte is None:
            continue

        print(f"[Écouté] {texte}")

        if WAKE_WORD in texte.lower():
            print("[Jarvis] Oui ? Je t'écoute...")

            # On isole ce qui suit "jarvis" si dit dans la même phrase
            reste = texte.lower().split(WAKE_WORD, 1)[1].strip()

            if reste:
                executer_commande(reste)
            else:
                # Rien après "jarvis" dans la même phrase : on écoute la commande séparément
                commande = ecouter_et_transcrire(timeout=5, phrase_time_limit=5)
                if commande:
                    print(f"[Commande] {commande}")
                    executer_commande(commande)
                else:
                    print("[Info] Aucune commande détectée.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Jarvis] Arrêt du programme. À bientôt !")
