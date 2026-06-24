"""Unit tests for src.validators.email_check"""

import pandas as pd

from src.validators.email_check import check_emails, is_valid_email


def test_valid_emails():
    assert is_valid_email("alice@example.com")
    assert is_valid_email("a.b+c@sub.example.co.uk")


def test_invalid_emails():
    assert not is_valid_email("not-an-email")
    assert not is_valid_email("missing@domain")
    assert not is_valid_email("spaced out@example.com")
    assert not is_valid_email("double@@example.com")
    assert not is_valid_email(123)
    assert not is_valid_email(None)


def test_no_invalid_emails_returns_empty(clean_df):
    issues = check_emails(clean_df, "email")
    assert issues == []


def test_detects_invalid_emails(dirty_df):
    issues = check_emails(dirty_df, "email")
    flagged_rows = {i.row_index for i in issues}
    assert 2 in flagged_rows  # not-an-email
    assert 3 in flagged_rows  # missing@domain
    assert 5 in flagged_rows  # spaced out@example.com


def test_null_emails_are_skipped(dirty_df):
    # row 4 is None and should not be flagged by the email checker.
    issues = check_emails(dirty_df, "email")
    flagged_rows = {i.row_index for i in issues}
    assert 4 not in flagged_rows


def test_missing_column_reports_issue(clean_df):
    issues = check_emails(clean_df, "nope")
    assert len(issues) == 1
    assert issues[0].check_type == "invalid_email"
