from pathlib import Path

from mlsanity.checks.corruption import run_image_corruption_check
from mlsanity.checks.duplicates import run_image_exact_duplicates_check, run_tabular_duplicates_check
from mlsanity.checks.imbalance import run_class_imbalance_check
from mlsanity.checks.leakage import (
    run_image_cross_split_exact_leakage,
    run_image_cross_split_near_leakage,
    run_tabular_cross_split_leakage,
)
from mlsanity.checks.near_duplicates import run_image_near_duplicates_check
from mlsanity.checks.schema import run_tabular_schema_check
from mlsanity.loaders.image_loader import load_image_classification_dataset
from mlsanity.loaders.tabular_loader import load_tabular_csv_dataset
from mlsanity.reporting.scoring import compute_health_score_and_status
from mlsanity.types import CheckResult, Report


def run_scan(path: str, dataset_type: str, target: str | None = None, split_column: str | None = None) -> Report:
    normalized_type = dataset_type.strip().lower()
    resolved_path = str(Path(path).expanduser().resolve())
    checks: list[CheckResult] = []

    if normalized_type == "image":
        samples = load_image_classification_dataset(path)
        checks.append(run_image_corruption_check(samples))
        checks.append(run_image_exact_duplicates_check(samples))
        checks.append(run_image_near_duplicates_check(samples))
        checks.append(run_class_imbalance_check(samples))
        checks.append(run_image_cross_split_exact_leakage(samples))
        checks.append(run_image_cross_split_near_leakage(samples))
    elif normalized_type == "tabular":
        if target is None:
            raise ValueError("Tabular datasets require --target.")
        samples = load_tabular_csv_dataset(path, target_column=target, split_column=split_column)
        checks.append(run_tabular_schema_check(path, target_column=target, split_column=split_column))
        checks.append(run_tabular_duplicates_check(samples))
        checks.append(run_class_imbalance_check(samples))
        checks.append(run_tabular_cross_split_leakage(samples))
    else:
        raise ValueError("Unsupported dataset type. Use 'image' or 'tabular'.")

    health_score, overall_status = compute_health_score_and_status(checks)

    return Report(
        dataset_type=normalized_type,
        total_samples=len(samples),
        checks=checks,
        health_score=health_score,
        overall_status=overall_status,
        dataset_path=resolved_path,
    )
