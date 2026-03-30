from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import imagehash
from PIL import Image, UnidentifiedImageError

from mlsanity.types import CheckResult, Sample


@dataclass
class _EdgeExample:
    id_a: str
    id_b: str
    distance: int


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


def run_image_near_duplicates_check(
    samples: list[Sample],
    *,
    hash_distance_threshold: int = 5,
    hash_size: int = 8,
    max_images: int = 2500,
    max_groups_in_details: int = 10,
    max_pair_examples_in_details: int = 50,
) -> CheckResult:
    image_samples = [s for s in samples if s.modality == "image" and s.path is not None]

    total_images = len(image_samples)
    if total_images == 0:
        return CheckResult(
            name="near_duplicates",
            status="ok",
            summary="No images found for near-duplicate checking.",
            details={
                "total_images": 0,
                "near_duplicate_groups": 0,
                "threshold": hash_distance_threshold,
            },
            suggestions=[],
        )

    if total_images > max_images:
        # Keep MVP predictable: naive all-pairs can get slow for very large datasets.
        image_samples = image_samples[:max_images]

    hash_by_index: list[imagehash.ImageHash | None] = [None] * len(image_samples)
    unreadable_ids: list[str] = []

    for i, sample in enumerate(image_samples):
        image_path = Path(sample.path)
        try:
            with Image.open(image_path) as img:
                # Convert to a deterministic mode so hashing is less sensitive to colorspaces.
                img = img.convert("RGB")
                hash_by_index[i] = imagehash.phash(img, hash_size=hash_size)
        except (UnidentifiedImageError, OSError, ValueError):
            unreadable_ids.append(sample.id)

    n = len(image_samples)
    uf = _UnionFind(n)

    pair_examples: list[_EdgeExample] = []
    valid_indices = [i for i in range(n) if hash_by_index[i] is not None]

    # Naive all-pairs within the bounded MVP max_images.
    for idx_a_i, idx_a in enumerate(valid_indices):
        hash_a = hash_by_index[idx_a]
        if hash_a is None:
            continue
        for idx_b in valid_indices[idx_a_i + 1 :]:
            hash_b = hash_by_index[idx_b]
            if hash_b is None:
                continue

            distance = hash_a - hash_b
            if distance <= hash_distance_threshold:
                uf.union(idx_a, idx_b)
                if len(pair_examples) < max_pair_examples_in_details:
                    pair_examples.append(
                        _EdgeExample(
                            id_a=image_samples[idx_a].id,
                            id_b=image_samples[idx_b].id,
                            distance=int(distance),
                        )
                    )

    groups_map: dict[int, list[str]] = {}
    for i in range(n):
        root = uf.find(i)
        groups_map.setdefault(root, []).append(image_samples[i].id)

    groups = [ids for ids in groups_map.values() if len(ids) > 1]
    groups.sort(key=len, reverse=True)

    near_duplicate_images = sum(len(g) for g in groups)

    if not groups:
        return CheckResult(
            name="near_duplicates",
            status="ok",
            summary="No near-duplicate images detected (perceptual hashing).",
            details={
                "total_images": total_images,
                "hashed_images": len(valid_indices),
                "near_duplicate_groups": 0,
                "near_duplicate_images": 0,
                "threshold": hash_distance_threshold,
                "hash_size": hash_size,
                "unreadable_while_hashing": len(unreadable_ids),
            },
            suggestions=[],
        )

    groups_preview = groups[:max_groups_in_details]
    status = "warning"

    return CheckResult(
        name="near_duplicates",
        status=status,
        summary=f"Found {near_duplicate_images} image(s) in near-duplicate groups.",
        details={
            "total_images": total_images,
            "hashed_images": len(valid_indices),
            "near_duplicate_groups": len(groups),
            "near_duplicate_images": near_duplicate_images,
            "threshold": hash_distance_threshold,
            "hash_size": hash_size,
            "groups": groups_preview,
            "pair_examples": [e.__dict__ for e in pair_examples],
            "unreadable_while_hashing": len(unreadable_ids),
        },
        suggestions=[
            "Consider de-duplicating near-identical samples within each split.",
            "Verify if similar images are expected (e.g. repeated captures) or indicate dataset issues.",
        ],
    )

