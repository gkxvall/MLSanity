from __future__ import annotations

from collections.abc import Callable
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

ProgressCallback = Callable[[int, int, str], None]


def run_scan(
    path: str,
    dataset_type: str,
    target: str | None = None,
    split_column: str | None = None,
    *,
    progress: ProgressCallback | None = None,
) -> Report:
    """
    Load samples, run checks, score, return Report.

    If ``progress`` is set, it is called as ``(completed_steps, total_steps, label)`` at the
    start of each phase: loading (step 0), then each check (1..n-1), then a final ``Complete``
    step (n == total_steps). ``completed_steps`` matches the bar fill level.
    """
    normalized_type = dataset_type.strip().lower()
    resolved_path = str(Path(path).expanduser().resolve())
    checks: list[CheckResult] = []

    def tick(completed: int, total: int, label: str) -> None:
        if progress is not None:
            progress(completed, total, label)

    if normalized_type == "image":
        checkers: list[tuple[str, Callable[[], CheckResult]]] = [
            ("Corruption", lambda: run_image_corruption_check(samples)),
            ("Duplicates", lambda: run_image_exact_duplicates_check(samples)),
            ("Near-duplicates", lambda: run_image_near_duplicates_check(samples)),
            ("Class imbalance", lambda: run_class_imbalance_check(samples)),
            ("Cross-split leakage (exact)", lambda: run_image_cross_split_exact_leakage(samples)),
            ("Cross-split leakage (near)", lambda: run_image_cross_split_near_leakage(samples)),
        ]
        total_steps = 1 + len(checkers)
        tick(0, total_steps, "Loading dataset")
        samples = load_image_classification_dataset(path)
        for i, (label, fn) in enumerate(checkers, start=1):
            tick(i, total_steps, label)
            checks.append(fn())
        tick(total_steps, total_steps, "Complete")
    elif normalized_type == "tabular":
        if target is None:
            raise ValueError("Tabular datasets require --target.")
        checkers = [
            ("Schema", lambda: run_tabular_schema_check(path, target_column=target, split_column=split_column)),
            ("Duplicates", lambda: run_tabular_duplicates_check(samples)),
            ("Class imbalance", lambda: run_class_imbalance_check(samples)),
            ("Cross-split leakage", lambda: run_tabular_cross_split_leakage(samples)),
        ]
        total_steps = 1 + len(checkers)
        tick(0, total_steps, "Loading dataset")
        samples = load_tabular_csv_dataset(path, target_column=target, split_column=split_column)
        for i, (label, fn) in enumerate(checkers, start=1):
            tick(i, total_steps, label)
            checks.append(fn())
        tick(total_steps, total_steps, "Complete")
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
