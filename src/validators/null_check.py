"""
Null value check.

Flags missing values (NaN, None, pandas.NaT, empty string after
stripping) in columns marked as non-nullable in the config.
"""

from typing import List

import pandas as pd

from ..issue import Issue, SEVERITY_HIGH


def _is_blank(value) -> bool:
    """Treat NaN/None/NaT and whitespace-only strings as 'null'."""
    if pd.isna(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def check_nulls(df: pd.DataFrame, column: str) -> List[Issue]:
    """Return one Issue per row where `column` is null/blank."""
    if column not in df.columns:
        return [
            Issue(
                check_type="null",
                column=column,
                row_index=None,
                message=f"Column '{column}' is missing from the dataset.",
                severity=SEVERITY_HIGH,
            )
        ]

    issues: List[Issue] = []
    mask = df[column].apply(_is_blank)
    for idx in df.index[mask]:
        issues.append(
            Issue(
                check_type="null",
                column=column,
                row_index=int(idx),
                message=f"Null/blank value found in required column '{column}'.",
                severity=SEVERITY_HIGH,
                value=df.at[idx, column],
            )
        )
    return issues
