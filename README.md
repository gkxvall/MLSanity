# MLSanity

Sanity-check your dataset before training your model.

MLSanity is an open-source dataset sanity-checking toolkit that scans common dataset formats,
detects data quality issues, and produces actionable findings before you train.

## Current status

MLSanity is in early development. The project is being built incrementally with a small, practical MVP.

### What works today

- **CLI**: `mlsanity doctor` runs a scan and prints a basic summary.
- **Dataset loading**
  - **Image classification folders** (split-based or flat class folders)
  - **Tabular CSV** (required `--target`, optional `--split-column`)
- **Implemented checks**
  - **Corrupted/unreadable images** (zero-byte + Pillow validation)
  - **Exact duplicates**
    - images: SHA-256 file hash grouping
    - tabular: exact duplicate rows + feature-duplicates with conflicting labels
  - **Near-duplicates (images)**: perceptual hashing (pHash) with distance threshold grouping

## Quickstart

### Install (editable)

```bash
python -m pip install -e .
```

### Scan an image dataset

```bash
mlsanity doctor /path/to/dataset --type image
```

Supported layouts:

```text
dataset/
  train/
    cat/
    dog/
  val/
    cat/
    dog/
```

or:

```text
dataset/
  cat/
  dog/
```

### Scan a tabular CSV

```bash
mlsanity doctor /path/to/data.csv --type tabular --target target_col
```

With a split column:

```bash
mlsanity doctor /path/to/data.csv --type tabular --target target_col --split-column split
```

## MVP scope and roadmap

MLSanity v0.1 targets **image classification** and **tabular CSV** datasets.

### Done

- **Step 1**: Package foundation (types, CLI skeleton, engine skeleton)
- **Step 2**: Dataset loaders (image + tabular) and engine wiring
- **Step 3**: Checkers:
        **Step 3A**: Corruption check (images)
        **Step 3B**: Exact duplicates check (images + tabular)
        **Step 3C**: Near-duplicates check (images)

### In progress / next

- **Step 3D**: Class imbalance check (images + tabular)
- **Step 3E**: Tabular schema checks (missing values, empty/constant columns, etc.)
- **Step 4**: Train/validation leakage checks (exact + near-duplicate leakage)
- **Step 5**: Reporting (terminal summary, JSON report, HTML report)
- **Step 6**: Polish (examples, tests, docs, release prep)

## Planned MVP

- Image classification dataset support
- Tabular CSV dataset support
- Duplicate detection
- Near-duplicate detection
- Corruption detection
- Class imbalance detection
- Train/validation leakage detection
- JSON and HTML reports
