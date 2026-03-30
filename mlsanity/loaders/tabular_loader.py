from __future__ import annotations

from pathlib import Path

import pandas as pd

from mlsanity.types import Sample


def load_tabular_csv_dataset(
    csv_path: str,
    target_column: str,
    split_column: str | None = None,
) -> list[Sample]:
    if not target_column or not target_column.strip():
        raise ValueError("A non-empty target column is required for tabular datasets.")

    path = Path(csv_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"CSV path does not exist: {csv_path}")
    if not path.is_file():
        raise ValueError(f"CSV path must be a file: {csv_path}")
    if path.suffix.lower() != ".csv":
        raise ValueError(f"Expected a CSV file (.csv), got: {csv_path}")

    df = pd.read_csv(path)

    if target_column not in df.columns:
        raise ValueError(f"Missing required target column: '{target_column}'")

    if split_column is not None and split_column not in df.columns:
        raise ValueError(f"Split column not found: '{split_column}'")

    feature_columns = [col for col in df.columns if col not in {target_column, split_column}]

    samples: list[Sample] = []
    for idx, row in df.iterrows():
        target_value = row[target_column]
        split_value = row[split_column] if split_column else None

        features = {col: row[col] for col in feature_columns}
        sample_id = f"row_{idx}"

        samples.append(
            Sample(
                id=sample_id,
                path=str(path),
                label=None if pd.isna(target_value) else str(target_value),
                split=None if split_value is None or pd.isna(split_value) else str(split_value),
                modality="tabular",
                features=features,
                metadata={"row_index": int(idx)},
            )
        )

    return samples
