"""
Validation engine.

This is the orchestration layer: given a DataFrame and a DQConfig, it
runs every applicable check, collects all Issues, computes the quality
score, and packages everything into a `ValidationResult` that the
report generator and CLI consume.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

import pandas as pd

from .config_loader import DQConfig
from .issue import Issue
from .logger import get_logger
from .scoring import CHECK_TYPES, ScoreBreakdown, compute_score
from .validators import (
    check_dates,
    check_dtype,
    check_duplicates,
    check_emails,
    check_nulls,
    check_outliers,
)

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    dataset_name: str
    run_timestamp: str
    total_rows: int
    total_columns: int
    issues: List[Issue] = field(default_factory=list)
    score: ScoreBreakdown = None
    column_summary: Dict[str, Dict] = field(default_factory=dict)

    def issues_for_column(self, column: str) -> List[Issue]:
        return [i for i in self.issues if i.column == column]

    def to_dict(self) -> dict:
        return {
            "dataset_name": self.dataset_name,
            "run_timestamp": self.run_timestamp,
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "total_issues": len(self.issues),
            "score": self.score.to_dict() if self.score else None,
            "column_summary": self.column_summary,
            "issues": [i.to_dict() for i in self.issues],
        }


class ValidationEngine:
    """Runs all configured checks against a DataFrame."""

    def __init__(self, config: DQConfig):
        self.config = config

    def run(self, df: pd.DataFrame) -> ValidationResult:
        logger.info(
            "Starting validation run for dataset '%s' (%d rows, %d columns).",
            self.config.dataset_name,
            len(df),
            len(df.columns),
        )

        issues: List[Issue] = []
        column_summary: Dict[str, Dict] = {}
        checked_columns_per_type: Dict[str, int] = {ct: 0 for ct in CHECK_TYPES}

        for col_name, rule in self.config.columns.items():
            col_issue_counts: Dict[str, int] = {}

            if not rule.nullable:
                null_issues = check_nulls(df, col_name)
                issues.extend(null_issues)
                col_issue_counts["null"] = len(null_issues)
                checked_columns_per_type["null"] += 1

            if rule.type == "date":
                date_issues = check_dates(df, col_name, rule.date_format)
                issues.extend(date_issues)
                col_issue_counts["invalid_date"] = len(date_issues)
                checked_columns_per_type["invalid_date"] += 1

            if rule.check_email:
                email_issues = check_emails(df, col_name)
                issues.extend(email_issues)
                col_issue_counts["invalid_email"] = len(email_issues)
                checked_columns_per_type["invalid_email"] += 1

            if rule.type:
                dtype_issues = check_dtype(df, col_name, rule.type)
                issues.extend(dtype_issues)
                col_issue_counts["dtype"] = len(dtype_issues)
                checked_columns_per_type["dtype"] += 1

            if rule.outlier_check:
                outlier_issues = check_outliers(
                    df, col_name, rule.outlier_method, rule.outlier_threshold
                )
                issues.extend(outlier_issues)
                col_issue_counts["outlier"] = len(outlier_issues)
                checked_columns_per_type["outlier"] += 1

            column_summary[col_name] = {
                "type": rule.type,
                "nullable": rule.nullable,
                "issue_counts": col_issue_counts,
                "total_issues": sum(col_issue_counts.values()),
            }

        if self.config.duplicate_rule.enabled:
            dup_issues = check_duplicates(df, self.config.duplicate_rule.subset)
            issues.extend(dup_issues)
            checked_columns_per_type["duplicate"] = 1

        score = compute_score(
            issues=issues,
            total_rows=len(df),
            checked_columns_per_type=checked_columns_per_type,
            weights=self.config.weights,
        )

        result = ValidationResult(
            dataset_name=self.config.dataset_name,
            run_timestamp=datetime.now(timezone.utc).isoformat(),
            total_rows=len(df),
            total_columns=len(df.columns),
            issues=issues,
            score=score,
            column_summary=column_summary,
        )

        logger.info(
            "Validation complete: %d issues found, overall score %.2f/100.",
            len(issues),
            score.overall_score,
        )
        return result
