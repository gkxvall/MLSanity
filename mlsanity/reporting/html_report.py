from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mlsanity.reporting.json_report import report_to_dict
from mlsanity.types import Report


def render_html_report(report: Report) -> str:
    templates_dir = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html.j2")
    return template.render(report=report_to_dict(report))


def write_html_report(report: Report, output_path: str) -> None:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html_report(report), encoding="utf-8")
