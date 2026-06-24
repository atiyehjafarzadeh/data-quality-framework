"""
Quality scoring.

Converts a raw list of Issues into a single 0-100 quality score, plus a
breakdown by check type, so the result can be tracked over time and
shown on a dashboard.

Scoring approach
-----------------
For each check type, we compute an *error rate* = issues_of_type /
total_opportunities_for_that_type, where "opportunities" is the number
of cells (row x column) that check could have flagged. We then convert
that to a per-check score (100 = perfect, 0 = every opportunity failed)
and combine per-check scores using the configured weights to get the
overall score. This keeps a dataset with many columns but only a tiny
fraction of bad cells from being unfairly punished, while still letting
pervasive problems pull the score down meaningfully.
"""

from dataclasses import dataclass
from typing import Dict, List

from .issue import Issue

CHECK_TYPES = [
    "null",
    "duplicate",
    "invalid_date",
    "invalid_email",
    "dtype",
    "outlier",
]


@dataclass
class ScoreBreakdown:
    overall_score: float
    per_check_score: Dict[str, float]
    per_check_count: Dict[str, int]
    total_issues: int
    total_rows: int
    total_opportunities: Dict[str, int]

    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_score, 2),
            "per_check_score": {
                k: round(v, 2) for k, v in self.per_check_score.items()
            },
            "per_check_count": self.per_check_count,
            "total_issues": self.total_issues,
            "total_rows": self.total_rows,
            "total_opportunities": self.total_opportunities,
        }


def compute_score(
    issues: List[Issue],
    total_rows: int,
    checked_columns_per_type: Dict[str, int],
    weights: Dict[str, float],
) -> ScoreBreakdown:
    """Compute the overall and per-check quality score."""
    counts: Dict[str, int] = {ct: 0 for ct in CHECK_TYPES}
    for issue in issues:
        counts[issue.check_type] = counts.get(issue.check_type, 0) + 1

    opportunities: Dict[str, int] = {}
    per_check_score: Dict[str, float] = {}

    for check_type in CHECK_TYPES:
        n_cols = checked_columns_per_type.get(check_type, 0)
        if check_type == "duplicate":
            opp = total_rows if n_cols > 0 else 0
        else:
            opp = total_rows * n_cols

        opportunities[check_type] = opp

        if opp == 0:
            # Check wasn't configured for any column -> treat as perfect
            # (it contributes its weight at full score rather than
            # silently zeroing out the overall score).
            per_check_score[check_type] = 100.0
            continue

        error_rate = min(counts[check_type] / opp, 1.0)
        per_check_score[check_type] = (1.0 - error_rate) * 100.0

    overall = sum(
        per_check_score[ct] * weights.get(ct, 0.0) for ct in CHECK_TYPES
    )

    return ScoreBreakdown(
        overall_score=overall,
        per_check_score=per_check_score,
        per_check_count=counts,
        total_issues=len(issues),
        total_rows=total_rows,
        total_opportunities=opportunities,
    )


def score_grade(score: float) -> str:
    """Map a numeric score to a letter grade for quick-glance reporting."""
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"
