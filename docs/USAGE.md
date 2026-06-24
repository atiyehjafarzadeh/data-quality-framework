# Usage Guide

## CLI Usage

```bash
python -m src.main --data <path_to_csv> --config <path_to_yaml> --output-dir <path_to_output_dir>
```

| Flag | Required | Description |
|---|---|---|
| `--data` | yes | Path to the CSV file to validate. |
| `--config` | yes | Path to the YAML rules file. |
| `--output-dir` | no (default: `reports`) | Directory to write the HTML report and JSON outputs into. |

### Example

```bash
python -m src.main \
  --data data/sample_dirty.csv \
  --config config/rules.yaml \
  --output-dir reports/
```

This produces:

- `reports/sample_dirty_report.html`
- `reports/sample_dirty_dashboard.json`
- `reports/sample_dirty_metrics.json`
- `reports/dq_framework.log` (appended to on every run)

## Programmatic Usage

```python
import pandas as pd
from src.config_loader import load_config
from src.engine import ValidationEngine
from src.report_generator import (
    generate_html_report,
    generate_dashboard_data,
    generate_metrics_summary,
)

config = load_config("config/rules.yaml")
df = pd.read_csv("data/sample_dirty.csv")

result = ValidationEngine(config).run(df)

print(result.score.overall_score)        # e.g. 80.75
print(result.score.per_check_score)       # {'null': 92.86, 'duplicate': 96.15, ...}
print(len(result.issues))                 # 17

generate_html_report(result, "reports/my_report.html")
generate_dashboard_data(result, "reports/my_dashboard.json")
generate_metrics_summary(result, "reports/my_metrics.json")
```

## Inspecting Individual Issues

```python
for issue in result.issues:
    print(issue.check_type, issue.column, issue.row_index, issue.severity, issue.message)
```

Filter issues for a specific column:

```python
email_issues = result.issues_for_column("email")
```

## Running Validators Standalone

Every check is a plain function and can be called directly without the
engine, which is useful for ad-hoc exploration or notebook usage:

```python
from src.validators import check_nulls, check_emails, check_outliers

null_issues = check_nulls(df, "email")
email_issues = check_emails(df, "email")
outlier_issues = check_outliers(df, "age", method="iqr", threshold=1.5)
```

## Running the Test Suite

```bash
pip install pytest
pytest tests/ -v
```

To run a single test file:

```bash
pytest tests/test_outlier_check.py -v
```

To run with coverage (requires `pytest-cov`):

```bash
pip install pytest-cov
pytest tests/ --cov=src --cov-report=term-missing
```

## Integrating Into a Pipeline / CI

A typical pattern is to fail a pipeline step if the quality score
drops below a threshold:

```python
result = ValidationEngine(config).run(df)
if result.score.overall_score < 85:
    raise SystemExit(
        f"Data quality gate failed: score {result.score.overall_score:.1f} < 85"
    )
```

Combine this with `generate_metrics_summary()` to persist a JSON
snapshot per run, which can be diffed over time to catch quality
regressions early.
