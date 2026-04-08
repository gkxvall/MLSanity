from __future__ import annotations

from pathlib import Path

from PIL import Image

from mlsanity.engine import run_scan
from mlsanity.reporting.html_report import render_html_report


def _get_check(report, name: str):
    for c in report.checks:
        if c.name == name:
            return c
    return None


def test_label_hints_tabular_warning_on_quantized_conflict(tmp_path: Path) -> None:
    # Two rows have the same "near-identical" features after quantization but different labels.
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("x,target\n1.0002,A\n1.0004,B\n", encoding="utf-8")

    report = run_scan(str(csv_path), "tabular", target="target")
    check = _get_check(report, "label_hints")
    assert check is not None
    assert check.status == "warning"
    assert isinstance(check.details.get("candidate_count"), int)
    assert check.details["candidate_count"] >= 1
    assert isinstance(check.details.get("candidates"), list)

    html = render_html_report(report)
    candidates = check.details.get("candidates", [])
    assert any(c.get("sample_id") in html for c in candidates if isinstance(c, dict))


def test_label_hints_image_warning_on_near_identical_conflict(tmp_path: Path) -> None:
    # Identical images under different class folders should yield label hint candidates.
    train_cat = tmp_path / "train" / "cat"
    train_dog = tmp_path / "train" / "dog"
    train_cat.mkdir(parents=True)
    train_dog.mkdir(parents=True)

    img = Image.new("RGB", (32, 32), color=(10, 200, 100))
    img.save(train_cat / "a.png")
    img.save(train_dog / "a.png")

    report = run_scan(str(tmp_path), "image")
    check = _get_check(report, "label_hints")
    assert check is not None
    assert check.status == "warning"
    assert check.details["candidate_count"] >= 1

