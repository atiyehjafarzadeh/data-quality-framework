"""Unit tests for src.validators.null_check"""

import pandas as pd

from src.validators.null_check import check_nulls


def test_no_nulls_returns_empty(clean_df):
    issues = check_nulls(clean_df, "full_name")
    assert issues == []


def test_detects_nan(dirty_df):
    issues = check_nulls(dirty_df, "full_name")
    assert len(issues) == 1
    assert issues[0].check_type == "null"
    assert issues[0].row_index == 1


def test_detects_none_value():
    df = pd.DataFrame({"col": ["a", None, "c"]})
    issues = check_nulls(df, "col")
    assert len(issues) == 1
    assert issues[0].row_index == 1


def test_detects_whitespace_only_string():
    df = pd.DataFrame({"col": ["a", "   ", "c"]})
    issues = check_nulls(df, "col")
    assert len(issues) == 1
    assert issues[0].row_index == 1


def test_missing_column_returns_high_severity_issue(clean_df):
    issues = check_nulls(clean_df, "nonexistent_column")
    assert len(issues) == 1
    assert issues[0].severity == "HIGH"


def test_severity_is_high_for_nulls(dirty_df):
    issues = check_nulls(dirty_df, "email")
    assert all(i.severity == "HIGH" for i in issues)
