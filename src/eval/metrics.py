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
    errored: int  # labeled bulletins whose classification raised — excluded from P/R

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
    predicted_relevant is True / False from Stage 2, or None if the
    classification errored. Errored bulletins are NOT counted toward precision
    or recall — a quota error is an infrastructure failure, not a model
    judgement, and crediting it as a correct TN would inflate the metric.
    They are reported as `errored` so the reviewer sees the true classified
    sample size.
    """
    tp = fp = tn = fn = 0
    total = 0
    skipped = 0
    errored = 0

    for expected, predicted in pairs:
        total += 1
        if expected not in ("relevant", "not_relevant"):
            skipped += 1
            continue
        if predicted is None:
            errored += 1
            continue
        expected_pos = expected == "relevant"
        predicted_pos = bool(predicted)

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
        errored=errored,
        true_positive=tp,
        false_positive=fp,
        true_negative=tn,
        false_negative=fn,
        precision=precision,
        recall=recall,
        f1=f1,
        accuracy=accuracy,
    )
