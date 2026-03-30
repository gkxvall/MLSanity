from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from mlsanity.types import CheckResult, Sample


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _stable_value(value: Any) -> Any:
    if value is None:
        return None

    try:
        if isinstance(value, float) and math.isnan(value):
            return "__NaN__"
    except TypeError:
        pass

    if isinstance(value, (str, int, float, bool)):
        return value

    return repr(value)


def _stable_features_key(features: dict[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    if not features:
        return tuple()
    return tuple(sorted((str(k), _stable_value(v)) for k, v in features.items()))


def run_image_exact_duplicates_check(samples: list[Sample]) -> CheckResult:
    image_samples = [s for s in samples if s.modality == "image" and s.path is not None]
    hashes_to_ids: dict[str, list[str]] = defaultdict(list)
    unreadable_ids: list[str] = []

    for sample in image_samples:
        path = Path(sample.path)
        try:
            file_hash = _sha256_file(path)
        except OSError:
            unreadable_ids.append(sample.id)
            continue
        hashes_to_ids[file_hash].append(sample.id)

    duplicate_groups = [ids for ids in hashes_to_ids.values() if len(ids) > 1]
    duplicate_groups.sort(key=len, reverse=True)

    duplicates_count = sum(len(group) for group in duplicate_groups)

    if duplicates_count == 0:
        return CheckResult(
            name="duplicates",
            status="ok",
            summary="No exact duplicate images detected.",
            details={
                "total_images": len(image_samples),
                "duplicate_groups": 0,
                "duplicate_images": 0,
                "unreadable_while_hashing": len(unreadable_ids),
            },
            suggestions=[],
        )

    return CheckResult(
        name="duplicates",
        status="warning",
        summary=f"Found {duplicates_count} image(s) that are exact duplicates.",
        details={
            "total_images": len(image_samples),
            "duplicate_groups": len(duplicate_groups),
            "duplicate_images": duplicates_count,
            "groups": duplicate_groups,
            "unreadable_while_hashing": len(unreadable_ids),
            "unreadable_ids": unreadable_ids,
        },
        suggestions=[
            "Remove duplicates to avoid overcounting and biased evaluation.",
            "If duplicates are expected (e.g. data augmentation artifacts), consider de-duplicating within each split.",
        ],
    )


def run_tabular_duplicates_check(samples: list[Sample]) -> CheckResult:
    tab_samples = [s for s in samples if s.modality == "tabular"]

    row_key_to_ids: dict[tuple[Any, Any, tuple[tuple[str, Any], ...]], list[str]] = defaultdict(list)
    features_key_to_labels: dict[tuple[tuple[str, Any], ...], set[str | None]] = defaultdict(set)
    features_key_to_ids: dict[tuple[tuple[str, Any], ...], list[str]] = defaultdict(list)

    for sample in tab_samples:
        features_key = _stable_features_key(sample.features)
        row_key = (sample.label, sample.split, features_key)
        row_key_to_ids[row_key].append(sample.id)

        features_key_to_labels[features_key].add(sample.label)
        features_key_to_ids[features_key].append(sample.id)

    exact_duplicate_row_groups = [ids for ids in row_key_to_ids.values() if len(ids) > 1]
    exact_duplicate_row_groups.sort(key=len, reverse=True)
    exact_duplicate_rows = sum(len(g) for g in exact_duplicate_row_groups)

    same_label_feature_groups: list[list[str]] = []
    conflicting_label_feature_groups: list[list[str]] = []
    for features_key, ids in features_key_to_ids.items():
        if len(ids) <= 1:
            continue
        labels = features_key_to_labels[features_key]
        if len(labels) > 1:
            conflicting_label_feature_groups.append(ids)
        else:
            same_label_feature_groups.append(ids)

    same_label_feature_groups.sort(key=len, reverse=True)
    conflicting_label_feature_groups.sort(key=len, reverse=True)

    duplicate_feature_rows_same_label = sum(len(g) for g in same_label_feature_groups)
    duplicate_feature_rows_conflicting_labels = sum(len(g) for g in conflicting_label_feature_groups)

    total_issues = exact_duplicate_rows + duplicate_feature_rows_conflicting_labels

    if total_issues == 0:
        return CheckResult(
            name="duplicates",
            status="ok",
            summary="No duplicate rows detected.",
            details={
                "total_rows": len(tab_samples),
                "exact_duplicate_row_groups": 0,
                "exact_duplicate_rows": 0,
                "duplicate_feature_rows_same_label": duplicate_feature_rows_same_label,
                "duplicate_feature_rows_conflicting_labels": 0,
            },
            suggestions=[],
        )

    status = "error" if duplicate_feature_rows_conflicting_labels > 0 else "warning"

    return CheckResult(
        name="duplicates",
        status=status,
        summary=(
            f"Found {exact_duplicate_rows} exact-duplicate row(s) and "
            f"{duplicate_feature_rows_conflicting_labels} feature-duplicate row(s) with conflicting labels."
        ),
        details={
            "total_rows": len(tab_samples),
            "exact_duplicate_row_groups": len(exact_duplicate_row_groups),
            "exact_duplicate_rows": exact_duplicate_rows,
            "exact_duplicate_groups": exact_duplicate_row_groups,
            "duplicate_feature_rows_same_label": duplicate_feature_rows_same_label,
            "duplicate_feature_rows_conflicting_labels": duplicate_feature_rows_conflicting_labels,
            "conflicting_feature_groups": conflicting_label_feature_groups,
        },
        suggestions=[
            "Remove exact duplicates to avoid leakage and biased metrics.",
            "Investigate feature-duplicate rows with conflicting labels; they often indicate labeling errors or data joins gone wrong.",
        ],
    )

