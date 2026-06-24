"""Unit tests for src.scoring"""

from src.issue import Issue
from src.scoring import compute_score, score_grade


def _weights():
    return {
        "null": 0.2,
        "duplicate": 0.2,
        "invalid_date": 0.15,
        "invalid_email": 0.15,
        "dtype": 0.15,
        "outlier": 0.15,
    }


def test_perfect_score_with_no_issues():
    score = compute_score(
        issues=[],
        total_rows=100,
        checked_columns_per_type={"null": 1, "duplicate": 1},
        weights=_weights(),
    )
    assert score.overall_score == 100.0
    assert score.total_issues == 0


def test_score_drops_with_issues():
    issues = [
        Issue(check_type="null", column="a", row_index=i, message="x")
        for i in range(10)
    ]
    score = compute_score(
        issues=issues,
        total_rows=100,
        checked_columns_per_type={"null": 1},
        weights=_weights(),
    )
    # 10/100 = 10% error rate on a check weighted at 0.2
    assert score.per_check_score["null"] == 90.0
    assert score.overall_score < 100.0


def test_unconfigured_check_type_scores_perfect():
    score = compute_score(
        issues=[],
        total_rows=50,
        checked_columns_per_type={},
        weights=_weights(),
    )
    assert score.overall_score == 100.0
    assert all(v == 100.0 for v in score.per_check_score.values())


def test_error_rate_capped_at_100_percent():
    issues = [
        Issue(check_type="duplicate", column=None, row_index=i, message="x")
        for i in range(200)  # more "issues" than rows, shouldn't go negative
    ]
    score = compute_score(
        issues=issues,
        total_rows=50,
        checked_columns_per_type={"duplicate": 1},
        weights=_weights(),
    )
    assert score.per_check_score["duplicate"] == 0.0


def test_score_grade_boundaries():
    assert score_grade(95) == "A"
    assert score_grade(90) == "A"
    assert score_grade(85) == "B"
    assert score_grade(75) == "C"
    assert score_grade(65) == "D"
    assert score_grade(40) == "F"
