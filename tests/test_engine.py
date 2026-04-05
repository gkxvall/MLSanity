from __future__ import annotations

from pathlib import Path

import pytest

from mlsanity.engine import run_scan


def test_tabular_scan_minimal(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("f1,f2,target\n1,2,A\n3,4,B\n", encoding="utf-8")
    report = run_scan(str(csv_path), "tabular", target="target")
    assert report.dataset_type == "tabular"
    assert report.total_samples == 2
    assert report.health_score >= 0
    assert report.overall_status in ("healthy", "acceptable", "needs_attention", "critical")
    names = {c.name for c in report.checks}
    assert "schema" in names
    assert "duplicates" in names
    assert "imbalance" in names
    assert "leakage" in names


def test_image_scan_empty_class_folder(tmp_path: Path) -> None:
    (tmp_path / "train" / "cat").mkdir(parents=True)
    report = run_scan(str(tmp_path), "image")
    assert report.dataset_type == "image"
    assert report.total_samples == 0
    assert isinstance(report.dataset_path, str)


def test_tabular_requires_target(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="target"):
        run_scan(str(csv_path), "tabular")


def test_report_to_dict_roundtrip_keys() -> None:
    from mlsanity.reporting.json_report import report_to_dict
    from mlsanity.types import CheckResult, Report

    r = Report(
        dataset_type="tabular",
        total_samples=1,
        checks=[
            CheckResult(name="schema", status="ok", summary="ok", details={}, suggestions=[]),
        ],
        health_score=100,
        overall_status="healthy",
        dataset_path="/tmp/x.csv",
    )
    d = report_to_dict(r)
    assert d["dataset_path"] == "/tmp/x.csv"
    assert d["checks"][0]["name"] == "schema"


def test_html_report_renders() -> None:
    from mlsanity.reporting.html_report import render_html_report
    from mlsanity.types import CheckResult, Report

    r = Report(
        dataset_type="tabular",
        total_samples=1,
        checks=[
            CheckResult(name="schema", status="ok", summary="ok", details={}, suggestions=[]),
        ],
        health_score=100,
        overall_status="healthy",
        dataset_path="/tmp/x.csv",
    )
    html = render_html_report(r)
    assert "MLSanity" in html
    assert "schema" in html
