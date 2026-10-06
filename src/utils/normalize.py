import re
import unicodedata

_NON_ALNUM = re.compile(r"[\W_]+")


def normalize_word(text: str) -> str:
    """Canonical form used for storing and comparing vocabulary words.

    Unicode compatibility normalization, lowercase, then every character
    that is not a letter or digit is removed, so "TP-Link", "tp-link" and
    "TPLink" all become "tplink". Cyrillic letters are kept as they are.
    """
    text = unicodedata.normalize("NFKC", text).casefold()
    return _NON_ALNUM.sub("", text)


def normalize_title_words(title: str) -> set[str]:
    """Normalized forms of every word in a title.

    Each whitespace separated word is included whole and also split on
    punctuation, so "Dolce-Gusto" yields "dolcegusto", "dolce" and "gusto".
    Empty results, for example from a lone "-", are left out.
    """
    forms: set[str] = set()
    for raw in title.split():
        forms.add(normalize_word(raw))
        for part in _NON_ALNUM.split(unicodedata.normalize("NFKC", raw)):
            forms.add(normalize_word(part))
    forms.discard("")
    return forms