"""Unit tests for src.validators.outlier_check"""

import pandas as pd
import pytest

from src.validators.outlier_check import check_outliers


def test_no_outliers_in_tight_distribution(clean_df):
    issues = check_outliers(clean_df, "age", method="iqr", threshold=1.5)
    assert issues == []


def test_detects_iqr_outlier():
    df = pd.DataFrame({"val": [10, 12, 11, 13, 12, 11, 10, 12, 500]})
    issues = check_outliers(df, "val", method="iqr", threshold=1.5)
    flagged_rows = {i.row_index for i in issues}
    assert 8 in flagged_rows


def test_detects_zscore_outlier():
    df = pd.DataFrame({"val": [10, 12, 11, 13, 12, 11, 10, 12, 500]})
    issues = check_outliers(df, "val", method="zscore", threshold=2.0)
    flagged_rows = {i.row_index for i in issues}
    assert 8 in flagged_rows


def test_skips_when_sample_too_small():
    df = pd.DataFrame({"val": [10, 500]})
    issues = check_outliers(df, "val", method="iqr", threshold=1.5)
    assert issues == []


def test_non_numeric_values_are_ignored_not_errored():
    df = pd.DataFrame({"val": [10, 12, 11, 13, 12, "garbage", 11, 10, 12]})
    issues = check_outliers(df, "val", method="iqr", threshold=1.5)
    # Should not raise, and "garbage" itself isn't a numeric outlier candidate.
    assert isinstance(issues, list)


def test_invalid_method_raises_value_error():
    df = pd.DataFrame({"val": [1, 2, 3, 4, 5, 6]})
    with pytest.raises(ValueError):
        check_outliers(df, "val", method="not_a_method", threshold=1.5)


def test_missing_column_reports_issue(clean_df):
    issues = check_outliers(clean_df, "nope")
    assert len(issues) == 1
    assert issues[0].check_type == "outlier"


def test_zero_variance_column_returns_no_outliers():
    df = pd.DataFrame({"val": [5, 5, 5, 5, 5, 5]})
    issues = check_outliers(df, "val", method="zscore", threshold=3.0)
    assert issues == []
