# Data Quality Framework

A config-driven Python framework for automatically validating incoming
datasets, scoring their quality, and generating HTML/JSON reports.

Built with **pandas**, **PyYAML**, and **pytest**.

---

## Features

| Feature | Description |
|---|---|
| **Validation engine** | Orchestrates all checks based on a YAML config, no code changes needed to validate a new dataset |
| **Six built-in checks** | Null values, duplicate records, invalid dates, invalid emails, data type mismatches, statistical outliers |
| **Quality scoring** | Weighted 0–100 score + letter grade (A–F), per-check breakdown |
| **HTML reports** | Self-contained, styled HTML report per run |
| **Dashboard data** | Compact JSON payload for BI tools / dashboard widgets |
| **Metrics summary** | Full JSON export of every issue found, for time-series tracking or alerting |
| **Logging** | Console + rotating file log of every validation run |
| **Config-driven rules** | All checks, types, and scoring weights live in `config/rules.yaml` |

---

## Project Structure

```
dq_framework/
├── src/                      # Source code
│   ├── issue.py              # Issue data model
│   ├── logger.py             # Centralized logging
│   ├── config_loader.py      # YAML config -> DQConfig
│   ├── engine.py              # ValidationEngine orchestrator
│   ├── scoring.py             # Quality scoring logic
│   ├── report_generator.py    # HTML / JSON report generation
│   ├── main.py                 # CLI entry point
│   └── validators/             # One module per check
│       ├── null_check.py
│       ├── duplicate_check.py
│       ├── date_check.py
│       ├── email_check.py
│       ├── dtype_check.py
│       └── outlier_check.py
├── tests/                     # Pytest unit + integration tests
├── config/
│   └── rules.yaml              # Sample validation rules
├── data/
│   ├── sample_clean.csv        # Sample dataset with no issues
│   └── sample_dirty.csv        # Sample dataset with every issue type injected
├── reports/                    # Generated reports land here (gitkeept)
├── docs/                       # Architecture & configuration reference
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Installation

```bash
cd dq_framework
pip install -r requirements.txt
```

Requires Python 3.9+.

---

## Quick Start

Run the framework against the bundled dirty sample dataset:

```bash
python -m src.main --data data/sample_dirty.csv --config config/rules.yaml --output-dir reports/
```

Expected output:

```
Validation complete for dataset: customers
  Overall score : 80.75/100
  Total issues  : 17
  HTML report   : reports/sample_dirty_report.html
  Dashboard data: reports/sample_dirty_dashboard.json
  Metrics JSON  : reports/sample_dirty_metrics.json
```

Open `reports/sample_dirty_report.html` in a browser to see the full report.

Try it against the clean sample too:

```bash
python -m src.main --data data/sample_clean.csv --config config/rules.yaml --output-dir reports/
```

---

## Using It On Your Own Dataset

1. Write a `config/your_rules.yaml` describing your dataset's columns
   (see `config/rules.yaml` for a full example, and
   `docs/CONFIGURATION.md` for the schema reference).
2. Run:

   ```bash
   python -m src.main --data path/to/your_data.csv --config config/your_rules.yaml --output-dir reports/
   ```

3. Check `reports/` for the HTML report, dashboard JSON, and metrics JSON.

---

## Using It Programmatically

```python
import pandas as pd
from src.config_loader import load_config
from src.engine import ValidationEngine
from src.report_generator import generate_html_report

config = load_config("config/rules.yaml")
df = pd.read_csv("data/sample_dirty.csv")

result = ValidationEngine(config).run(df)

print(f"Score: {result.score.overall_score:.2f}/100")
for issue in result.issues[:5]:
    print(issue.to_dict())

generate_html_report(result, "reports/my_report.html")
```

---

## The Six Checks

| Check | What it does | Config key |
|---|---|---|
| **Null values** | Flags NaN/None/blank strings in columns marked `nullable: false` | `nullable` |
| **Duplicate records** | Flags repeated rows based on a key subset (or the whole row) | `checks.duplicates` |
| **Invalid dates** | Flags values that don't parse as a valid date (optionally against a strict format) | `type: date`, `date_format` |
| **Invalid emails** | Flags syntactically malformed email addresses | `check_email: true` |
| **Data type validation** | Flags values that can't be cast to the declared type (`int`, `float`, `str`, `bool`, `date`) | `type` |
| **Outlier detection** | Flags statistical outliers via IQR or z-score | `outlier_check`, `outlier_method`, `outlier_threshold` |

---

## Quality Scoring

Each check type contributes a weighted score (0–100) to the overall
score. The error rate for a check = `issues found / opportunities`
(rows × columns the check actually ran against). Weights are defined
in `config/rules.yaml` under `scoring.weights` and are normalized to
sum to 1.0 automatically.

| Score | Grade |
|---|---|
| 90–100 | A |
| 80–89 | B |
| 70–79 | C |
| 60–69 | D |
| < 60 | F |

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

The suite includes unit tests for every validator, the config loader,
the scoring engine, the report generator, and end-to-end integration
tests against the bundled sample datasets.

---

## Outputs

Every run produces three files in the output directory:

1. **`<dataset>_report.html`** — human-readable report with summary
   cards, a score breakdown by check, a column-level summary, and a
   full issue log.
2. **`<dataset>_dashboard.json`** — compact aggregated payload
   (overall score, grade, per-check scores, severity counts, top
   problem columns) for feeding a dashboard widget or BI tool.
3. **`<dataset>_metrics.json`** — full machine-readable export
   including every single issue found, for alerting pipelines or
   historical tracking.

A log file is also written to `reports/dq_framework.log` for every run.

---

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — design overview and extension points
- [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) — full YAML config schema reference
- [`docs/USAGE.md`](docs/USAGE.md) — CLI and programmatic usage examples

---

## License

Provided as-is for internal use / demonstration purposes.
