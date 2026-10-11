"""Point d'entrée : python -m jarvis"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="jarvis", description="Assistant vocal local (Whisper).")
    parser.add_argument("--config", type=Path, help="chemin d'un config.toml (défaut : celui du projet)")
    parser.add_argument("--list-devices", action="store_true", help="liste les micros disponibles puis quitte")
    args = parser.parse_args(argv)

    if args.list_devices:
        import sounddevice as sd

        print(sd.query_devices())
        return 0

    from .config import load_config

    cfg = load_config(args.config)
    logging.basicConfig(
        level=getattr(logging, cfg.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    from .app import Jarvis
    from .audio import MicListener
    from .stt import Transcriber
    from .tts import Speaker

    listener = MicListener(cfg.sample_rate, cfg.silence_ms, cfg.min_speech_ms, cfg.max_phrase_s)
    try:
        listener.start()  # d'abord : une panne de micro doit se voir avant le chargement du modèle
        transcriber = Transcriber(cfg)
        speaker = Speaker(cfg.speak, cfg.tts_rate, after_speech=listener.flush)
        listener.flush()  # ce qui a été capté pendant le chargement est périmé
    except RuntimeError as exc:
        print(f"[Erreur] {exc}", file=sys.stderr)
        listener.stop()
        return 1

    print("=" * 50)
    print(f"  Dis '{cfg.wake_word.capitalize()}' puis ta commande.  (Ctrl+C pour quitter)")
    print("=" * 50)
    try:
        Jarvis(cfg, listener, transcriber, speaker).run()
    except KeyboardInterrupt:
        print("\n[Jarvis] Arrêt du programme. À bientôt !")
    finally:
        listener.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
