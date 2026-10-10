"""Actions de Jarvis et table des commandes vocales."""

from __future__ import annotations

import glob
import logging
import os
import subprocess
import time
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Protocol
from urllib.parse import quote_plus

from .config import Config
from .matcher import is_yes, match, starts_with_any

log = logging.getLogger(__name__)


class Context(Protocol):
    """Ce dont les actions ont besoin : config, parole, et écoute d'une réponse."""

    cfg: Config

    def say(self, text: str) -> None: ...

    def hear(self, timeout: Optional[float] = None) -> Optional[str]: ...


# ----------------------------------------------------------------------
# Outils
# ----------------------------------------------------------------------

def _gui():
    """pyautogui est importé à l'usage : il exige un écran et n'existe pas sur les serveurs de test."""
    import pyautogui

    return pyautogui


def _run(*args: str) -> None:
    """Lance une commande système sans shell : rien de ce qui est dit n'y est interprété."""
    subprocess.run(list(args), check=True)


def build_search_url(query: str) -> str:
    return "https://www.google.com/search?q=" + quote_plus(query)


# ----------------------------------------------------------------------
# Applications
# ----------------------------------------------------------------------

def ouvrir_chrome(ctx: Context, _: str) -> None:
    ctx.say("J'ouvre Chrome.")
    os.startfile("chrome")  # type: ignore[attr-defined]


def ouvrir_spotify(ctx: Context, _: str) -> None:
    ctx.say("J'ouvre Spotify.")
    os.startfile("spotify")  # type: ignore[attr-defined]


def ouvrir_youtube(ctx: Context, _: str) -> None:
    ctx.say("J'ouvre YouTube.")
    webbrowser.open("https://youtube.com")


def ouvrir_bloc_notes(ctx: Context, _: str) -> None:
    ctx.say("J'ouvre le Bloc-notes.")
    os.startfile("notepad")  # type: ignore[attr-defined]


def ouvrir_explorateur(ctx: Context, _: str) -> None:
    ctx.say("J'ouvre l'explorateur de fichiers.")
    os.startfile("explorer")  # type: ignore[attr-defined]


def ouvrir_steam(ctx: Context, _: str) -> None:
    ctx.say("J'ouvre Steam.")
    for chemin in (r"C:\Program Files (x86)\Steam\Steam.exe", r"C:\Program Files\Steam\Steam.exe"):
        if os.path.exists(chemin):
            subprocess.Popen([chemin])
            return
    os.startfile("steam://open/main")  # type: ignore[attr-defined]


def ouvrir_discord(ctx: Context, _: str) -> None:
    ctx.say("J'ouvre Discord.")
    update_exe = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Discord", "Update.exe")
    if os.path.exists(update_exe):
        subprocess.Popen([update_exe, "--processStart", "Discord.exe"])
    else:
        os.startfile("discord://")  # type: ignore[attr-defined]


def ouvrir_roblox(ctx: Context, _: str) -> None:
    ctx.say("J'ouvre Roblox.")
    motif = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Roblox", "Versions", "*", "RobloxPlayerBeta.exe")
    trouves = glob.glob(motif)
    if trouves:
        subprocess.Popen([trouves[0]])
    else:
        webbrowser.open("https://www.roblox.com/games")


# ----------------------------------------------------------------------
# Web, dictée, captures
# ----------------------------------------------------------------------

def rechercher_web(ctx: Context, requete: str) -> None:
    if not requete:
        ctx.say("Dis-moi ce que je dois chercher.")
        return
    ctx.say(f"Je cherche {requete}.")
    webbrowser.open(build_search_url(requete))


def _taper(texte: str) -> None:
    """Colle le texte via le presse-papiers : les accents passent, contrairement à pyautogui.write."""
    import pyperclip

    precedent = None
    try:
        precedent = pyperclip.paste()
    except Exception:  # noqa: BLE001 - presse-papiers illisible : on n'essaie pas de le restaurer
        pass
    pyperclip.copy(texte + " ")
    _gui().hotkey("ctrl", "v")
    time.sleep(0.15)
    if precedent is not None:
        pyperclip.copy(precedent)


def mode_dictee(ctx: Context, _: str) -> None:
    ctx.say("Dictée activée. Clique dans la fenêtre où écrire. Dis stop pour arrêter.")
    time.sleep(1)
    dernier_son = time.monotonic()
    while time.monotonic() - dernier_son < ctx.cfg.dictation_idle_s:
        texte = ctx.hear(timeout=2)
        if not texte:
            continue
        dernier_son = time.monotonic()
        if starts_with_any(texte, ctx.cfg.stop_words):
            ctx.say("Dictée terminée.")
            return
        log.info("Dictée : %s", texte)
        _taper(texte)
    ctx.say("Dictée arrêtée, je n'entends plus rien.")


def prendre_screenshot(ctx: Context, _: str) -> None:
    dossier = Path(ctx.cfg.screenshot_dir) if ctx.cfg.screenshot_dir else Path.home() / "Pictures" / "Jarvis_Screenshots"
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / datetime.now().strftime("screenshot_%Y-%m-%d_%H-%M-%S.png")
    _gui().screenshot().save(chemin)
    ctx.say("Capture d'écran enregistrée.")
    log.info("Screenshot : %s", chemin)


# ----------------------------------------------------------------------
# Son et musique
# ----------------------------------------------------------------------

