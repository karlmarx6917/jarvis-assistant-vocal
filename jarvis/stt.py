"""Reconnaissance vocale locale avec faster-whisper (GPU NVIDIA, repli CPU)."""

from __future__ import annotations

import logging
import os
import sys
from typing import Optional

import numpy as np

from .config import Config

log = logging.getLogger(__name__)

# Phrases que Whisper invente sur du silence ou du bruit.
_HALLUCINATIONS = (
    "sous-titrage",
    "sous-titres",
    "merci d'avoir regardé",
    "merci d'avoir regarde",
    "abonnez-vous",
    "amara.org",
)


def register_cuda_dlls() -> None:
    """Windows : rend visibles les DLL cuBLAS/cuDNN installées par pip (paquets nvidia-*)."""
    if sys.platform != "win32" or not hasattr(os, "add_dll_directory"):
        return
    try:
        import nvidia  # type: ignore[import-not-found]
    except ImportError:
        return
    for base in getattr(nvidia, "__path__", []):
        for name in os.listdir(base):
            bin_dir = os.path.join(base, name, "bin")
            if os.path.isdir(bin_dir):
                os.add_dll_directory(bin_dir)
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")


def is_hallucination(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _HALLUCINATIONS)


class Transcriber:
    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self._model = self._load()

    def _load(self):
        register_cuda_dlls()
        from faster_whisper import WhisperModel

        wanted = [("cuda", "float16"), ("cpu", "int8")] if self._cfg.device == "auto" else [
            (self._cfg.device, "float16" if self._cfg.device == "cuda" else "int8")
        ]
        silence = np.zeros(16000, dtype=np.float32)
        last_error: Optional[Exception] = None
        for device, default_type in wanted:
            compute = default_type if self._cfg.compute_type == "auto" else self._cfg.compute_type
            try:
                log.info("Chargement de Whisper '%s' sur %s (%s)...", self._cfg.whisper_model, device, compute)
                model = WhisperModel(self._cfg.whisper_model, device=device, compute_type=compute)
                # Les bibliothèques CUDA manquantes ne se plaignent qu'à la première inférence.
                list(model.transcribe(silence, language=self._cfg.language, beam_size=1)[0])
                log.info("Whisper prêt sur %s.", device)
                return model
            except Exception as exc:  # noqa: BLE001 - on veut retomber sur le CPU quoi qu'il arrive
                last_error = exc
                log.warning("Whisper sur %s indisponible : %s", device, exc)
        raise RuntimeError(f"Impossible de charger Whisper : {last_error}")

    def transcribe(self, audio: np.ndarray) -> str:
        """Texte reconnu (chaîne vide si rien d'intelligible)."""
        segments, _ = self._model.transcribe(
            audio,
            language=self._cfg.language,
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=f"{self._cfg.wake_word.capitalize()}, ouvre Chrome. Jarvis, monte le son.",
        )
        text = " ".join(s.text.strip() for s in segments).strip()
        return "" if is_hallucination(text) else text
