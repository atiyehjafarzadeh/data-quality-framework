# Architecture

## Design Goals

1. **Config-driven, not code-driven.** Validating a new dataset should
   require writing a YAML file, not Python code.
2. **Checks are pure functions.** Each check takes a DataFrame (and a
   few parameters) and returns a list of `Issue` objects. No check
   mutates the DataFrame or has side effects, which makes them trivial
   to unit test in isolation.
3. **One uniform finding type.** Every check, regardless of what it's
   checking, emits the same `Issue` shape. This lets scoring, logging,
   and reporting be written once against `Issue` rather than once per
   check type.
4. **Minimal dependencies.** Only pandas, NumPy, PyYAML, and pytest are
   required — no Jinja2, no web framework, no database. HTML reports
   are generated with plain string templating.

## Data Flow

```
                 ┌───────────────┐
   rules.yaml ─► │ config_loader │ ─► DQConfig
                 └───────────────┘
                                            │
   dataset.csv ─► pandas.read_csv ─► DataFrame
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │ ValidationEngine │
                                   │   (engine.py)    │
                                   └────────┬─────────┘
                                            │ runs each
                                            │ configured check
                              ┌─────────────┼──────────────────┐
                              ▼             ▼                  ▼
                     null_check.py   duplicate_check.py  ... outlier_check.py
                              │             │                  │
                              └─────────────┴──────────────────┘
                                            │ List[Issue]
                                            ▼
                                   ┌─────────────────┐
                                   │  scoring.py      │ ─► ScoreBreakdown
                                   └─────────────────┘
                                            │
                                            ▼
                                   ValidationResult
                                            │
                              ┌─────────────┼──────────────────┐
                              ▼             ▼                  ▼
                     HTML report     dashboard.json      metrics.json
                  (report_generator.py)
```

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `issue.py` | Defines the `Issue` dataclass — the single finding type used everywhere |
| `config_loader.py` | Parses & validates `rules.yaml` into a `DQConfig` object; normalizes scoring weights |
| `validators/*.py` | One pure-function check per file; no dependencies on each other |
| `engine.py` | Iterates over configured columns, calls the right checks, aggregates `Issue`s into a `ValidationResult` |
| `scoring.py` | Converts issues + opportunity counts into a weighted 0–100 score |
| `report_generator.py` | Renders a `ValidationResult` into HTML / dashboard JSON / metrics JSON |
| `logger.py` | Centralized logging configuration (console + file handler) |
| `main.py` | CLI glue: argument parsing, wiring the above together |

## Adding a New Check

1. Create `src/validators/my_check.py` with a function:

   ```python
   def check_my_thing(df: pd.DataFrame, column: str, **kwargs) -> List[Issue]:
       ...
   ```

2. Export it from `src/validators/__init__.py`.
3. Add a new check_type constant to `CHECK_TYPES` in `scoring.py`.
4. Wire it into `ValidationEngine.run()` in `engine.py`, gated on
   whatever new `ColumnRule` field you add in `config_loader.py`.
5. Add unit tests in `tests/test_my_check.py`.

Because checks are pure functions returning `Issue` lists, this is the
only place new logic needs to be threaded through — scoring and
reporting work automatically once `CHECK_TYPES` includes the new type.

## Extension Points

- **New report formats** (e.g. PDF, Slack message): add a new function
  to `report_generator.py` consuming `ValidationResult`; no changes
  needed elsewhere.
- **New data sources** (e.g. database tables instead of CSV): swap out
  `pd.read_csv(...)` in `main.py` for any call that returns a
  DataFrame — the engine doesn't care where the DataFrame came from.
- **Custom scoring strategy**: `scoring.compute_score` is a standalone
  function; replace it with an alternative implementation that
  produces a `ScoreBreakdown` with the same shape.
