from __future__ import annotations

from pathlib import Path

from mlsanity.engine import run_compare
from mlsanity.reporting.compare_html_report import render_compare_html_report
from mlsanity.reporting.compare_json_report import compare_report_to_dict


def test_compare_tabular_basic(tmp_path: Path) -> None:
    old_csv = tmp_path / "old.csv"
    new_csv = tmp_path / "new.csv"
    old_csv.write_text("f,target,split\n1,A,train\n2,B,val\n", encoding="utf-8")
    new_csv.write_text("f,target,split\n1,A,train\n2,B,val\n3,B,val\n", encoding="utf-8")

    compare = run_compare(str(old_csv), str(new_csv), "tabular", target="target", split_column="split")

    assert compare.dataset_type == "tabular"
    assert compare.total_samples_delta == 1
    assert isinstance(compare.health_score_delta, int)
    assert any(delta.name == "schema" for delta in compare.check_deltas)


def test_compare_image_basic(tmp_path: Path) -> None:
    (tmp_path / "old" / "cat").mkdir(parents=True)
    (tmp_path / "new" / "cat").mkdir(parents=True)
    (tmp_path / "old" / "cat" / "a.jpg").write_bytes(b"123")
    (tmp_path / "new" / "cat" / "a.jpg").write_bytes(b"123")
    (tmp_path / "new" / "cat" / "b.jpg").write_bytes(b"456")

    compare = run_compare(str(tmp_path / "old"), str(tmp_path / "new"), "image")
    assert compare.dataset_type == "image"
    assert compare.total_samples_delta == 1
    names = {d.name for d in compare.check_deltas}
    assert "corruption" in names
    assert "duplicates" in names


def test_compare_serialization_and_html(tmp_path: Path) -> None:
    old_csv = tmp_path / "old.csv"
    new_csv = tmp_path / "new.csv"
    old_csv.write_text("f,target\n1,A\n", encoding="utf-8")
    new_csv.write_text("f,target\n1,A\n2,B\n", encoding="utf-8")

    compare = run_compare(str(old_csv), str(new_csv), "tabular", target="target")

    payload = compare_report_to_dict(compare)
    assert "check_deltas" in payload
    assert payload["dataset_type"] == "tabular"

    html = render_compare_html_report(compare)
    assert "MLSanity compare report" in html
    assert "Check deltas" in html
