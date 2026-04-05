from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import imagehash
from PIL import Image, UnidentifiedImageError

from mlsanity.checks.duplicates import _sha256_file, _stable_features_key
from mlsanity.types import CheckResult, Sample


def run_image_cross_split_exact_leakage(samples: list[Sample]) -> CheckResult:
    image_samples = [s for s in samples if s.modality == "image" and s.path is not None]
    with_split = [s for s in image_samples if s.split is not None]

    if not with_split:
        return CheckResult(
            name="leakage",
            status="ok",
            summary="No split labels on images; skipping train/val exact-duplicate leakage check.",
            details={"skipped": True, "reason": "no_split"},
            suggestions=[],
        )

    hash_to_splits: dict[str, set[str]] = defaultdict(set)
    hash_to_ids: dict[str, list[str]] = defaultdict(list)

    for sample in with_split:
        try:
            h = _sha256_file(Path(sample.path))
        except OSError:
            continue
        hash_to_splits[h].add(sample.split)
        hash_to_ids[h].append(sample.id)

    leaking_hashes = [h for h, splits in hash_to_splits.items() if len(splits) > 1]
    leaking_ids = [i for h in leaking_hashes for i in hash_to_ids[h]]

    if not leaking_hashes:
        return CheckResult(
            name="leakage",
            status="ok",
            summary="No exact duplicate images found across different splits.",
            details={
                "skipped": False,
                "cross_split_duplicate_groups": 0,
                "affected_images": 0,
            },
            suggestions=[],
        )

    return CheckResult(
        name="leakage",
        status="warning",
        summary=f"Found {len(leaking_hashes)} identical file(s) appearing in more than one split.",
        details={
            "skipped": False,
            "cross_split_duplicate_groups": len(leaking_hashes),
            "affected_images": len(set(leaking_ids)),
            "example_ids": leaking_ids[:50],
        },
        suggestions=[
            "Remove or reassign samples so the same file does not appear in both train and validation.",
        ],
    )


def run_image_cross_split_near_leakage(
    samples: list[Sample],
    *,
    hash_distance_threshold: int = 5,
    hash_size: int = 8,
    max_images: int = 2500,
) -> CheckResult:
    image_samples = [s for s in samples if s.modality == "image" and s.path is not None]
    with_split = [s for s in image_samples if s.split is not None]

    if not with_split:
        return CheckResult(
            name="leakage_near",
            status="ok",
            summary="No split labels on images; skipping near-duplicate cross-split leakage check.",
            details={"skipped": True, "reason": "no_split"},
            suggestions=[],
        )

    if len(with_split) > max_images:
        with_split = with_split[:max_images]

    hashes: list[imagehash.ImageHash | None] = [None] * len(with_split)
    for i, s in enumerate(with_split):
        try:
            with Image.open(Path(s.path)) as img:
                img = img.convert("RGB")
                hashes[i] = imagehash.phash(img, hash_size=hash_size)
        except (UnidentifiedImageError, OSError, ValueError):
            hashes[i] = None

    cross_pairs: list[dict[str, str | int]] = []
    valid = [
        (hashes[i], with_split[i].split, with_split[i].id)
        for i in range(len(with_split))
        if hashes[i] is not None
    ]

    total_cross = 0
    for a in range(len(valid)):
        h_a, split_a, id_a = valid[a]
        for b in range(a + 1, len(valid)):
            h_b, split_b, id_b = valid[b]
            if split_a == split_b:
                continue
            dist = h_a - h_b
            if dist <= hash_distance_threshold:
                total_cross += 1
                if len(cross_pairs) < 50:
                    cross_pairs.append(
                        {
                            "id_a": id_a,
                            "id_b": id_b,
                            "distance": int(dist),
                            "splits": f"{split_a}|{split_b}",
                        }
                    )

    if total_cross == 0:
        return CheckResult(
            name="leakage_near",
            status="ok",
            summary="No near-duplicate images detected across different splits.",
            details={
                "skipped": False,
                "cross_split_near_pairs": 0,
                "threshold": hash_distance_threshold,
            },
            suggestions=[],
        )

    return CheckResult(
        name="leakage_near",
        status="warning",
        summary=f"Found {total_cross} near-duplicate pair(s) across splits.",
        details={
            "skipped": False,
            "cross_split_near_pairs": total_cross,
            "threshold": hash_distance_threshold,
            "pair_examples": cross_pairs,
        },
        suggestions=[
            "Near-duplicates across train and validation can inflate validation metrics; de-duplicate or move one copy.",
        ],
    )


def run_tabular_cross_split_leakage(samples: list[Sample]) -> CheckResult:
    tab = [s for s in samples if s.modality == "tabular"]
    with_split = [s for s in tab if s.split is not None]

    if not with_split:
        return CheckResult(
            name="leakage",
            status="ok",
            summary="No split column values; skipping cross-split row leakage check.",
            details={"skipped": True, "reason": "no_split"},
            suggestions=[],
        )

    features_to_splits: dict[tuple, set[str]] = defaultdict(set)
    features_to_ids: dict[tuple, list[str]] = defaultdict(list)

    for s in with_split:
        fk = _stable_features_key(s.features)
        features_to_splits[fk].add(s.split)
        features_to_ids[fk].append(s.id)

    leaking_keys = [fk for fk, splits in features_to_splits.items() if len(splits) > 1]
    affected = sum(len(features_to_ids[fk]) for fk in leaking_keys)

    if not leaking_keys:
        return CheckResult(
            name="leakage",
            status="ok",
            summary="No identical feature rows found across different splits.",
            details={
                "skipped": False,
                "leaking_feature_groups": 0,
                "affected_rows": 0,
            },
            suggestions=[],
        )

    return CheckResult(
        name="leakage",
        status="warning",
        summary=f"Found {len(leaking_keys)} feature pattern(s) repeated across splits ({affected} row(s)).",
        details={
            "skipped": False,
            "leaking_feature_groups": len(leaking_keys),
            "affected_rows": affected,
            "example_row_ids": [i for fk in leaking_keys[:5] for i in features_to_ids[fk][:10]],
        },
        suggestions=[
            "Ensure train and validation splits are disjoint by feature identity to avoid leakage.",
        ],
    )
