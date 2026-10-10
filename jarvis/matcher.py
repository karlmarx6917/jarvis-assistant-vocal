"""Association texte -> commande. Logique pure : aucun accès au micro ni au système."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Generic, Iterable, Optional, Sequence, TypeVar

T = TypeVar("T")

_WORD = re.compile(r"\w+")
_EDGE_PUNCTUATION = " \t\n.,;:!?…-–—\"'«»"


def normalize_word(word: str) -> str:
    """Minuscules et sans accents : « Arrête » -> « arrete »."""
    decomposed = unicodedata.normalize("NFKD", word.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def normalize(text: str) -> str:
    """Texte complet normalisé, mots séparés par un espace."""
    return " ".join(normalize_word(m.group()) for m in _WORD.finditer(text))


@dataclass(frozen=True)
class Token:
    norm: str
    start: int
    end: int


def tokenize(text: str) -> list[Token]:
    return [Token(normalize_word(m.group()), m.start(), m.end()) for m in _WORD.finditer(text)]


def _clean_edges(text: str) -> str:
    return text.strip(_EDGE_PUNCTUATION)


@dataclass(frozen=True)
class Match(Generic[T]):
    item: T
    phrase: str
    rest: str  # ce qui suit l'expression, texte d'origine (accents et ponctuation conservés)


def _find(tokens: Sequence[Token], phrase: Sequence[str]) -> Optional[int]:
    size = len(phrase)
    for i in range(len(tokens) - size + 1):
        if all(tokens[i + j].norm == phrase[j] for j in range(size)):
            return i
    return None


def match(text: str, entries: Iterable[tuple[T, Sequence[str]]]) -> Optional[Match[T]]:
    """Trouve la commande dont une expression apparaît en mots entiers dans le texte.

    Plusieurs correspondances : la plus tôt dans la phrase gagne, puis la plus longue,
    puis l'ordre de la table.
    """
    tokens = tokenize(text)
    best: Optional[tuple[int, int, int, T, str, int]] = None
    for order, (item, phrases) in enumerate(entries):
        for phrase in phrases:
            words = normalize(phrase).split()
            if not words:
                continue
            index = _find(tokens, words)
            if index is None:
                continue
            key = (index, -len(words), order)
            if best is None or key < best[:3]:
                best = (index, -len(words), order, item, phrase, index + len(words) - 1)
    if best is None:
        return None
    _, _, _, item, phrase, last = best
    return Match(item, phrase, _clean_edges(text[tokens[last].end:]))


def split_wake_word(text: str, wake_word: str, threshold: float = 0.75) -> Optional[str]:
    """Si le mot d'activation (ou un mot proche) est présent, renvoie ce qui le suit.

    Renvoie None s'il est absent, et "" s'il est dit seul.
    """
    target = normalize_word(wake_word)
    for token in tokenize(text):
        if SequenceMatcher(None, token.norm, target).ratio() >= threshold:
            return _clean_edges(text[token.end:])
    return None


def starts_with_any(text: str, words: Iterable[str]) -> bool:
    """Vrai si le premier mot du texte fait partie de la liste (mot d'arrêt de la dictée)."""
    tokens = tokenize(text)
    wanted = {normalize_word(w) for w in words}
    return bool(tokens) and tokens[0].norm in wanted


_YES = {"oui", "ouais", "confirme", "confirmer", "ok", "okay", "go", "affirmatif", "accord"}
_NO = {"non", "annule", "annuler", "stop"}


def is_yes(text: str) -> bool:
    words = {t.norm for t in tokenize(text)}
    return bool(words & _YES) and not words & _NO
