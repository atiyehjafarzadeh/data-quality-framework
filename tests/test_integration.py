"""
End-to-end integration tests: run the full pipeline (config -> engine ->
reports) against the actual sample CSV files shipped in data/, the same
way a real user would via src/main.py.
"""

from pathlib import Path

import pandas as pd

from src.config_loader import load_config
from src.engine import ValidationEngine
from src.report_generator import (
    generate_dashboard_data,
    generate_html_report,
    generate_metrics_summary,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "rules.yaml"
CLEAN_DATA_PATH = PROJECT_ROOT / "data" / "sample_clean.csv"
DIRTY_DATA_PATH = PROJECT_ROOT / "data" / "sample_dirty.csv"


def test_sample_clean_dataset_scores_high():
    config = load_config(CONFIG_PATH)
    df = pd.read_csv(CLEAN_DATA_PATH)
    result = ValidationEngine(config).run(df)
    assert result.score.overall_score >= 80


def test_sample_dirty_dataset_has_issues_and_lower_score():
    config = load_config(CONFIG_PATH)
    df = pd.read_csv(DIRTY_DATA_PATH)
    result = ValidationEngine(config).run(df)
    assert len(result.issues) > 0

    check_types_found = {issue.check_type for issue in result.issues}
    assert {"null", "duplicate", "invalid_date", "invalid_email", "dtype", "outlier"} & check_types_found


def test_full_pipeline_writes_all_three_report_files(tmp_path):
    config = load_config(CONFIG_PATH)
    df = pd.read_csv(DIRTY_DATA_PATH)
    result = ValidationEngine(config).run(df)

    html_path = generate_html_report(result, tmp_path / "out.html")
    dashboard_path = generate_dashboard_data(result, tmp_path / "out_dashboard.json")
    metrics_path = generate_metrics_summary(result, tmp_path / "out_metrics.json")

    assert html_path.exists()
    assert dashboard_path.exists()
    assert metrics_path.exists()
