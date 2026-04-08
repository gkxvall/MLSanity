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
    class_counts: dict[str, int] = field(default_factory=dict)
    split_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class CompareCheckDelta:
    name: str
    old_status: str
    new_status: str
    old_issue_count: int
    new_issue_count: int
    issue_delta: int


@dataclass
class CompareReport:
    dataset_type: str
    old_path: str
    new_path: str
    old_total_samples: int
    new_total_samples: int
    total_samples_delta: int
    old_health_score: int
    new_health_score: int
    health_score_delta: int
    old_class_counts: dict[str, int]
    new_class_counts: dict[str, int]
    class_count_delta: dict[str, int]
    check_deltas: list[CompareCheckDelta]
    introduced_regressions: list[str] = field(default_factory=list)
    resolved_issues: list[str] = field(default_factory=list)