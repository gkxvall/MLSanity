from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import imagehash
from PIL import Image, UnidentifiedImageError

from mlsanity.types import CheckResult, Sample


@dataclass
class _LabelHintCandidate:
    sample_id: str
    current_label: str | None
    suspected_label: str | None
    score: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "current_label": self.current_label,
            "suspected_label": self.suspected_label,
            "score": self.score,
            "reason": self.reason,
        }


def _quantize_feature_value(value: Any, *, decimals: int = 3) -> Any:
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return "__NaN__"
        return round(value, decimals)
    if isinstance(value, (int, str, bool)):
        return value
    return repr(value)


def _quantize_features_key(features: dict[str, Any] | None, *, decimals: int = 3) -> tuple[tuple[str, Any], ...]:
    if not features:
        return tuple()
    items: list[tuple[str, Any]] = []
    for k, v in features.items():
        items.append((str(k), _quantize_feature_value(v, decimals=decimals)))
    return tuple(sorted(items))


def _most_common_label(labels: Iterable[str]) -> str | None:
    counts: dict[str, int] = {}
    for l in labels:
        counts[l] = counts.get(l, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda kv: (kv[1], str(kv[0])))[0]


def _label_hints_from_tabular_features(
    samples: list[Sample],
    *,
    numeric_quantize_decimals: int = 3,
    max_candidates: int = 50,
) -> list[_LabelHintCandidate]:
    # Group by quantized features to approximate "near-identical" rows.
    # If split exists, keep groups within split to avoid noisy cross-split comparisons.
    groups: dict[tuple[Any, ...], dict[str, list[str]]] = {}

    for s in samples:
        if s.modality != "tabular" or s.features is None:
            continue
        if s.label is None:
            continue

        q_features = _quantize_features_key(s.features, decimals=numeric_quantize_decimals)
        split_key = s.split if s.split is not None else "__NO_SPLIT__"
        group_key = (split_key, q_features)

        label_map = groups.setdefault(group_key, {})
        label_map.setdefault(s.label, []).append(s.id)

    candidates: list[_LabelHintCandidate] = []

    for (_split_key, _q_features), label_map in groups.items():
        if len(label_map) <= 1:
            continue

        likely_label = _most_common_label(label_map.keys())
        if likely_label is None:
            continue

        labeled_count = sum(len(ids) for ids in label_map.values())
        for current_label, ids in label_map.items():
            if current_label == likely_label:
                continue

            other_count = len(ids)
            likely_count = len(label_map.get(likely_label, []))

            # Suspicion is higher when current label is a minority inside a near-identical feature group.
            score = 100.0 * (1.0 - (other_count / labeled_count)) if labeled_count else 0.0
            reason = (
                "Near-identical features (quantized) appear with conflicting labels "
                f"in the same group; likely label is '{likely_label}'."
            )

            for sid in ids:
                candidates.append(
                    _LabelHintCandidate(
                        sample_id=sid,
                        current_label=current_label,
                        suspected_label=likely_label,
                        score=round(score, 4),
                        reason=reason,
                    )
                )

    # Rank by score descending, then stable by sample_id.
    candidates.sort(key=lambda c: (-c.score, c.sample_id))
    return candidates[:max_candidates]


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]


