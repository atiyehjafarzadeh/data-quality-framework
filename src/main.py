"""
Command-line entry point for the Data Quality Framework.

Usage:
    python -m src.main --data data/sample_dirty.csv --config config/rules.yaml \
        --output-dir reports/

This loads the dataset and rules, runs the validation engine, and writes
out the three report artifacts (HTML report, dashboard JSON, metrics
JSON) into the output directory.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from .config_loader import load_config
from .engine import ValidationEngine
from .logger import get_logger
from .report_generator import (
    generate_dashboard_data,
    generate_html_report,
    generate_metrics_summary,
)

logger = get_logger(__name__)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Data Quality Framework against a dataset."
    )
    parser.add_argument(
        "--data", required=True, help="Path to the input CSV dataset."
    )
    parser.add_argument(
        "--config", required=True, help="Path to the YAML rules config file."
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory to write reports into (default: reports/).",
    )
    return parser.parse_args(argv)


def run(data_path: str, config_path: str, output_dir: str) -> int:
    data_path = Path(data_path)
    output_dir = Path(output_dir)

    if not data_path.exists():
        logger.error("Data file not found: %s", data_path)
        return 1

    logger.info("Loading config from %s", config_path)
    config = load_config(config_path)

    logger.info("Loading dataset from %s", data_path)
    df = pd.read_csv(data_path)

    engine = ValidationEngine(config)
    result = engine.run(df)

    base_name = data_path.stem
    html_path = output_dir / f"{base_name}_report.html"
    dashboard_path = output_dir / f"{base_name}_dashboard.json"
    metrics_path = output_dir / f"{base_name}_metrics.json"

    generate_html_report(result, html_path)
    generate_dashboard_data(result, dashboard_path)
    generate_metrics_summary(result, metrics_path)

    print(f"\nValidation complete for dataset: {config.dataset_name}")
    print(f"  Overall score : {result.score.overall_score:.2f}/100")
    print(f"  Total issues  : {len(result.issues)}")
    print(f"  HTML report   : {html_path}")
    print(f"  Dashboard data: {dashboard_path}")
    print(f"  Metrics JSON  : {metrics_path}\n")

    return 0


def main(argv=None) -> int:
    args = parse_args(argv)
    return run(args.data, args.config, args.output_dir)


if __name__ == "__main__":
    sys.exit(main())
