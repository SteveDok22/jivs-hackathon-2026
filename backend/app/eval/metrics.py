"""Metric primitives. Pure functions, no I/O — trivially testable.

These turn raw counts into the numbers the jury sheet rewards:
precision/recall/F1 for detection quality, catch rate for security.
"""

from dataclasses import dataclass


@dataclass
class PRF:
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int


def prf(true_positives: int, false_positives: int, false_negatives: int) -> PRF:
    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives)
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives)
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return PRF(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
    )
