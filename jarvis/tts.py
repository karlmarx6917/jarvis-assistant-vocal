"""Voix de Jarvis (pyttsx3, voix française de Windows)."""

from __future__ import annotations

import logging
from typing import Callable, Optional

log = logging.getLogger(__name__)

_FRENCH_HINTS = ("french", "français", "francais", "fr-fr", "fr_fr", "hortense", "julie", "paul", "denise", "henri")


def pick_french_voice(voices) -> Optional[str]:
    """Identifiant de la première voix française trouvée, sinon None."""
    for voice in voices:
        langs = " ".join(
            l.decode("utf-8", "ignore") if isinstance(l, bytes) else str(l)
            for l in (getattr(voice, "languages", None) or [])
        )
        haystack = f"{voice.id} {voice.name} {langs}".lower()
        if any(hint in haystack for hint in _FRENCH_HINTS):
            return voice.id
    return None


class Speaker:
    """Parle de façon bloquante (le micro est vidé ensuite par l'appelant).

    Si pyttsx3 est indisponible ou désactivé, Jarvis écrit simplement dans la console.
    """

    def __init__(self, enabled: bool = True, rate: int = 185, after_speech: Optional[Callable[[], None]] = None) -> None:
        self._after = after_speech
        self._engine = None
        if not enabled:
            return
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", rate)
            voice = pick_french_voice(engine.getProperty("voices"))
            if voice:
                engine.setProperty("voice", voice)
            else:
                log.warning("Aucune voix française installée : Windows > Paramètres > Heure et langue > Voix.")
            self._engine = engine
        except Exception as exc:  # noqa: BLE001
            log.warning("Synthèse vocale indisponible (%s), réponses en texte seulement.", exc)

    def say(self, text: str) -> None:
        print(f"[Jarvis] {text}")
        if self._engine is None:
            return
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as exc:  # noqa: BLE001
            log.warning("La synthèse vocale a échoué : %s", exc)
        finally:
            if self._after:
                self._after()
