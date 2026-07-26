"""Name normalization — the foundation under all fuzzy matching.

Legacy ERP spells one person five ways: "Paul Jonas", "Jonas, Paul",
"P. Jonas", "PAUL JONAS", "Юрий Ковалёв". Before comparing anything we
bring every string to one canonical shape: transliterated to Latin
(unidecode), lowercased, punctuation stripped, whitespace collapsed.
"""

import re

from unidecode import unidecode

_PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")


# Cross-language transliteration folds. The same Slavic name arrives as
# "Kovalev" (English), "Kowaljow" (German) or "Ковалёв" (Cyrillic via
# unidecode). Folding w->v and j->y makes these spellings comparable.
# Applied to BOTH sides of every comparison, so it only affects matching,
# never the stored data.
_TRANSLIT_FOLDS = str.maketrans({"w": "v", "j": "y"})


def normalize(text: str) -> str:
    """Transliterate -> lowercase -> fold -> strip punctuation -> collapse."""
    latin = unidecode(text)
    lowered = latin.lower().translate(_TRANSLIT_FOLDS)
    no_punctuation = _PUNCTUATION.sub(" ", lowered)
    return _WHITESPACE.sub(" ", no_punctuation).strip()


def initials_compatible(candidate: str, target: str) -> bool:
    """True when `candidate` is an initials form of `target`.

    "p jonas" vs "paul jonas" -> True. Fuzzy ratios undervalue initials
    (one letter against a full first name), so this rule handles them.
    """
    candidate_tokens = candidate.split()
    target_tokens = target.split()
    if len(candidate_tokens) != len(target_tokens):
        return False
    for candidate_token, target_token in zip(candidate_tokens, target_tokens, strict=True):
        if candidate_token == target_token:
            continue
        if len(candidate_token) == 1 and target_token.startswith(candidate_token):
            continue
        return False
    return True
