from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from mlsanity.types import CheckResult, Sample


def run_image_corruption_check(samples: list[Sample]) -> CheckResult:
    zero_byte_ids: list[str] = []
    unreadable_ids: list[str] = []

    for sample in samples:
        if sample.modality != "image" or sample.path is None:
            continue

        image_path = Path(sample.path)

        try:
            if image_path.stat().st_size == 0:
                zero_byte_ids.append(sample.id)
                continue
        except OSError:
            unreadable_ids.append(sample.id)
            continue

        try:
            with Image.open(image_path) as image:
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError):
            unreadable_ids.append(sample.id)

    corrupted_count = len(zero_byte_ids) + len(unreadable_ids)
    total_images = sum(1 for sample in samples if sample.modality == "image")

    if corrupted_count == 0:
        return CheckResult(
            name="corruption",
            status="ok",
            summary="No corrupted images detected.",
            details={
                "total_images": total_images,
                "corrupted_images": 0,
                "zero_byte_files": 0,
                "unreadable_images": 0,
            },
            suggestions=[],
        )

    return CheckResult(
        name="corruption",
        status="warning",
        summary=f"Found {corrupted_count} corrupted image(s).",
        details={
            "total_images": total_images,
            "corrupted_images": corrupted_count,
            "zero_byte_files": len(zero_byte_ids),
            "unreadable_images": len(unreadable_ids),
            "zero_byte_ids": zero_byte_ids,
            "unreadable_ids": unreadable_ids,
        },
        suggestions=[
            "Remove or replace unreadable image files.",
            "Regenerate zero-byte files from the source dataset.",
        ],
    )
