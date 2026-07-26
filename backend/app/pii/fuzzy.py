"""Fuzzy search for person names across table cells and free text.

Two matching modes, because the data comes in two shapes:
- CELL: the whole cell is (roughly) a name -> "Jonas, Paul" in KNA1.NAME1.
  Score = best of token_sort / token_set / partial ratios on normalized
  strings, plus the initials rule.
- TEXT: the name hides inside a sentence -> "Payment to Paul Jnoas re
  invoice 84551" in BSEG.SGTXT. token_set_ratio handles containment;
  char-level fuzziness still catches typos.
"""

from dataclasses import dataclass

from rapidfuzz import fuzz

from app.pii.normalize import initials_compatible, normalize


@dataclass
class NameMatch:
    matched_name: str      # canonical form of the target that matched
    score: float           # 0-100
    method: str            # "cell" | "text" | "initials"


def score_cell(cell: str, target: str) -> NameMatch | None:
    """Match when the whole cell is a candidate name."""
    cell_norm = normalize(cell)
    target_norm = normalize(target)
    if not cell_norm:
        return None
    if initials_compatible(cell_norm, target_norm):
        return NameMatch(matched_name=target, score=95.0, method="initials")
    score = max(
        fuzz.token_sort_ratio(cell_norm, target_norm),
        fuzz.token_set_ratio(cell_norm, target_norm),
        fuzz.partial_ratio(cell_norm, target_norm),
    )
    return NameMatch(matched_name=target, score=score, method="cell")


def score_text(text: str, target: str) -> NameMatch | None:
    """Match when the name may be embedded in free text.

    token_set_ratio alone fails on typos inside sentences: the misspelled
    token drops out of the exact-token intersection and the score collapses
    ("Paul Jnoas" in a payment line scored 57). So we also slide a window
    of the target's width across the text and score each window with the
    full cell-grade fuzzy comparison — typos and transliterations survive.
    """
    text_norm = normalize(text)
    target_norm = normalize(target)
    if not text_norm:
        return None
    best = float(fuzz.token_set_ratio(text_norm, target_norm))
    method = "text"
    tokens = text_norm.split()
    width = len(target_norm.split())
    for window_width in (width, width + 1):
        for start in range(max(0, len(tokens) - window_width + 1)):
            window = " ".join(tokens[start : start + window_width])
            if initials_compatible(window, target_norm):
                return NameMatch(matched_name=target, score=95.0, method="initials")
            window_score = max(
                fuzz.token_sort_ratio(window, target_norm),
                fuzz.token_set_ratio(window, target_norm),
            )
            if window_score > best:
                best = window_score
                method = "window"
    return NameMatch(matched_name=target, score=best, method=method)
