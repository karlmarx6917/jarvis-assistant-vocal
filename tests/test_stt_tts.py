from types import SimpleNamespace

from jarvis.stt import is_hallucination
from jarvis.tts import pick_french_voice


def voice(id, name, languages=()):
    return SimpleNamespace(id=id, name=name, languages=list(languages))


def test_hallucinations_are_filtered():
    assert is_hallucination("Sous-titrage ST' 501")
    assert is_hallucination("Merci d'avoir regardé cette vidéo !")
    assert not is_hallucination("Jarvis ouvre Chrome")


def test_picks_french_voice_by_name():
    voices = [voice("HKEY_..._EN-US_ZIRA_11.0", "Microsoft Zira Desktop - English (United States)"),
              voice("HKEY_..._FR-FR_HORTENSE_11.0", "Microsoft Hortense Desktop - French")]
    assert pick_french_voice(voices) == "HKEY_..._FR-FR_HORTENSE_11.0"


def test_picks_french_voice_by_language_bytes():
    assert pick_french_voice([voice("v1", "X", [b"fr_FR"])]) == "v1"


def test_no_french_voice():
    assert pick_french_voice([voice("v1", "Microsoft David - English")]) is None
