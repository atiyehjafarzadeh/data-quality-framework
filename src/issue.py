"""
Core data model for validation findings.

Every check in the framework (null, duplicate, date, email, dtype,
outlier) emits a list of `Issue` objects. This gives the rest of the
framework (scoring, reporting, logging) a single, uniform shape to work
with regardless of which check produced the finding.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


# Severity levels used consistently across the framework.
SEVERITY_LOW = "LOW"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_HIGH = "HIGH"

VALID_SEVERITIES = {SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH}


@dataclass
class Issue:
    """A single data quality finding.

    Attributes:
        check_type: Category of the check, e.g. "null", "duplicate",
            "invalid_date", "invalid_email", "dtype", "outlier".
        column: Column the issue was found in. None for row-level /
            dataset-level issues (e.g. duplicate rows).
        row_index: The pandas index of the offending row, if applicable.
        message: Human readable description of the problem.
        severity: One of LOW / MEDIUM / HIGH.
        value: The offending value itself (for debugging / reporting).
    """

    check_type: str
    column: Optional[str]
    row_index: Optional[int]
    message: str
    severity: str = SEVERITY_MEDIUM
    value: Any = field(default=None)

    def __post_init__(self) -> None:
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(
                f"Invalid severity '{self.severity}'. "
                f"Must be one of {sorted(VALID_SEVERITIES)}."
            )

    def to_dict(self) -> dict:
        return {
            "check_type": self.check_type,
            "column": self.column,
            "row_index": self.row_index,
            "message": self.message,
            "severity": self.severity,
            "value": None if self.value is None else str(self.value),
        }
