"""
Invalid email format check.

Uses a pragmatic (not fully RFC 5322 compliant) regex that catches the
vast majority of real-world malformed emails: missing '@', missing
domain, missing TLD, illegal characters, spaces, etc.
"""

import re
from typing import List

import pandas as pd

from ..issue import Issue, SEVERITY_MEDIUM

EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9_!#$%&'*+/=?`{|}~^.-]+"
    r"@"
    r"[A-Za-z0-9.-]+"
    r"\.[A-Za-z]{2,}$"
)


def is_valid_email(value: str) -> bool:
    """Return True if `value` looks like a syntactically valid email."""
    if not isinstance(value, str):
        return False
    value = value.strip()
    if " " in value or value.count("@") != 1:
        return False
    return bool(EMAIL_REGEX.match(value))


def check_emails(df: pd.DataFrame, column: str) -> List[Issue]:
    """Return one Issue per row with a malformed email in `column`."""
    if column not in df.columns:
        return [
            Issue(
                check_type="invalid_email",
                column=column,
                row_index=None,
                message=f"Column '{column}' is missing from the dataset.",
                severity=SEVERITY_MEDIUM,
            )
        ]

    issues: List[Issue] = []
    for idx, value in df[column].items():
        if pd.isna(value):
            continue
        if not is_valid_email(value):
            issues.append(
                Issue(
                    check_type="invalid_email",
                    column=column,
                    row_index=int(idx),
                    message=f"Invalid email format in column '{column}'.",
                    severity=SEVERITY_MEDIUM,
                    value=value,
                )
            )
    return issues
