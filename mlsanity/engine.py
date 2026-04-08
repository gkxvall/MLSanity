from __future__ import annotations

from collections import Counter
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
from mlsanity.checks.label_hints import run_label_hints_check
from mlsanity.checks.near_duplicates import run_image_near_duplicates_check
from mlsanity.checks.schema import run_tabular_schema_check
from mlsanity.loaders.image_loader import load_image_classification_dataset
from mlsanity.loaders.tabular_loader import load_tabular_csv_dataset
from mlsanity.reporting.scoring import compute_health_score_and_status
from mlsanity.types import CheckResult, CompareCheckDelta, CompareReport, Report

ProgressCallback = Callable[[int, int, str], None]


def _find_check(report: Report, name: str) -> CheckResult | None:
    for check in report.checks:
        if check.name == name:
            return check
    return None


def _extract_issue_count(check: CheckResult | None) -> int:
    if check is None or check.status == "ok":
        return 0

    details = check.details or {}
    if check.name == "label_hints":
        candidate_count = details.get("candidate_count")
        if isinstance(candidate_count, int):
            return candidate_count
        candidates = details.get("candidates")
        if isinstance(candidates, list):
            return len(candidates)
        return 1

    for key in (
        "corrupted_images",
        "duplicate_images",
        "near_duplicate_images",
        "cross_split_duplicate_groups",
        "cross_split_near_pairs",
        "affected_images",
        "affected_rows",
        "leaking_feature_groups",
        "exact_duplicate_rows",
        "duplicate_feature_rows_conflicting_labels",
    ):
        value = details.get(key)
        if isinstance(value, int):
            return value

    if check.name == "schema":
        missing_cols = details.get("columns_with_missing", [])
        empty_cols = details.get("empty_columns", [])
        if isinstance(missing_cols, list) and isinstance(empty_cols, list):
            return len(set(missing_cols + empty_cols))

    # For checks that are mostly severity based (e.g. imbalance), use binary issue count.
    return 1


def _extract_class_counts(report: Report) -> dict[str, int]:
    imbalance = _find_check(report, "imbalance")
    if imbalance is None:
        return {}
    counts = imbalance.details.get("class_counts", {})
    if not isinstance(counts, dict):
        return {}
    cleaned: dict[str, int] = {}
    for k, v in counts.items():
        if isinstance(v, int):
            cleaned[str(k)] = v
    return cleaned


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
    class_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()

    def tick(completed: int, total: int, label: str) -> None:
        if progress is not None:
            progress(completed, total, label)

    if normalized_type == "image":
        checkers: list[tuple[str, Callable[[], CheckResult]]] = [
            ("Corruption", lambda: run_image_corruption_check(samples)),
            ("Duplicates", lambda: run_image_exact_duplicates_check(samples)),
            ("Near-duplicates", lambda: run_image_near_duplicates_check(samples)),
            ("Label hints", lambda: run_label_hints_check(samples)),
            ("Class imbalance", lambda: run_class_imbalance_check(samples)),
            ("Cross-split leakage (exact)", lambda: run_image_cross_split_exact_leakage(samples)),
            ("Cross-split leakage (near)", lambda: run_image_cross_split_near_leakage(samples)),
        ]
        total_steps = 1 + len(checkers)
        tick(0, total_steps, "Loading dataset")
        samples = load_image_classification_dataset(path)
        class_counts = Counter(s.label for s in samples if s.label is not None)
        split_counts = Counter(s.split for s in samples if s.split is not None)
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
            ("Label hints", lambda: run_label_hints_check(samples)),
            ("Class imbalance", lambda: run_class_imbalance_check(samples)),
            ("Cross-split leakage", lambda: run_tabular_cross_split_leakage(samples)),
        ]
        total_steps = 1 + len(checkers)
        tick(0, total_steps, "Loading dataset")
        samples = load_tabular_csv_dataset(path, target_column=target, split_column=split_column)
        class_counts = Counter(s.label for s in samples if s.label is not None)
        split_counts = Counter(s.split for s in samples if s.split is not None)
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
        class_counts=dict(class_counts),
        split_counts=dict(split_counts),
    )


def build_compare_report(old_report: Report, new_report: Report, dataset_type: str) -> CompareReport:
    check_names = sorted({c.name for c in old_report.checks} | {c.name for c in new_report.checks})
    check_deltas: list[CompareCheckDelta] = []
    introduced_regressions: list[str] = []
    resolved_issues: list[str] = []

    for name in check_names:
        old_check = _find_check(old_report, name)
        new_check = _find_check(new_report, name)

        old_status = old_check.status if old_check is not None else "ok"
        new_status = new_check.status if new_check is not None else "ok"

        old_count = _extract_issue_count(old_check)
        new_count = _extract_issue_count(new_check)
        delta = new_count - old_count

        check_deltas.append(
            CompareCheckDelta(
                name=name,
                old_status=old_status,
                new_status=new_status,
                old_issue_count=old_count,
                new_issue_count=new_count,
                issue_delta=delta,
            )
        )

        if old_count == 0 and new_count > 0:
            introduced_regressions.append(name)
        elif old_count > 0 and new_count == 0:
            resolved_issues.append(name)

    old_counts = _extract_class_counts(old_report)
    new_counts = _extract_class_counts(new_report)
    labels = sorted(set(old_counts) | set(new_counts))
    class_count_delta = {label: new_counts.get(label, 0) - old_counts.get(label, 0) for label in labels}

    return CompareReport(
        dataset_type=dataset_type.strip().lower(),
        old_path=old_report.dataset_path,
        new_path=new_report.dataset_path,
        old_total_samples=old_report.total_samples,
        new_total_samples=new_report.total_samples,
        total_samples_delta=new_report.total_samples - old_report.total_samples,
        old_health_score=old_report.health_score,
        new_health_score=new_report.health_score,
        health_score_delta=new_report.health_score - old_report.health_score,
        old_class_counts=old_counts,
        new_class_counts=new_counts,
        class_count_delta=class_count_delta,
        check_deltas=check_deltas,
        introduced_regressions=introduced_regressions,
        resolved_issues=resolved_issues,
    )


def run_compare(
    old_path: str,
    new_path: str,
    dataset_type: str,
    target: str | None = None,
    split_column: str | None = None,
) -> CompareReport:
    old_report = run_scan(old_path, dataset_type, target=target, split_column=split_column)
    new_report = run_scan(new_path, dataset_type, target=target, split_column=split_column)
    return build_compare_report(old_report, new_report, dataset_type)
