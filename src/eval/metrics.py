"""Precision / recall / F1 for the binary relevance classifier.

Positive class = `relevant`. The eval frame is small (10-30 bulletins) so we
care more about exposing the confusion matrix than about confidence intervals.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass
class ClassificationMetrics:
    total: int
    labeled: int
    skipped_unlabeled: int

    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int

    precision: float | None  # None when no positive predictions
    recall: float | None     # None when no positive labels
    f1: float | None
    accuracy: float | None

    def as_dict(self) -> dict:
        return asdict(self)


def compute_metrics(
    pairs: Iterable[tuple[str | None, bool | None]],
) -> ClassificationMetrics:
    """Compute metrics from an iterable of (expected_label, predicted_relevant) pairs.

    expected_label is the frontmatter string ("relevant" / "not_relevant") or
    None when the bulletin is unlabeled — those are skipped.
    predicted_relevant is the bool Stage-2 output, or None if classification
    errored (counted as a miss only if the expected label is `relevant`).
    """
    tp = fp = tn = fn = 0
    total = 0
    skipped = 0

    for expected, predicted in pairs:
        total += 1
        if expected not in ("relevant", "not_relevant"):
            skipped += 1
            continue
        expected_pos = expected == "relevant"
        # Failed classifications count against the model: a missed `relevant`
        # is a false negative, and (charitably) a missed `not_relevant` is a
        # true negative — declining to act on noise is correct behaviour.
        predicted_pos = bool(predicted) if predicted is not None else False

        if expected_pos and predicted_pos:
            tp += 1
        elif expected_pos and not predicted_pos:
            fn += 1
        elif not expected_pos and predicted_pos:
            fp += 1
        else:
            tn += 1

    labeled = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = None
    accuracy = (tp + tn) / labeled if labeled else None

    return ClassificationMetrics(
        total=total,
        labeled=labeled,
        skipped_unlabeled=skipped,
        true_positive=tp,
        false_positive=fp,
        true_negative=tn,
        false_negative=fn,
        precision=precision,
        recall=recall,
        f1=f1,
        accuracy=accuracy,
    )
