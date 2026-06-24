"""Unit tests for src.engine.ValidationEngine"""

from src.engine import ValidationEngine


def test_clean_dataframe_yields_high_score(clean_df, base_config):
    engine = ValidationEngine(base_config)
    result = engine.run(clean_df)
    assert result.score.overall_score > 90
    assert result.total_rows == len(clean_df)
    assert result.total_columns == len(clean_df.columns)


def test_dirty_dataframe_finds_all_injected_issues(dirty_df, base_config):
    engine = ValidationEngine(base_config)
    result = engine.run(dirty_df)

    check_types_found = {issue.check_type for issue in result.issues}
    assert "null" in check_types_found
    assert "duplicate" in check_types_found
    assert "invalid_date" in check_types_found
    assert "invalid_email" in check_types_found
    assert "dtype" in check_types_found

    assert result.score.overall_score < 90


def test_column_summary_is_populated(dirty_df, base_config):
    engine = ValidationEngine(base_config)
    result = engine.run(dirty_df)
    assert "email" in result.column_summary
    assert result.column_summary["email"]["total_issues"] > 0


def test_issues_for_column_filters_correctly(dirty_df, base_config):
    engine = ValidationEngine(base_config)
    result = engine.run(dirty_df)
    email_issues = result.issues_for_column("email")
    assert all(i.column == "email" for i in email_issues)


def test_to_dict_is_json_serializable_shape(dirty_df, base_config):
    import json

    engine = ValidationEngine(base_config)
    result = engine.run(dirty_df)
    payload = result.to_dict()
    # Should not raise -- proves every value is JSON-serializable.
    json.dumps(payload)
    assert payload["dataset_name"] == "test_dataset"
    assert payload["total_issues"] == len(result.issues)


def test_duplicate_check_disabled_skips_duplicates(dirty_df, base_config_dict):
    from src.config_loader import DQConfig

    base_config_dict["checks"]["duplicates"]["enabled"] = False
    config = DQConfig.from_dict(base_config_dict)
    engine = ValidationEngine(config)
    result = engine.run(dirty_df)
    assert all(i.check_type != "duplicate" for i in result.issues)
