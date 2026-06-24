"""Unit tests for src.report_generator"""

import json

from src.engine import ValidationEngine
from src.report_generator import (
    generate_dashboard_data,
    generate_html_report,
    generate_metrics_summary,
)


def test_html_report_is_created_and_contains_dataset_name(
    tmp_path, dirty_df, base_config
):
    engine = ValidationEngine(base_config)
    result = engine.run(dirty_df)

    output_path = tmp_path / "report.html"
    path = generate_html_report(result, output_path)

    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "test_dataset" in content
    assert "<html" in content.lower()


def test_dashboard_data_is_valid_json(tmp_path, dirty_df, base_config):
    engine = ValidationEngine(base_config)
    result = engine.run(dirty_df)

    output_path = tmp_path / "dashboard.json"
    path = generate_dashboard_data(result, output_path)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["dataset_name"] == "test_dataset"
    assert "overall_score" in payload
    assert "check_scores" in payload
    assert "top_problem_columns" in payload


def test_metrics_summary_is_valid_json_and_includes_all_issues(
    tmp_path, dirty_df, base_config
):
    engine = ValidationEngine(base_config)
    result = engine.run(dirty_df)

    output_path = tmp_path / "metrics.json"
    path = generate_metrics_summary(result, output_path)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["total_issues"] == len(result.issues)
    assert len(payload["issues"]) == len(result.issues)


def test_report_handles_zero_issues_gracefully(tmp_path, clean_df, base_config):
    engine = ValidationEngine(base_config)
    result = engine.run(clean_df)

    html_path = generate_html_report(result, tmp_path / "report.html")
    content = html_path.read_text(encoding="utf-8")
    assert "No issues found" in content or result.issues
