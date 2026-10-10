"""Capture du micro et découpage en phrases.

Un seul flux micro reste ouvert. Le seuil de détection suit le bruit ambiant en continu,
il n'y a donc plus de recalibrage (ni de parole perdue) à chaque écoute.
"""

from __future__ import annotations

import logging
import queue
import time
from collections import deque
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)

BLOCK_MS = 32


class Segmenter:
    """Machine à états : reçoit des blocs audio, renvoie une phrase complète quand elle est finie."""

    def __init__(
        self,
        sample_rate: int = 16000,
        silence_ms: int = 700,
        min_speech_ms: int = 250,
        max_phrase_s: float = 15.0,
        preroll_ms: int = 300,
        min_rms: float = 0.012,
        noise_factor: float = 3.0,
    ) -> None:
        self.sample_rate = sample_rate
        self.min_rms = min_rms
        self.noise_factor = noise_factor
        self._silence_blocks = max(1, silence_ms // BLOCK_MS)
        self._min_speech_blocks = max(1, min_speech_ms // BLOCK_MS)
        self._max_blocks = int(max_phrase_s * 1000 // BLOCK_MS)
        self._preroll: deque[np.ndarray] = deque(maxlen=max(1, preroll_ms // BLOCK_MS))
        self.noise_floor = min_rms / noise_factor
        self.reset()

    def reset(self) -> None:
        self._preroll.clear()
        self._phrase: list[np.ndarray] = []
        self._levels: list[float] = []
        self._speech_blocks = 0
        self._quiet_run = 0
        self._active = False

    @property
    def threshold(self) -> float:
        return max(self.min_rms, self.noise_floor * self.noise_factor)

    def feed(self, block: np.ndarray) -> Optional[np.ndarray]:
        """Ajoute un bloc float32 mono. Renvoie la phrase (float32) quand elle est terminée."""
        rms = float(np.sqrt(np.mean(np.square(block)))) if block.size else 0.0
        loud = rms > self.threshold

        if not self._active:
            if not loud:
                # Le bruit de fond suit lentement ce qu'on entend quand personne ne parle.
                self.noise_floor = 0.98 * self.noise_floor + 0.02 * rms
                self._preroll.append(block)
                return None
            self._active = True
            self._phrase = list(self._preroll)
            self._preroll.clear()

        self._phrase.append(block)
        self._levels.append(rms)
        if loud:
            self._speech_blocks += 1
            self._quiet_run = 0
        else:
            self._quiet_run += 1

        too_long = len(self._phrase) >= self._max_blocks
        if self._quiet_run >= self._silence_blocks or too_long:
            phrase = np.concatenate(self._phrase)
            enough = self._speech_blocks >= self._min_speech_blocks
            if too_long and self._quiet_run == 0:
                # Jamais de silence : c'est un bruit continu (ventilateur, télé...), pas une phrase.
                # On relève le niveau de bruit de fond pour ne plus le prendre pour de la parole.
                self.noise_floor = max(self.noise_floor, float(np.median(self._levels)))
            self.reset()
            return phrase if enough else None
        return None


class MicListener:
    """Flux micro en continu (sounddevice) + segmentation."""

    def __init__(self, sample_rate: int, silence_ms: int, min_speech_ms: int, max_phrase_s: float) -> None:
        self.sample_rate = sample_rate
        self._segmenter = Segmenter(sample_rate, silence_ms, min_speech_ms, max_phrase_s)
        self._blocks: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=2000)
        self._stream = None

    def start(self) -> None:
        try:
            import sounddevice as sd
        except (ImportError, OSError) as exc:
            raise RuntimeError(f"sounddevice est indisponible ({exc}). Lance : pip install -r requirements.txt") from exc

        def on_audio(indata, frames, time_info, status) -> None:
            if status:
                log.debug("Audio : %s", status)
            try:
                self._blocks.put_nowait(indata[:, 0].copy())
            except queue.Full:
                pass  # mieux vaut perdre un bloc que bloquer le thread audio

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=self.sample_rate * BLOCK_MS // 1000,
                callback=on_audio,
            )
            self._stream.start()
        except Exception as exc:
            raise RuntimeError(f"Impossible d'ouvrir le micro : {exc}") from exc

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def flush(self) -> None:
        """Jette l'audio en attente (appelé après que Jarvis a parlé, pour qu'il ne s'écoute pas)."""
        while True:
            try:
                self._blocks.get_nowait()
            except queue.Empty:
                break
        self._segmenter.reset()

    def listen(self, timeout: Optional[float] = None) -> Optional[np.ndarray]:
        """Attend une phrase. Renvoie None si rien n'est dit avant `timeout` secondes."""
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            wait = 0.5 if deadline is None else min(0.5, deadline - time.monotonic())
            if wait <= 0:
                return None
            try:
                block = self._blocks.get(timeout=wait)
            except queue.Empty:
                continue
            phrase = self._segmenter.feed(block)
            if phrase is not None:
                return phrase
