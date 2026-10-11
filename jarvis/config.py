"""Chargement de config.toml (toutes les clés sont facultatives)."""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config.toml"


@dataclass
class Config:
    wake_word: str = "jarvis"
    wake_threshold: float = 0.75
    language: str = "fr"

    whisper_model: str = "small"
    device: str = "auto"
    compute_type: str = "auto"

    sample_rate: int = 16000
    silence_ms: int = 700
    min_speech_ms: int = 250
    max_phrase_s: float = 15.0
    command_timeout_s: float = 6.0
    dictation_idle_s: float = 30.0
    stop_words: list[str] = field(default_factory=lambda: ["arrête", "stop", "termine"])

    shutdown_delay: int = 10
    confirm_power_actions: bool = True
    screenshot_dir: Optional[str] = None

    speak: bool = True
    tts_rate: int = 185

    log_level: str = "INFO"

    def __post_init__(self) -> None:
        if not 0 < self.wake_threshold <= 1:
            raise ValueError("wake_threshold doit être compris entre 0 et 1")
        if self.shutdown_delay < 0:
            raise ValueError("shutdown_delay doit être positif")


def load_config(path: Optional[Path] = None) -> Config:
    """Lit le fichier TOML. Fichier absent : valeurs par défaut. Clé inconnue : avertissement."""
    path = Path(path) if path else DEFAULT_PATH
    if not path.exists():
        log.warning("Fichier de config introuvable (%s), valeurs par défaut utilisées.", path)
        return Config()
    with open(path, "rb") as handle:
        data = tomllib.load(handle)
    known = {f.name for f in fields(Config)}
    for key in sorted(set(data) - known):
        log.warning("Clé inconnue ignorée dans %s : %s", path.name, key)
    return Config(**{k: v for k, v in data.items() if k in known})
