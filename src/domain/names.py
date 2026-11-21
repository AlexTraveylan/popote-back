import re
import unicodedata

_NON_WORD = re.compile(r"[^a-z0-9]+")
_STOP_WORDS = frozenset({"de", "d", "du", "des", "la", "le", "les", "l", "a", "au", "aux", "en", "et"})


_LIGATURES = str.maketrans({"œ": "oe", "Œ": "oe", "æ": "ae", "Æ": "ae"})


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.translate(_LIGATURES))
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _singular(word: str) -> str:
    if len(word) > 3 and word.endswith(("s", "x")):
        return word[:-1]
    return word


def name_tokens(name: str) -> tuple[str, ...]:
    cleaned = _NON_WORD.sub(" ", _strip_accents(name).lower())
    return tuple(_singular(word) for word in cleaned.split() if word not in _STOP_WORDS)


def normalize_name(name: str) -> str:
    return " ".join(name_tokens(name))


def names_match(wanted: str, candidate: str) -> bool:
    wanted_tokens = set(name_tokens(wanted))
    candidate_tokens = set(name_tokens(candidate))
    if not wanted_tokens or not candidate_tokens:
        return False
    return wanted_tokens <= candidate_tokens
