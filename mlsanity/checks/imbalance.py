from __future__ import annotations

from collections import Counter

from mlsanity.types import CheckResult, Sample


def run_class_imbalance_check(
    samples: list[Sample],
    *,
    warning_ratio_threshold: float = 3.0,
    severe_ratio_threshold: float = 10.0,
) -> CheckResult:
    labeled = [s for s in samples if s.label is not None]
    missing_label_count = len(samples) - len(labeled)

    counts = Counter(s.label for s in labeled)
    total_labeled = sum(counts.values())

    if total_labeled == 0:
        return CheckResult(
            name="imbalance",
            status="warning",
            summary="No labeled samples found; cannot compute class imbalance.",
            details={
                "total_samples": len(samples),
                "total_labeled": 0,
                "missing_label_count": missing_label_count,
                "class_counts": {},
                "class_percentages": {},
                "imbalance_ratio": None,
            },
            suggestions=[
                "Ensure labels/targets are present and correctly parsed.",
            ],
        )

    if len(counts) == 1:
        (only_label, only_count) = next(iter(counts.items()))
        status = "warning"
        if missing_label_count > 0:
            status = "warning"
        return CheckResult(
            name="imbalance",
            status=status,
            summary=f"Only one class detected ('{only_label}') across {only_count} labeled sample(s).",
            details={
                "total_samples": len(samples),
                "total_labeled": total_labeled,
                "missing_label_count": missing_label_count,
                "num_classes": 1,
                "class_counts": dict(counts),
                "class_percentages": {only_label: 100.0},
                "imbalance_ratio": None,
            },
            suggestions=[
                "Verify the dataset really contains multiple classes for classification tasks.",
                "If this is expected, ensure your model/training setup matches a single-class scenario.",
            ],
        )

    # Compute percentages and ratio using smallest non-zero class count.
    class_percentages = {k: (v / total_labeled) * 100.0 for k, v in counts.items()}
    sorted_by_count_desc = sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0])))
    sorted_by_count_asc = sorted(counts.items(), key=lambda kv: (kv[1], str(kv[0])))
    max_label, max_count = sorted_by_count_desc[0]
    min_label, min_count = sorted_by_count_asc[0]
    if len(counts) > 1 and max_count == min_count:
        min_label, min_count = sorted_by_count_desc[-1]
    imbalance_ratio = (max_count / min_count) if min_count > 0 else None

    status = "ok"
    if missing_label_count > 0:
        status = "warning"
    if imbalance_ratio is not None:
        if imbalance_ratio >= severe_ratio_threshold:
            status = "warning"
        elif imbalance_ratio >= warning_ratio_threshold:
            status = "warning"

    summary = (
        f"Class imbalance ratio is {imbalance_ratio:.2f} "
        f"(max: '{max_label}'={max_count}, min: '{min_label}'={min_count})."
        if imbalance_ratio is not None
        else "Class imbalance ratio could not be computed."
    )

    suggestions: list[str] = []
    if imbalance_ratio is not None and imbalance_ratio >= warning_ratio_threshold:
        suggestions.append(
            "Consider rebalancing (sampling, class weights) or collecting more data for minority classes."
        )
    if missing_label_count > 0:
        suggestions.append("Investigate missing labels/targets; they can break training and metrics.")

    return CheckResult(
        name="imbalance",
        status=status,
        summary=summary,
        details={
            "total_samples": len(samples),
            "total_labeled": total_labeled,
            "missing_label_count": missing_label_count,
            "num_classes": len(counts),
            "class_counts": dict(counts),
            "class_percentages": class_percentages,
            "imbalance_ratio": imbalance_ratio,
            "max_class": {"label": max_label, "count": max_count},
            "min_class": {"label": min_label, "count": min_count},
            "warning_ratio_threshold": warning_ratio_threshold,
            "severe_ratio_threshold": severe_ratio_threshold,
        },
        suggestions=suggestions,
    )

