"""
Data type validation check.

Verifies that every non-null value in a column can legitimately be
interpreted as the expected type declared in the config (int, float,
str, bool, date). This is intentionally value-level rather than
dtype-level, since pandas often loads numeric-looking columns as
`object` dtype when even a single row is malformed -- checking the
declared pandas dtype alone would miss exactly the rows we care about.
"""

from typing import List

import pandas as pd

from ..issue import Issue, SEVERITY_MEDIUM

_BOOL_TRUE = {"true", "1", "yes", "y"}
_BOOL_FALSE = {"false", "0", "no", "n"}


def _matches_type(value, expected_type: str) -> bool:
    if pd.isna(value):
        return True  # nulls are the null-checker's responsibility

    if expected_type == "int":
        try:
            f = float(value)
            return f.is_integer()
        except (ValueError, TypeError):
            return False

    if expected_type == "float":
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    if expected_type == "bool":
        if isinstance(value, bool):
            return True
        return str(value).strip().lower() in (_BOOL_TRUE | _BOOL_FALSE)

    if expected_type == "str":
        return isinstance(value, str)

    if expected_type == "date":
        try:
            pd.to_datetime(str(value), errors="raise")
            return True
        except (ValueError, TypeError):
            return False

    # Unknown/unsupported type declaration: nothing to validate against.
    return True


def check_dtype(df: pd.DataFrame, column: str, expected_type: str) -> List[Issue]:
    """Return one Issue per row whose value cannot be cast to `expected_type`."""
    if column not in df.columns:
        return [
            Issue(
                check_type="dtype",
                column=column,
                row_index=None,
                message=f"Column '{column}' is missing from the dataset.",
                severity=SEVERITY_MEDIUM,
            )
        ]

    issues: List[Issue] = []
    for idx, value in df[column].items():
        if not _matches_type(value, expected_type):
            issues.append(
                Issue(
                    check_type="dtype",
                    column=column,
                    row_index=int(idx),
                    message=(
                        f"Value in column '{column}' does not match expected "
                        f"type '{expected_type}'."
                    ),
                    severity=SEVERITY_MEDIUM,
                    value=value,
                )
            )
    return issues
