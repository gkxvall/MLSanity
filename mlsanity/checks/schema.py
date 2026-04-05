from __future__ import annotations

from pathlib import Path

import pandas as pd

from mlsanity.types import CheckResult


def run_tabular_schema_check(
    csv_path: str,
    target_column: str,
    split_column: str | None = None,
) -> CheckResult:
    path = Path(csv_path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != ".csv":
        return CheckResult(
            name="schema",
            status="error",
            summary="Schema check requires a valid CSV file path.",
            details={},
            suggestions=[],
        )

    df = pd.read_csv(path)

    if target_column not in df.columns:
        return CheckResult(
            name="schema",
            status="error",
            summary=f"Missing target column: '{target_column}'.",
            details={"columns": list(df.columns)},
            suggestions=["Fix the CSV header or pass the correct --target name."],
        )

    if split_column is not None and split_column not in df.columns:
        return CheckResult(
            name="schema",
            status="error",
            summary=f"Split column not found: '{split_column}'.",
            details={"columns": list(df.columns)},
            suggestions=["Fix the CSV header or pass the correct --split-column name."],
        )

    n_rows = len(df)
    missing_by_column: dict[str, int] = {}
    missing_pct_by_column: dict[str, float] = {}
    empty_columns: list[str] = []
    constant_columns: list[str] = []

    for col in df.columns:
        series = df[col]
        missing = int(series.isna().sum())
        missing_by_column[col] = missing
        missing_pct_by_column[col] = (missing / n_rows * 100.0) if n_rows else 0.0

        if series.isna().all():
            empty_columns.append(col)
        elif series.nunique(dropna=True) <= 1:
            constant_columns.append(col)

    total_missing_cells = int(df.isna().sum().sum())
    columns_with_missing = [c for c, m in missing_by_column.items() if m > 0]

    status = "ok"
    if empty_columns or columns_with_missing:
        status = "warning"
    if target_column in empty_columns:
        status = "error"

    summary_parts: list[str] = []
    if columns_with_missing:
        summary_parts.append(f"{len(columns_with_missing)} column(s) have missing values")
    if empty_columns:
        summary_parts.append(f"{len(empty_columns)} empty column(s)")
    if constant_columns and constant_columns != [target_column]:
        non_target_constant = [c for c in constant_columns if c != target_column]
        if non_target_constant:
            summary_parts.append(f"{len(non_target_constant)} constant feature column(s)")

    summary = (
        "; ".join(summary_parts) + "."
        if summary_parts
        else "No major schema issues detected."
    )

    return CheckResult(
        name="schema",
        status=status,
        summary=summary,
        details={
            "num_rows": n_rows,
            "num_columns": len(df.columns),
            "columns": list(df.columns),
            "missing_by_column": missing_by_column,
            "missing_pct_by_column": missing_pct_by_column,
            "total_missing_cells": total_missing_cells,
            "columns_with_missing": columns_with_missing,
            "empty_columns": empty_columns,
            "constant_columns": constant_columns,
            "target_column": target_column,
            "split_column": split_column,
        },
        suggestions=[
            "Drop or impute columns with high missing rates before training.",
            "Remove empty columns; review constant columns—they may be useless features.",
        ]
        if status != "ok"
        else [],
    )
