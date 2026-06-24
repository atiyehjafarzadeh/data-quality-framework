"""Unit tests for src.validators.dtype_check"""

import pandas as pd

from src.validators.dtype_check import check_dtype


def test_valid_int_column_returns_empty(clean_df):
    issues = check_dtype(clean_df, "customer_id", "int")
    assert issues == []


def test_detects_non_numeric_value_in_int_column(dirty_df):
    issues = check_dtype(dirty_df, "customer_id", "int")
    assert len(issues) == 1
    assert issues[0].row_index == 5  # "abc"


def test_detects_non_numeric_value_in_float_column(dirty_df):
    issues = check_dtype(dirty_df, "annual_spend", "float")
    assert len(issues) == 1
    assert issues[0].row_index == 7  # "N/A"


def test_str_type_rejects_non_string_values():
    df = pd.DataFrame({"col": ["a", 123, "c"]})
    issues = check_dtype(df, "col", "str")
    assert len(issues) == 1
    assert issues[0].row_index == 1


def test_bool_type_accepts_common_representations():
    df = pd.DataFrame({"col": ["true", "False", "yes", "n", True, False]})
    issues = check_dtype(df, "col", "bool")
    assert issues == []


def test_bool_type_rejects_invalid_value():
    df = pd.DataFrame({"col": ["true", "maybe"]})
    issues = check_dtype(df, "col", "bool")
    assert len(issues) == 1
    assert issues[0].row_index == 1


def test_date_type_validates_parseable_dates():
    df = pd.DataFrame({"col": ["2023-01-01", "garbage"]})
    issues = check_dtype(df, "col", "date")
    assert len(issues) == 1
    assert issues[0].row_index == 1


def test_nulls_are_skipped_by_dtype_checker():
    df = pd.DataFrame({"col": [1, None, 3]})
    issues = check_dtype(df, "col", "int")
    assert issues == []


def test_missing_column_reports_issue(clean_df):
    issues = check_dtype(clean_df, "nope", "int")
    assert len(issues) == 1
    assert issues[0].check_type == "dtype"
