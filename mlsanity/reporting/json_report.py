from __future__ import annotations

import json
from typing import Any
from dataclasses import asdict
from pathlib import Path

from mlsanity.types import Report


def report_to_dict(report: Report) -> dict:
    return {
        "dataset_path": report.dataset_path,
        "dataset_type": report.dataset_type,
        "total_samples": report.total_samples,
        "health_score": report.health_score,
        "overall_status": report.overall_status,
        "class_counts": report.class_counts,
        "split_counts": report.split_counts,
        "checks": [asdict(c) for c in report.checks],
    }


def write_json_report(
    report: Report,
    output_path: str,
    *,
    quality_gates: dict[str, Any] | None = None,
) -> None:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = report_to_dict(report)
    if quality_gates is not None:
        payload.update(quality_gates)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
