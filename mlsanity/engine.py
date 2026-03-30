from mlsanity.checks.corruption import run_image_corruption_check
from mlsanity.checks.duplicates import run_image_exact_duplicates_check, run_tabular_duplicates_check
from mlsanity.checks.near_duplicates import run_image_near_duplicates_check
from mlsanity.loaders.image_loader import load_image_classification_dataset
from mlsanity.loaders.tabular_loader import load_tabular_csv_dataset
from mlsanity.types import CheckResult, Report


def run_scan(path: str, dataset_type: str, target: str | None = None, split_column: str | None = None) -> Report:
    normalized_type = dataset_type.strip().lower()
    checks: list[CheckResult] = []

    if normalized_type == "image":
        samples = load_image_classification_dataset(path)
        checks.append(run_image_corruption_check(samples))
        checks.append(run_image_exact_duplicates_check(samples))
        checks.append(run_image_near_duplicates_check(samples))
    elif normalized_type == "tabular":
        if target is None:
            raise ValueError("Tabular datasets require --target.")
        samples = load_tabular_csv_dataset(path, target_column=target, split_column=split_column)
        checks.append(run_tabular_duplicates_check(samples))
    else:
        raise ValueError("Unsupported dataset type. Use 'image' or 'tabular'.")

    return Report(
        dataset_type=normalized_type,
        total_samples=len(samples),
        checks=checks,
        health_score=100,
        overall_status="healthy",
    )