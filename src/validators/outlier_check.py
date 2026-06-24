"""
Outlier detection check.

Supports two standard statistical methods for numeric columns:

- IQR (Interquartile Range): flags values outside
  [Q1 - k*IQR, Q3 + k*IQR], default k=1.5 (the classic Tukey fence).
- Z-score: flags values whose absolute z-score exceeds a threshold,
  default 3.0 standard deviations from the mean.

Both methods require at least a handful of numeric data points to be
meaningful; columns with too few non-null numeric values are skipped
rather than producing noisy/meaningless flags.
"""

from typing import List

import numpy as np
import pandas as pd

from ..issue import Issue, SEVERITY_LOW

MIN_SAMPLE_SIZE = 5


def _iqr_bounds(series: pd.Series, k: float):
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr


def check_outliers(
    df: pd.DataFrame,
    column: str,
    method: str = "iqr",
    threshold: float = 1.5,
) -> List[Issue]:
    """Return one Issue per row considered a statistical outlier."""
    if column not in df.columns:
        return [
            Issue(
                check_type="outlier",
                column=column,
                row_index=None,
                message=f"Column '{column}' is missing from the dataset.",
                severity=SEVERITY_LOW,
            )
        ]

    numeric = pd.to_numeric(df[column], errors="coerce")
    valid = numeric.dropna()
    if len(valid) < MIN_SAMPLE_SIZE:
        return []

    issues: List[Issue] = []

    if method == "iqr":
        lower, upper = _iqr_bounds(valid, threshold)
        outlier_mask = (numeric < lower) | (numeric > upper)
        detail = f"outside [{lower:.2f}, {upper:.2f}] (IQR x{threshold})"
    elif method == "zscore":
        mean = valid.mean()
        std = valid.std(ddof=0)
        if std == 0:
            return []
        z_scores = (numeric - mean) / std
        outlier_mask = z_scores.abs() > threshold
        detail = f"z-score beyond +/-{threshold}"
    else:
        raise ValueError(f"Unsupported outlier method: {method}")

    outlier_mask = outlier_mask.fillna(False)
    for idx in df.index[outlier_mask]:
        issues.append(
            Issue(
                check_type="outlier",
                column=column,
                row_index=int(idx),
                message=f"Statistical outlier in column '{column}' ({detail}).",
                severity=SEVERITY_LOW,
                value=df.at[idx, column],
            )
        )
    return issues
