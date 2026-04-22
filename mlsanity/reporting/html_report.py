from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from mlsanity.reporting.json_report import report_to_dict
from mlsanity.types import Report


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _webapp_dist_dir() -> Path:
    return _project_root() / "report_template" / "dist"


def _enriched_payload(report: Report) -> dict:
    payload = report_to_dict(report)
    payload.update(
        {
            "project_name": "MLSanity",
            "report_title": "Dataset Report",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "splits_available": list((report.split_counts or {}).keys()),
            "num_classes": len(report.class_counts or {}),
        }
    )
    return payload


def render_html_report(report: Report) -> str:
    dist_dir = _webapp_dist_dir()
    index_path = dist_dir / "index.html"
    if not index_path.exists():
        raise FileNotFoundError(
            "Missing built report_template assets. "
            "Run `npm install && npm run build` in report_template."
        )

    html = index_path.read_text(encoding="utf-8")
    js_match = re.search(r'<script type="module" crossorigin src="(/assets/[^"]+\.js)"></script>', html)
    css_match = re.search(r'<link rel="stylesheet" crossorigin href="(/assets/[^"]+\.css)">', html)
    if not js_match or not css_match:
        raise RuntimeError("Unable to locate built web assets in dist/index.html")

    js_src = js_match.group(1).lstrip("/")
    css_href = css_match.group(1).lstrip("/")
    payload_json = json.dumps(_enriched_payload(report), separators=(",", ":"))

    html = html.replace(f'href="/{css_href}"', f'href="{css_href}"')
    html = html.replace(
        f'<script type="module" crossorigin src="/{js_src}"></script>',
        f"<script>window.__MLSANITY_REPORT__={payload_json};</script>\n"
        f'<script type="module" crossorigin src="{js_src}"></script>',
    )
    return html


def write_html_report(report: Report, output_path: str) -> None:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html_report(report), encoding="utf-8")

    dist_assets = _webapp_dist_dir() / "assets"
    if not dist_assets.exists():
        raise FileNotFoundError(
            "Missing built report_template assets directory. "
            "Run `npm install && npm run build` in report_template."
        )
    shutil.copytree(dist_assets, path.parent / "assets", dirs_exist_ok=True)
