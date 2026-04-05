from dataclasses import dataclass, field
from typing import Any


@dataclass
class Sample:
    id: str
    path: str | None
    label: str | None
    split: str | None
    modality: str
    features: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckResult:
    name: str
    status: str  # ok, warning, error
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class Report:
    dataset_type: str
    total_samples: int
    checks: list[CheckResult]
    health_score: int
    overall_status: str
    dataset_path: str = ""