def _label_hints_from_image_hash(
    samples: list[Sample],
    *,
    hash_distance_threshold: int = 5,
    hash_size: int = 8,
    max_images: int = 2500,
    max_candidates: int = 50,
) -> list[_LabelHintCandidate]:
    image_samples = [s for s in samples if s.modality == "image" and s.path is not None]
    if len(image_samples) == 0:
        return []

    if len(image_samples) > max_images:
        image_samples = image_samples[:max_images]

    labels = [s.label for s in image_samples]

    hash_by_index: list[imagehash.ImageHash | None] = [None] * len(image_samples)
    unreadable_ids: list[str] = []
    for i, s in enumerate(image_samples):
        try:
            with Image.open(Path(s.path)) as img:
                img = img.convert("RGB")
                hash_by_index[i] = imagehash.phash(img, hash_size=hash_size)
        except (UnidentifiedImageError, OSError, ValueError):
            unreadable_ids.append(s.id)

    n = len(image_samples)
    uf = _UnionFind(n)
    valid_indices = [i for i in range(n) if hash_by_index[i] is not None]

    # Connect near-duplicate images (pHash distance <= threshold).
    for idx_a, a in enumerate(valid_indices):
        h_a = hash_by_index[a]
        if h_a is None:
            continue
        for b in valid_indices[idx_a + 1 :]:
            h_b = hash_by_index[b]
            if h_b is None:
                continue
            if int(h_a - h_b) <= hash_distance_threshold:
                uf.union(a, b)

    # Build connected components and detect label conflicts inside them.
    comp_to_indices: dict[int, list[int]] = {}
    for i in range(n):
        root = uf.find(i)
        comp_to_indices.setdefault(root, []).append(i)

    candidates: list[_LabelHintCandidate] = []
    for comp_indices in comp_to_indices.values():
        # Determine conflicting labels in this component.
        comp_labels = [labels[i] for i in comp_indices if labels[i] is not None]
        if len(set(comp_labels)) <= 1:
            continue

        likely_label = _most_common_label(comp_labels)
        if likely_label is None:
            continue

        labeled_count = len(comp_labels)
        likely_count = sum(1 for l in comp_labels if l == likely_label)

        for i in comp_indices:
            current_label = labels[i]
            if current_label is None or current_label == likely_label:
                continue

            other_count = sum(1 for l in comp_labels if l == current_label)
            score = 100.0 * (1.0 - (other_count / labeled_count)) if labeled_count else 0.0
            reason = (
                "Near-identical images (pHash grouping) share similar appearance but have conflicting labels "
                f"in the same group; likely label is '{likely_label}'."
            )

            candidates.append(
                _LabelHintCandidate(
                    sample_id=image_samples[i].id,
                    current_label=current_label,
                    suspected_label=likely_label,
                    score=round(score, 4),
                    reason=reason,
                )
            )

    candidates.sort(key=lambda c: (-c.score, c.sample_id))
    _ = unreadable_ids  # reserved for potential future detail
    return candidates[:max_candidates]


def run_label_hints_check(
    samples: list[Sample],
    *,
    image_hash_distance_threshold: int = 5,
    image_hash_size: int = 8,
    image_max_images: int = 2500,
    tabular_numeric_quantize_decimals: int = 3,
    max_candidates: int = 50,
) -> CheckResult:
    image_samples = [s for s in samples if s.modality == "image"]
    tabular_samples = [s for s in samples if s.modality == "tabular"]

    candidates: list[_LabelHintCandidate] = []

    if image_samples:
        candidates.extend(
            _label_hints_from_image_hash(
                samples,
                hash_distance_threshold=image_hash_distance_threshold,
                hash_size=image_hash_size,
                max_images=image_max_images,
                max_candidates=max_candidates,
            )
        )

    if tabular_samples:
        candidates.extend(
            _label_hints_from_tabular_features(
                samples,
                numeric_quantize_decimals=tabular_numeric_quantize_decimals,
                max_candidates=max_candidates,
            )
        )

    if not candidates:
        return CheckResult(
            name="label_hints",
            status="ok",
            summary="No suspicious label candidates detected (heuristic hints).",
            details={
                "candidate_count": 0,
                "image_hash_distance_threshold": image_hash_distance_threshold,
                "image_hash_size": image_hash_size,
                "tabular_numeric_quantize_decimals": tabular_numeric_quantize_decimals,
            },
            suggestions=[],
        )

    top = candidates[:max_candidates]
    return CheckResult(
        name="label_hints",
        status="warning",
        summary=f"Found {len(top)} potentially mislabeled sample(s) (label hints).",
        details={
            "candidate_count": len(top),
            "candidates": [c.to_dict() for c in top],
            "image_hash_distance_threshold": image_hash_distance_threshold,
            "image_hash_size": image_hash_size,
            "tabular_numeric_quantize_decimals": tabular_numeric_quantize_decimals,
        },
        suggestions=[
            "Review the flagged samples and verify the labeling pipeline/source-of-truth for those items.",
            "If labels are expected to disagree (e.g. ambiguous items), consider adjusting the labeling guidelines or dataset policy.",
        ],
    )