def _touches(touche: str, fois: int = 1) -> None:
    gui = _gui()
    for _ in range(fois):
        gui.press(touche)


def monter_le_son(ctx: Context, _: str) -> None:
    _touches("volumeup", 5)
    ctx.say("Volume augmenté.")


def baisser_le_son(ctx: Context, _: str) -> None:
    _touches("volumedown", 5)
    ctx.say("Volume baissé.")


def couper_le_son(ctx: Context, _: str) -> None:
    _touches("volumemute")
    ctx.say("C'est fait.")


def musique_pause(ctx: Context, _: str) -> None:
    _touches("playpause")


def musique_suivante(ctx: Context, _: str) -> None:
    _touches("nexttrack")


def musique_precedente(ctx: Context, _: str) -> None:
    _touches("prevtrack")


# ----------------------------------------------------------------------
# Alimentation
# ----------------------------------------------------------------------

def _confirmer(ctx: Context, question: str) -> bool:
    if not ctx.cfg.confirm_power_actions:
        return True
    ctx.say(question)
    reponse = ctx.hear(timeout=ctx.cfg.command_timeout_s)
    if reponse and is_yes(reponse):
        return True
    ctx.say("D'accord, je ne fais rien.")
    return False


def eteindre_pc(ctx: Context, _: str) -> None:
    if not _confirmer(ctx, "Tu veux vraiment éteindre le PC ? Dis oui pour confirmer."):
        return
    delai = ctx.cfg.shutdown_delay
    _run("shutdown", "/s", "/t", str(delai))
    ctx.say(f"Extinction dans {delai} secondes. Dis Jarvis annule pour arrêter.")


def redemarrer_pc(ctx: Context, _: str) -> None:
    if not _confirmer(ctx, "Tu veux vraiment redémarrer le PC ? Dis oui pour confirmer."):
        return
    delai = ctx.cfg.shutdown_delay
    _run("shutdown", "/r", "/t", str(delai))
    ctx.say(f"Redémarrage dans {delai} secondes. Dis Jarvis annule pour arrêter.")


def annuler_extinction(ctx: Context, _: str) -> None:
    _run("shutdown", "/a")
    ctx.say("Extinction annulée.")


def verrouiller_pc(ctx: Context, _: str) -> None:
    ctx.say("Je verrouille le PC.")
    _run("rundll32.exe", "user32.dll,LockWorkStation")


def mettre_en_veille(ctx: Context, _: str) -> None:
    ctx.say("Mise en veille.")
    # Windows met en hibernation à la place si l'hibernation est activée (comportement connu de cet appel).
    _run("rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0")


# ----------------------------------------------------------------------
# Table des commandes. Pour en ajouter une : une fonction + une ligne ici.
# ----------------------------------------------------------------------

Action = Callable[[Context, str], None]


@dataclass(frozen=True)
class Command:
    nom: str
    phrases: tuple[str, ...]
    action: Action


COMMANDES: tuple[Command, ...] = (
    Command("chrome", ("chrome",), ouvrir_chrome),
    Command("spotify", ("spotify",), ouvrir_spotify),
    Command("youtube", ("youtube",), ouvrir_youtube),
    Command("bloc-notes", ("bloc-notes", "bloc note", "notepad"), ouvrir_bloc_notes),
    Command("explorateur", ("explorateur", "fichiers"), ouvrir_explorateur),
    Command("steam", ("steam",), ouvrir_steam),
    Command("discord", ("discord",), ouvrir_discord),
    Command("roblox", ("roblox",), ouvrir_roblox),
    Command("recherche", ("cherche", "recherche"), rechercher_web),
    Command("dictée", ("écris", "dictée"), mode_dictee),
    Command("screenshot", ("screenshot", "capture d'écran"), prendre_screenshot),
    Command("son+", ("monte le son", "augmente le son", "plus fort"), monter_le_son),
    Command("son-", ("baisse le son", "diminue le son", "moins fort"), baisser_le_son),
    Command("mute", ("coupe le son", "mute", "muet"), couper_le_son),
    Command("suivante", ("piste suivante", "chanson suivante", "musique suivante"), musique_suivante),
    Command("précédente", ("piste précédente", "chanson précédente", "musique précédente"), musique_precedente),
    Command("pause", ("pause", "lecture", "play"), musique_pause),
    Command("éteindre", ("éteins", "arrête le pc"), eteindre_pc),
    Command("annuler", ("annule", "annuler", "stop shutdown"), annuler_extinction),
    Command("redémarrer", ("redémarre", "restart"), redemarrer_pc),
    Command("verrouiller", ("verrouille", "lock"), verrouiller_pc),
    Command("veille", ("veille", "sleep"), mettre_en_veille),
)


def execute(ctx: Context, texte: str, commandes: tuple[Command, ...] = COMMANDES) -> bool:
    """Exécute la commande trouvée dans `texte`. Une action qui échoue n'arrête jamais Jarvis."""
    trouve = match(texte, [(c, c.phrases) for c in commandes])
    if trouve is None:
        log.info("Commande non reconnue : %r", texte)
        ctx.say("Je n'ai pas compris.")
        return False
    log.info("Commande : %s (%r)", trouve.item.nom, texte)
    try:
        trouve.item.action(ctx, trouve.rest)
    except Exception:  # noqa: BLE001 - toute panne d'action doit rester locale
        log.exception("L'action %s a échoué", trouve.item.nom)
        ctx.say("Je n'ai pas réussi à le faire.")
        return False
    return True
