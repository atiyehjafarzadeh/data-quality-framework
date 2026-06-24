"""Unit tests for src.validators.date_check"""

import pandas as pd

from src.validators.date_check import check_dates


def test_all_valid_dates_returns_empty(clean_df):
    issues = check_dates(clean_df, "signup_date", date_format="%Y-%m-%d")
    assert issues == []


def test_detects_invalid_date_format(dirty_df):
    issues = check_dates(dirty_df, "signup_date", date_format="%Y-%m-%d")
    flagged_rows = {i.row_index for i in issues}
    # row 1 = "not-a-date", row 3 = "2023-13-45" (invalid month)
    assert 1 in flagged_rows
    assert 3 in flagged_rows


def test_null_dates_are_skipped_by_date_checker(dirty_df):
    # row 6 is None -- the date checker should not flag nulls;
    # that's the null checker's job.
    issues = check_dates(dirty_df, "signup_date", date_format="%Y-%m-%d")
    flagged_rows = {i.row_index for i in issues}
    assert 6 not in flagged_rows


def test_generic_parsing_without_format():
    df = pd.DataFrame({"d": ["2023-01-01", "January 5, 2023", "garbage"]})
    issues = check_dates(df, "d", date_format=None)
    flagged_rows = {i.row_index for i in issues}
    assert 2 in flagged_rows
    assert 0 not in flagged_rows


def test_missing_column_reports_issue(clean_df):
    issues = check_dates(clean_df, "nope", date_format="%Y-%m-%d")
    assert len(issues) == 1
    assert issues[0].check_type == "invalid_date"
