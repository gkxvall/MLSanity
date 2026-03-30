from __future__ import annotations

from pathlib import Path

from mlsanity.types import Sample

SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".webp",
}

KNOWN_SPLITS = {"train", "val", "valid", "validation", "test"}


def _is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def _iter_image_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if _is_hidden(file_path.relative_to(root)):
            continue
        if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            continue
        files.append(file_path)
    return files


def load_image_classification_dataset(dataset_path: str) -> list[Sample]:
    root = Path(dataset_path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Dataset path does not exist: {dataset_path}")
    if not root.is_dir():
        raise ValueError(f"Dataset path must be a directory: {dataset_path}")

    top_level_dirs = [
        child
        for child in root.iterdir()
        if child.is_dir() and not child.name.startswith(".")
    ]
    available_splits = {d.name.lower() for d in top_level_dirs if d.name.lower() in KNOWN_SPLITS}

    samples: list[Sample] = []

    if available_splits:
        for split_dir in top_level_dirs:
            split_name = split_dir.name.lower()
            if split_name not in KNOWN_SPLITS:
                continue

            class_dirs = [
                child
                for child in split_dir.iterdir()
                if child.is_dir() and not child.name.startswith(".")
            ]
            for class_dir in class_dirs:
                label = class_dir.name
                for image_path in _iter_image_files(class_dir):
                    relative_path = image_path.relative_to(root).as_posix()
                    samples.append(
                        Sample(
                            id=relative_path,
                            path=str(image_path),
                            label=label,
                            split=split_name,
                            modality="image",
                            features=None,
                            metadata={},
                        )
                    )
    else:
        class_dirs = top_level_dirs
        for class_dir in class_dirs:
            label = class_dir.name
            for image_path in _iter_image_files(class_dir):
                relative_path = image_path.relative_to(root).as_posix()
                samples.append(
                    Sample(
                        id=relative_path,
                        path=str(image_path),
                        label=label,
                        split=None,
                        modality="image",
                        features=None,
                        metadata={},
                    )
                )

    return samples
