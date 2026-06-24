"""Statistical outlier detection for numeric columns.

Supports two interchangeable methods, selectable per-column in config:
  - "zscore": flags values more than `threshold` standard deviations from
    the mean. Simple and fast, but sensitive to the outliers themselves
    skewing mean/std.
  - "iqr": flags values outside [Q1 - threshold*IQR, Q3 + threshold*IQR].
    More robust to extreme values; the classic boxplot rule (threshold=1.5).
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from src.models import CheckResult, CheckStatus

CHECK_NAME = "outlier_check"


def _zscore_outliers(series: pd.Series, threshold: float) -> pd.Series:
    mean = series.mean()
    std = series.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series(False, index=series.index)
    z = (series - mean).abs() / std
    return z > threshold


def _iqr_outliers(series: pd.Series, threshold: float) -> pd.Series:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0 or pd.isna(iqr):
        return pd.Series(False, index=series.index)
    lower = q1 - threshold * iqr
    upper = q3 + threshold * iqr
    return (series < lower) | (series > upper)


_METHODS = {
    "zscore": _zscore_outliers,
    "iqr": _iqr_outliers,
}


def check_outliers(
    df: pd.DataFrame,
    column_rules: List[Dict[str, Any]],
    weight: float = 0.0,
) -> List[CheckResult]:
    results: List[CheckResult] = []
    total = len(df)

    for rule in column_rules:
        col = rule["column"]
        method = rule.get("method", "zscore")
        threshold = float(rule.get("threshold", 3.0))

        if col not in df.columns:
            results.append(
                CheckResult(
                    check_name=CHECK_NAME,
                    target=col,
                    status=CheckStatus.ERROR,
                    total_records=total,
                    failed_records=0,
                    weight=weight,
                    message=f"Column '{col}' not found in dataset.",
                )
            )
            continue

        method_fn = _METHODS.get(method)
        if method_fn is None:
            results.append(
                CheckResult(
                    check_name=CHECK_NAME,
                    target=col,
                    status=CheckStatus.ERROR,
                    total_records=total,
                    failed_records=0,
                    weight=weight,
                    message=f"Unknown outlier method '{method}' for column '{col}'.",
                )
            )
            continue

        numeric_series = pd.to_numeric(df[col], errors="coerce")
        valid_mask = numeric_series.notna()
        outlier_mask = pd.Series(False, index=df.index)
        if valid_mask.sum() >= 2:  # need at least 2 points for std/IQR to mean anything
            outlier_mask.loc[valid_mask] = method_fn(numeric_series[valid_mask], threshold)

        outlier_count = int(outlier_mask.sum())
        outlier_pct = round((outlier_count / total) * 100, 4) if total else 0.0

        sample_idx = df.index[outlier_mask][:10].tolist()
        details = [
            {"row_index": int(i), "value": str(df[col].loc[i])} for i in sample_idx
        ]

        # Outliers are flagged as WARN rather than FAIL by default - they are
        # often legitimate extreme-but-valid data points that deserve review,
        # not automatic rejection. Adjust to FAIL in your own pipeline if
        # outliers should hard-block a dataset.
        status = CheckStatus.PASS if outlier_count == 0 else CheckStatus.WARN

        results.append(
            CheckResult(
                check_name=CHECK_NAME,
                target=col,
                status=status,
                total_records=total,
                failed_records=outlier_count,
                weight=weight,
                message=(
                    f"{outlier_count} outlier(s) ({outlier_pct}%) detected in '{col}' "
                    f"using {method} (threshold={threshold})."
                ),
                details=details,
                extra={"method": method, "threshold": threshold, "outlier_pct": outlier_pct},
            )
        )

    return results
