from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mlsanity.reporting.compare_json_report import compare_report_to_dict
from mlsanity.types import CompareReport


def render_compare_html_report(report: CompareReport) -> str:
    templates_dir = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("compare_report.html.j2")
    return template.render(report=compare_report_to_dict(report))


def write_compare_html_report(report: CompareReport, output_path: str) -> None:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_compare_html_report(report), encoding="utf-8")
