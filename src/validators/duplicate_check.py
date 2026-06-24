"""
Duplicate record check.

Flags duplicate rows, either based on a subset of key columns (e.g. a
primary key like `customer_id`) or the entire row if no subset is
configured. The first occurrence of a value is considered the
"original"; subsequent occurrences are flagged as duplicates.
"""

from typing import List, Optional

import pandas as pd

from ..issue import Issue, SEVERITY_MEDIUM


def check_duplicates(
    df: pd.DataFrame, subset: Optional[List[str]] = None
) -> List[Issue]:
    """Return one Issue per duplicate row (excluding the first occurrence)."""
    if subset:
        missing = [c for c in subset if c not in df.columns]
        if missing:
            return [
                Issue(
                    check_type="duplicate",
                    column=",".join(missing),
                    row_index=None,
                    message=f"Duplicate-check key column(s) missing: {missing}",
                    severity=SEVERITY_MEDIUM,
                )
            ]
        dup_mask = df.duplicated(subset=subset, keep="first")
        key_desc = ", ".join(subset)
    else:
        dup_mask = df.duplicated(keep="first")
        key_desc = "all columns"

    issues: List[Issue] = []
    for idx in df.index[dup_mask]:
        if subset:
            key_values = {c: df.at[idx, c] for c in subset}
        else:
            key_values = None
        issues.append(
            Issue(
                check_type="duplicate",
                column=key_desc,
                row_index=int(idx),
                message=f"Duplicate record detected based on ({key_desc}).",
                severity=SEVERITY_MEDIUM,
                value=key_values,
            )
        )
    return issues
