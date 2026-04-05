from __future__ import annotations

from mlsanity.types import CheckResult


def compute_health_score_and_status(checks: list[CheckResult]) -> tuple[int, str]:
    score = 100
    for c in checks:
        if c.status == "ok":
            continue
        name = c.name
        if name == "corruption":
            score -= 20
        elif name == "leakage":
            score -= 25
        elif name == "leakage_near":
            score -= 15
        elif name == "duplicates":
            score -= 15 if c.status == "error" else 10
        elif name == "near_duplicates":
            score -= 10
        elif name == "imbalance":
            score -= 15
        elif name == "schema":
            score -= 15 if c.status == "error" else 10

    score = max(0, min(100, score))

    if score >= 90:
        overall = "healthy"
    elif score >= 70:
        overall = "acceptable"
    elif score >= 40:
        overall = "needs_attention"
    else:
        overall = "critical"

    return score, overall
