from __future__ import annotations

import json
from pathlib import Path

from mlsanity.reporting.json_report import write_json_report
from mlsanity.reporting.quality_gates import evaluate_quality_gates
from mlsanity.types import CheckResult, Report


def test_quality_gates_min_score_fails() -> None:
    report = Report(
        dataset_type="tabular",
        total_samples=1,
        checks=[CheckResult(name="schema", status="ok", summary="ok")],
        health_score=50,
        overall_status="needs_attention",
        dataset_path="/tmp/x.csv",
    )
    gates = evaluate_quality_gates(report, min_score=80, fail_on=None)
    assert gates["passed"] is False
    assert "below threshold" in gates["exit_reason"]


def test_quality_gates_fail_on_warning_fails() -> None:
    report = Report(
        dataset_type="tabular",
        total_samples=1,
        checks=[CheckResult(name="duplicates", status="warning", summary="warn")],
        health_score=100,
        overall_status="healthy",
        dataset_path="/tmp/x.csv",
    )
    gates = evaluate_quality_gates(report, min_score=None, fail_on="warning")
    assert gates["passed"] is False
    assert "status threshold" in gates["exit_reason"]


def test_write_json_report_includes_quality_gates(tmp_path: Path) -> None:
    report = Report(
        dataset_type="tabular",
        total_samples=1,
        checks=[CheckResult(name="schema", status="ok", summary="ok")],
        health_score=50,
        overall_status="needs_attention",
        dataset_path=str(tmp_path / "x.csv"),
    )
    gates = evaluate_quality_gates(report, min_score=80, fail_on=None)
    out = tmp_path / "report.json"
    write_json_report(report, str(out), quality_gates=gates)

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["passed"] is False
    assert payload["score_threshold"] == 80
    assert payload["status_threshold"] is None

