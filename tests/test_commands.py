import subprocess
import webbrowser

import numpy as np
import pytest

from jarvis import commands
from jarvis.app import Jarvis
from jarvis.commands import COMMANDES, build_search_url, execute
from jarvis.config import Config, load_config
from jarvis.matcher import match


class FakeCtx:
    def __init__(self, replies=(), **cfg):
        self.cfg = Config(**cfg)
        self.said = []
        self._replies = list(replies)

    def say(self, text):
        self.said.append(text)

    def hear(self, timeout=None):
        return self._replies.pop(0) if self._replies else None


@pytest.fixture
def calls(monkeypatch):
    """Intercepte tout ce qui toucherait au système."""
    recorded = []
    monkeypatch.setattr(commands.subprocess, "run", lambda args, **kw: recorded.append(("run", tuple(args))))
    monkeypatch.setattr(commands.webbrowser, "open", lambda url: recorded.append(("web", url)))
    monkeypatch.setattr(commands, "_touches", lambda key, n=1: recorded.append(("key", key, n)))
    return recorded


def test_every_phrase_routes_to_its_own_command():
    table = [(c, c.phrases) for c in COMMANDES]
    for command in COMMANDES:
        for phrase in command.phrases:
            assert match(phrase, table).item is command, phrase


def test_search_url_is_encoded():
    assert build_search_url("chat & chien #1") == "https://www.google.com/search?q=chat+%26+chien+%231"


def test_search_command(calls):
    ctx = FakeCtx()
    assert execute(ctx, "cherche recette de crêpes")
    assert calls == [("web", "https://www.google.com/search?q=recette+de+cr%C3%AApes")]


def test_search_without_query_asks(calls):
    ctx = FakeCtx()
    execute(ctx, "cherche")
    assert calls == [] and "chercher" in ctx.said[0]


def test_volume(calls):
    execute(FakeCtx(), "monte le son")
    assert calls == [("key", "volumeup", 5)]


def test_unrecognized_command(calls):
    ctx = FakeCtx()
    assert not execute(ctx, "il fait beau aujourd'hui")
    assert calls == [] and ctx.said == ["Je n'ai pas compris."]


def test_failing_action_does_not_raise(monkeypatch):
    def boom(ctx, rest):
        raise OSError("introuvable")

    table = (commands.Command("x", ("chrome",), boom),)
    ctx = FakeCtx()
    assert execute(ctx, "chrome", table) is False
    assert ctx.said == ["Je n'ai pas réussi à le faire."]


def test_shutdown_needs_confirmation(calls):
    ctx = FakeCtx(replies=["non"])
    execute(ctx, "éteins le pc")
    assert calls == []


def test_shutdown_silence_means_no(calls):
    execute(FakeCtx(replies=[]), "éteins le pc")
    assert calls == []


def test_shutdown_confirmed_uses_list_args_and_delay(calls):
    execute(FakeCtx(replies=["oui"], shutdown_delay=7), "éteins le pc")
    assert calls == [("run", ("shutdown", "/s", "/t", "7"))]


def test_shutdown_without_confirmation_setting(calls):
    execute(FakeCtx(confirm_power_actions=False), "redémarre")
    assert calls == [("run", ("shutdown", "/r", "/t", "10"))]


def test_cancel(calls):
    execute(FakeCtx(), "annule")
    assert calls == [("run", ("shutdown", "/a"))]


def test_dictation_types_until_stop(monkeypatch):
    typed = []
    monkeypatch.setattr(commands, "_taper", typed.append)
    monkeypatch.setattr(commands.time, "sleep", lambda s: None)
    ctx = FakeCtx(replies=["Bonjour à tous", "c'est l'été", "Stop"])
    execute(ctx, "écris")
    assert typed == ["Bonjour à tous", "c'est l'été"]
    assert ctx.said[-1] == "Dictée terminée."


def test_dictation_stops_when_idle(monkeypatch):
    monkeypatch.setattr(commands.time, "sleep", lambda s: None)
    clock = iter(range(0, 1000, 20))
    monkeypatch.setattr(commands.time, "monotonic", lambda: next(clock))
    ctx = FakeCtx(dictation_idle_s=30)
    execute(ctx, "dictée")
    assert "n'entends plus rien" in ctx.said[-1]


# --- boucle principale avec faux matériel ---

class FakeMic:
    """Micro et transcripteur factices : chaque phrase 'entendue' est déjà du texte."""

    def __init__(self, phrases):
        self.phrases = list(phrases)
        self.flushed = 0

    def listen(self, timeout=None):
        return np.zeros(10, dtype=np.float32) if self.phrases else None

    def transcribe(self, audio):
        return self.phrases.pop(0)

    def flush(self):
        self.flushed += 1


class FakeSpeaker:
    def __init__(self):
        self.said = []

    def say(self, text):
        self.said.append(text)


def make_app(phrases):
    speaker = FakeSpeaker()
    mic = FakeMic(phrases)
    return Jarvis(Config(), mic, mic, speaker), speaker, mic


def test_phrase_without_wake_word_is_ignored(calls):
    app, speaker, _ = make_app(["monte le son"])
    app.step()
    assert calls == [] and speaker.said == []


def test_wake_word_and_command_in_one_phrase(calls):
    app, _, _ = make_app(["Jarvis, monte le son"])
    app.step()
    assert calls == [("key", "volumeup", 5)]


def test_wake_word_then_command_in_two_steps(calls):
    app, speaker, listener = make_app(["Jarvis", "baisse le son"])
    app.step()
    assert speaker.said[0] == "Oui ?"
    assert calls == [("key", "volumedown", 5)]
    assert listener.flushed >= 1


def test_wake_word_alone_then_silence(calls):
    app, speaker, _ = make_app(["Jarvis"])
    app.step()
    assert speaker.said == ["Oui ?", "Je n'ai rien entendu."] and calls == []


# --- config ---

def test_config_defaults_when_file_missing(tmp_path):
    assert load_config(tmp_path / "absent.toml").wake_word == "jarvis"


def test_config_override_and_unknown_key(tmp_path, caplog):
    f = tmp_path / "c.toml"
    f.write_text('wake_word = "friday"\nbogus = 1\n')
    cfg = load_config(f)
    assert cfg.wake_word == "friday" and "bogus" in caplog.text


def test_shipped_config_is_valid():
    cfg = load_config()
    assert cfg.whisper_model == "small" and cfg.confirm_power_actions is True


def test_config_rejects_bad_threshold():
    with pytest.raises(ValueError):
        Config(wake_threshold=2)
