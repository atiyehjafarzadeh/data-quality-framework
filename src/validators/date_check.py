"""
Invalid date check.

Attempts to parse every non-null value in a date column against an
expected format (if provided) or pandas' general datetime inference
otherwise. Values that fail to parse are flagged.
"""

from typing import List, Optional

import pandas as pd

from ..issue import Issue, SEVERITY_MEDIUM


def _parse_one(value, date_format: Optional[str]) -> bool:
    """Return True if `value` parses as a valid date."""
    if pd.isna(value):
        return True  # Null dates are the null-checker's responsibility.
    try:
        if date_format:
            pd.to_datetime(str(value), format=date_format, errors="raise")
        else:
            pd.to_datetime(str(value), errors="raise")
        return True
    except (ValueError, TypeError):
        return False


def check_dates(
    df: pd.DataFrame, column: str, date_format: Optional[str] = None
) -> List[Issue]:
    """Return one Issue per row with an unparseable date in `column`."""
    if column not in df.columns:
        return [
            Issue(
                check_type="invalid_date",
                column=column,
                row_index=None,
                message=f"Column '{column}' is missing from the dataset.",
                severity=SEVERITY_MEDIUM,
            )
        ]

    issues: List[Issue] = []
    for idx, value in df[column].items():
        if not _parse_one(value, date_format):
            fmt_hint = f" (expected format: {date_format})" if date_format else ""
            issues.append(
                Issue(
                    check_type="invalid_date",
                    column=column,
                    row_index=int(idx),
                    message=f"Invalid date value in column '{column}'{fmt_hint}.",
                    severity=SEVERITY_MEDIUM,
                    value=value,
                )
            )
    return issues
