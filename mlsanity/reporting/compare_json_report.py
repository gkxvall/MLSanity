from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from mlsanity.types import CompareReport


def compare_report_to_dict(report: CompareReport) -> dict:
    return asdict(report)


def write_compare_json_report(
    report: CompareReport,
    output_path: str,
    *,
    quality_gates: dict[str, Any] | None = None,
) -> None:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = compare_report_to_dict(report)
    if quality_gates is not None:
        payload.update(quality_gates)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
