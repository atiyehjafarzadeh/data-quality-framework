# Configuration Reference

All validation behavior is driven by a single YAML file. This document
describes every available key.

## Top-Level Structure

```yaml
dataset:
  name: <string>            # Used in reports/logs; informational only

columns:
  <column_name>:
    type: <int|float|str|bool|date>
    nullable: <true|false>             # default: true
    check_email: <true|false>          # default: false
    date_format: <strftime string>     # only used when type: date
    outlier_check: <true|false>        # default: false
    outlier_method: <iqr|zscore>       # default: iqr
    outlier_threshold: <number>        # default: 1.5 (iqr) / 3.0 (zscore)

checks:
  duplicates:
    enabled: <true|false>     # default: true
    subset: [<column_name>, ...]   # default: null (whole row)

scoring:
  weights:
    null: <number>
    duplicate: <number>
    invalid_date: <number>
    invalid_email: <number>
    dtype: <number>
    outlier: <number>
```

## `dataset.name`

A human-readable label used in the HTML report header, dashboard JSON,
and log lines. Defaults to `unnamed_dataset` if omitted.

## `columns.<name>`

Each key under `columns` must match a column name in the dataset
being validated.

| Field | Type | Default | Effect |
|---|---|---|---|
| `type` | `int`, `float`, `str`, `bool`, `date` | `null` | Enables the **data type validation** check for this column. If `date`, also enables the **invalid date** check. |
| `nullable` | bool | `true` | If `false`, enables the **null check** for this column. |
| `check_email` | bool | `false` | If `true`, enables the **invalid email** check for this column. |
| `date_format` | string (strftime) | `null` | Used by the date check when `type: date`. If omitted, pandas' generic date parser is used (more permissive, less strict). |
| `outlier_check` | bool | `false` | If `true`, enables **outlier detection** for this column (numeric columns only). |
| `outlier_method` | `iqr`, `zscore` | `iqr` | Statistical method used for outlier detection. |
| `outlier_threshold` | number | `1.5` for `iqr`, `3.0` for `zscore` | IQR multiplier (Tukey fence) or z-score cutoff. |

### Notes on Type Validation

Type checks are **value-level**, not pandas-dtype-level. A column
loaded by pandas as `object` dtype (which happens whenever even one
row doesn't fit a numeric type) is still checked value-by-value against
the declared `type`. This is what lets the framework catch the exact
rows that broke the column's intended type, rather than only detecting
"this whole column isn't numeric."

## `checks.duplicates`

| Field | Type | Default | Effect |
|---|---|---|---|
| `enabled` | bool | `true` | Whether to run duplicate detection at all. |
| `subset` | list of column names | `null` | Columns that define uniqueness (e.g. a primary key). If omitted, the entire row must match for a record to be considered a duplicate. |

## `scoring.weights`

Six keys, one per check type: `null`, `duplicate`, `invalid_date`,
`invalid_email`, `dtype`, `outlier`. Any keys you omit fall back to
the framework defaults (all weights equal, summing to 1.0). Whatever
values you provide are **automatically normalized** to sum to 1.0, so
you can express them as relative importance (e.g. `2`, `2`, `1`, `1`,
`1`, `1`) rather than worrying about getting fractions exactly right.

A check type that isn't configured for any column (e.g. you set
`outlier_check: true` nowhere) automatically scores a perfect 100 for
that category, rather than being treated as 0/0 and zeroing out the
overall score.

## Full Example

See [`config/rules.yaml`](../config/rules.yaml) for a complete,
annotated example covering every feature above.
