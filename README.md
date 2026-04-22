<div align="center">

<img src="logo.png" alt="MLSanity logo" />

# MLSanity

**Sanity-check your dataset before training your model.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat)](LICENSE)
[![Typer](https://img.shields.io/badge/CLI-Typer-000000?style=flat&logo=terminal&logoColor=white)](https://typer.tiangolo.com/)
[![Rich](https://img.shields.io/badge/output-Rich-000000?style=flat)](https://rich.readthedocs.io/)

</div>

---

MLSanity is an open-source **dataset sanity-checking** toolkit for **image classification** folders and **tabular CSV** files. Run one command, get a **colorized terminal summary**, optional **JSON** and **HTML** reports, and a simple **health score** so you catch data issues before you waste GPU time.

**Current release:** `v0.2.0` (MVP)

## Why MLSanity?

| Without MLSanity                             | With MLSanity                                                    |
| -------------------------------------------- | ---------------------------------------------------------------- |
| Spot-check a few files by hand               | Scan **every** image row / file the loaders see                  |
| Duplicates and leakage hide in large folders | **Exact** and **near-duplicate** checks, **cross-split** leakage |
| “Looks fine” in a notebook                   | **Structured checks** + **scores** + exportable **reports**      |
| Hard to share findings with a team           | **JSON / HTML** artifacts you can attach to PRs or tickets       |

## Features at a glance

| Capability                                                 | v0.2          |
| ---------------------------------------------------------- | ------------- |
| Image classification folders (split-based or flat classes) | Yes           |
| Tabular CSV with `--target` (optional `--split-column`)    | Yes           |
| Corruption, duplicates, near-duplicates, imbalance         | Yes           |
| Schema + tabular duplicates + leakage                      | Yes           |
| Terminal (Rich), JSON, HTML reports                        | Yes           |
| Train/val **leakage** when splits exist                    | Yes           |
| Web dashboard, plugins, auto-fix                           | _Not in v0.2_ |

## How it works

```mermaid
flowchart LR
    subgraph inputs["Your data"]
        IMG["Image folders"]
        CSV["CSV + target"]
    end

    subgraph pipeline["MLSanity"]
        L["Loaders"]
        C["Checks"]
        S["Health score"]
        R["Reports"]
    end

    IMG --> L
    CSV --> L
    L --> C
    C --> S
    S --> R

    R --> T["Terminal"]
    R --> J["JSON"]
    R --> H["HTML"]
```

**Pipeline in words:** loaders turn paths into `Sample` objects → checks produce `CheckResult`s → scoring derives a 0–100 **health score** and status band → reporting prints to the terminal and optionally writes **JSON** / **HTML**.

## Requirements

- **Python 3.11+**

## Install

```bash
git clone https://github.com/<your-username>/MLSanity.git
cd MLSanity
python -m pip install -e .
```

## Quick usage

### Image classification

```bash
mlsanity doctor /path/to/dataset --type image
```

### Tabular CSV

```bash
mlsanity doctor /path/to/data.csv --type tabular --target target_column
```

Optional split column (enables cross-split leakage checks):

```bash
mlsanity doctor /path/to/data.csv --type tabular --target target_column --split-column split
```

### Export reports

```bash
mlsanity doctor /path/to/data --type image \
  --json report.json \
  --html report.html
```

The CLI uses **Rich** for tables, panels, and colored status in the terminal.

### Version

```bash
mlsanity version
```

## Supported layouts

**Images — split folders**

```text
dataset/
  train/
    cat/
    dog/
  val/
    cat/
    dog/
```

**Images — flat class folders**

```text
dataset/
  cat/
  dog/
```

## What v0.2 checks

| Area    | Check             | What it does                                              |
| ------- | ----------------- | --------------------------------------------------------- |
| Images  | `corruption`      | Zero-byte files; unreadable / invalid images (Pillow)     |
| Images  | `duplicates`      | Exact duplicates via **SHA-256** of file bytes            |
| Images  | `near_duplicates` | **pHash** + Hamming distance grouping                     |
| Images  | `imbalance`       | Class counts, %, imbalance ratio                          |
| Images  | `leakage`         | Same file hash in **more than one split**                 |
| Images  | `leakage_near`    | Near-duplicate **pairs across splits**                    |
| Images  | `label_hints`     | Heuristic hints for likely label issues (not definitive) |
| Tabular | `schema`          | Missing values, empty columns, constant columns           |
| Tabular | `duplicates`      | Exact duplicate rows; conflicting labels on same features |
| Tabular | `imbalance`       | Same metrics on the **target** column                     |
| Tabular | `leakage`         | Same **feature row** under **more than one split**        |
| Tabular | `label_hints`     | Heuristic hints for likely label issues (not definitive) |

If there are **no splits** (e.g. flat image layout), cross-split leakage checks return **OK** with a short “skipped” explanation.

## Health score & status bands

The score starts at **100** and applies **penalties** for warnings/errors from checks, then clamps to **0–100**.

| Check (when not OK)            | Approx. penalty |
| ------------------------------ | --------------- |
| `corruption`                   | −20             |
| `leakage`                      | −25             |
| `leakage_near`                 | −15             |
| `duplicates` (warning / error) | −10 / −15       |
| `near_duplicates`              | −10             |
| `imbalance`                    | −15             |
| `schema`                       | −10 / −15       |
| `label_hints`                  | −5              |

| Score  | `overall_status`  |
| ------ | ----------------- |
| 90–100 | `healthy`         |
| 70–89  | `acceptable`      |
| 40–69  | `needs_attention` |
| 0–39   | `critical`        |

## Report outputs compared

| Output       | Best for                                     |
| ------------ | -------------------------------------------- |
| **Terminal** | Fast feedback; colored summary in your shell |
| **JSON**     | Scripts, CI, dashboards, custom tooling      |
| **HTML**     | Sharing with teammates; opening in a browser |

## v0.2 additions (beyond v0.1)

- **Suspicious-label hints**: `label_hints` check (heuristic hints, status `warning`).
- **Dataset comparison mode**: `mlsanity compare OLD_PATH NEW_PATH ...` with terminal + JSON + HTML compare reports.
- **CI-friendly quality gates**: `--min-score` and `--fail-on warning|error` (non-zero exit code + pass/fail fields in JSON).
- **Tabular formats**: tabular loader supports **CSV**, **TSV**, and **Parquet** (`.parquet` requires a Parquet engine like `pyarrow`).
- **Richer report visuals**: HTML report now shows class distribution and split distribution charts, plus “what to fix first”.

## Project layout

```text
mlsanity/
  cli.py                 # Typer CLI (Rich output)
  engine.py              # Orchestrates loaders, checks, scoring
  types.py               # Sample, CheckResult, Report
  loaders/               # image_loader, tabular_loader
  checks/                # corruption, duplicates, near_duplicates, imbalance, schema, leakage
  reporting/             # terminal, json_report, html_report, scoring, templates/
examples/                # sample CSV + notes
tests/                   # pytest
logo.png                 # Logo for README (keep at repo root next to README.md)
```

## Examples

See [`examples/README.md`](examples/README.md) and [`examples/sample_tabular.csv`](examples/sample_tabular.csv).

## Tests

```bash
python -m pip install pytest
python -m pytest tests/ -v
```

## Roadmap (not v0.2)

- Web dashboard / plugins / auto-fix UI
- More formats and deeper diagnostics (tracked in project issues once published)

## License

MIT — see [`LICENSE`](LICENSE).
