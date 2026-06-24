"""Unit tests for src.validators.duplicate_check"""

import pandas as pd

from src.validators.duplicate_check import check_duplicates


def test_no_duplicates_with_unique_subset(clean_df):
    issues = check_duplicates(clean_df, subset=["customer_id"])
    assert issues == []


def test_detects_duplicate_subset(dirty_df):
    issues = check_duplicates(dirty_df, subset=["customer_id"])
    # customer_id=2 appears twice (rows 1 and 2); row 2 is flagged.
    assert len(issues) == 1
    assert issues[0].row_index == 2


def test_first_occurrence_is_not_flagged():
    df = pd.DataFrame({"id": [1, 1, 2, 3]})
    issues = check_duplicates(df, subset=["id"])
    flagged_indices = [i.row_index for i in issues]
    assert 0 not in flagged_indices
    assert 1 in flagged_indices


def test_whole_row_duplicate_detection_without_subset():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    issues = check_duplicates(df, subset=None)
    assert len(issues) == 1
    assert issues[0].row_index == 1


def test_missing_subset_column_reports_issue(clean_df):
    issues = check_duplicates(clean_df, subset=["does_not_exist"])
    assert len(issues) == 1
    assert "missing" in issues[0].message.lower()


def test_multiple_duplicate_groups():
    df = pd.DataFrame({"id": [1, 1, 2, 2, 2, 3]})
    issues = check_duplicates(df, subset=["id"])
    # id=1 -> 1 dup, id=2 -> 2 dups, id=3 -> 0 dups => 3 total
    assert len(issues) == 3
