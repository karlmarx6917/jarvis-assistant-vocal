from jarvis.matcher import is_yes, match, normalize, split_wake_word, starts_with_any

TABLE = [
    ("chrome", ["chrome"]),
    ("play", ["pause", "lecture", "play"]),
    ("lock", ["verrouille", "lock"]),
    ("search", ["cherche", "recherche"]),
    ("off", ["éteins", "arrête le pc"]),
    ("louder", ["monte le son", "plus fort"]),
]


def found(text):
    m = match(text, TABLE)
    return m.item if m else None


def test_normalize_strips_accents_and_punctuation():
    assert normalize("Arrête, l'ÉCOUTE !") == "arrete l ecoute"


def test_whole_words_only():
    assert found("jarvis display") is None
    assert found("jarvis block") is None
    assert found("mets play") == "play"
    assert found("verrouille le pc") == "lock"


def test_accents_are_optional():
    assert found("eteins le pc") == "off"
    assert found("éteins le pc") == "off"
    assert found("ARRÊTE LE PC") == "off"


def test_multi_word_phrase():
    assert found("monte le son un peu") == "louder"
    assert found("monte la musique") is None


def test_earliest_match_wins():
    assert found("ouvre chrome et verrouille") == "chrome"


def test_longer_phrase_wins_on_same_position():
    table = [("a", ["ouvre"]), ("b", ["ouvre le"])]
    assert match("ouvre le truc", table).item == "b"


def test_rest_keeps_original_text():
    m = match("Cherche des chats & des chiens à Paris.", TABLE)
    assert m.item == "search"
    assert m.rest == "des chats & des chiens à Paris"


def test_recherche_is_its_own_keyword():
    m = match("recherche météo", TABLE)
    assert m.item == "search" and m.rest == "météo"


def test_empty_rest():
    assert match("cherche", TABLE).rest == ""


def test_no_match():
    assert found("bonjour tout le monde") is None
    assert found("") is None


def test_wake_word_exact_and_rest():
    assert split_wake_word("Jarvis, ouvre Chrome", "jarvis") == "ouvre Chrome"
    assert split_wake_word("Jarvis", "jarvis") == ""
    assert split_wake_word("Jarvis.", "jarvis") == ""


def test_wake_word_tolerates_mishearing():
    assert split_wake_word("Harvis ouvre chrome", "jarvis") == "ouvre chrome"
    assert split_wake_word("Jarvice monte le son", "jarvis") == "monte le son"


def test_wake_word_absent():
    assert split_wake_word("le service est ouvert", "jarvis") is None
    assert split_wake_word("travis est là", "jarvis") is None
    assert split_wake_word("", "jarvis") is None


def test_starts_with_any():
    assert starts_with_any("Arrête la dictée", ["arrête", "stop"])
    assert starts_with_any("stop", ["arrête", "stop"])
    assert not starts_with_any("il faut que je m'arrête là", ["arrête", "stop"])
    assert not starts_with_any("", ["stop"])


def test_is_yes():
    assert is_yes("Oui, vas-y")
    assert is_yes("ok")
    assert not is_yes("non")
    assert not is_yes("oui non")
    assert not is_yes("peut-être")
