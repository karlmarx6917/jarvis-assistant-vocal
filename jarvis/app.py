"""Boucle principale : veille -> mot d'activation -> commande."""

from __future__ import annotations

import logging
import time
from typing import Optional, Protocol

import numpy as np

from .commands import execute
from .config import Config
from .matcher import split_wake_word

log = logging.getLogger(__name__)


class _Listener(Protocol):
    def listen(self, timeout: Optional[float] = None) -> Optional[np.ndarray]: ...
    def flush(self) -> None: ...


class _Transcriber(Protocol):
    def transcribe(self, audio: np.ndarray) -> str: ...


class _Speaker(Protocol):
    def say(self, text: str) -> None: ...


class Jarvis:
    def __init__(self, cfg: Config, listener: _Listener, transcriber: _Transcriber, speaker: _Speaker) -> None:
        self.cfg = cfg
        self._listener = listener
        self._transcriber = transcriber
        self._speaker = speaker

    # --- Context attendu par les commandes ---

    def say(self, text: str) -> None:
        self._speaker.say(text)
        self._listener.flush()  # Jarvis ne doit pas s'entendre lui-même

    def hear(self, timeout: Optional[float] = None) -> Optional[str]:
        audio = self._listener.listen(timeout)
        if audio is None:
            return None
        text = self._transcriber.transcribe(audio)
        if text:
            log.debug("Entendu : %s", text)
        return text or None

    # --- Boucle ---

    def step(self) -> None:
        """Une écoute : traite une phrase si elle commence par le mot d'activation."""
        text = self.hear(timeout=None)
        if not text:
            return
        rest = split_wake_word(text, self.cfg.wake_word, self.cfg.wake_threshold)
        if rest is None:
            return  # pas pour moi : rien n'est conservé ni envoyé nulle part
        if rest:
            execute(self, rest)
            return
        self.say("Oui ?")
        command = self.hear(timeout=self.cfg.command_timeout_s)
        if command:
            execute(self, command)
        else:
            self.say("Je n'ai rien entendu.")

    def run(self) -> None:
        self.say("Jarvis est prêt.")
        failures = 0
        while True:
            try:
                self.step()
                failures = 0
            except KeyboardInterrupt:
                raise
            except Exception:  # noqa: BLE001 - la boucle doit survivre à une erreur isolée
                failures += 1
                log.exception("Erreur dans la boucle d'écoute (%d de suite)", failures)
                time.sleep(min(30, 2 ** min(failures, 5)))
