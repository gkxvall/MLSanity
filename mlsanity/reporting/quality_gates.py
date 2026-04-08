from __future__ import annotations

from typing import Any

from mlsanity.types import Report


def evaluate_quality_gates(
    report: Report,
    *,
    min_score: int | None,
    fail_on: str | None,
) -> dict[str, Any]:
    """
    Evaluate CI-friendly thresholds.

    Returns a machine-readable dict suitable for inclusion in JSON output.
    """

    score_threshold = min_score
    status_threshold = fail_on

    passed_score = True
    if min_score is not None:
        passed_score = report.health_score >= min_score

    failed_status = False
    if fail_on is not None:
        normalized = fail_on.strip().lower()
        if normalized == "warning":
            failed_status = any(c.status in ("warning", "error") for c in report.checks)
        elif normalized == "error":
            failed_status = any(c.status == "error" for c in report.checks)
        else:
            raise ValueError("--fail-on must be one of: warning, error")

    passed = passed_score and not failed_status

    if not passed_score:
        exit_reason = (
            f"Health score {report.health_score} is below threshold {min_score}."
            if min_score is not None
            else "Health score threshold not satisfied."
        )
    elif failed_status:
        exit_reason = f"At least one check is at or above status threshold '{fail_on}'."
    else:
        exit_reason = "All quality gates passed."

    return {
        "passed": passed,
        "exit_reason": exit_reason,
        "score_threshold": score_threshold,
        "status_threshold": status_threshold,
    }

