"""
Config-driven rules loader.

The framework is entirely driven by a YAML file (see config/rules.yaml
for a full example) with this shape:

    dataset:
      name: customers

    columns:
      customer_id:
        type: int
        nullable: false
      email:
        type: str
        nullable: false
        check_email: true
      signup_date:
        type: date
        nullable: false
        date_format: "%Y-%m-%d"
      age:
        type: int
        nullable: true
        outlier_check: true
        outlier_method: iqr

    checks:
      duplicates:
        enabled: true
        subset: [customer_id]

    scoring:
      weights:
        null: 0.2
        duplicate: 0.2
        invalid_date: 0.2
        invalid_email: 0.2
        dtype: 0.1
        outlier: 0.1

This module loads that file into a `DQConfig` object and performs basic
sanity checks so misconfiguration fails fast with a clear error instead
of silently skipping checks at validation time.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

SUPPORTED_TYPES = {"int", "float", "str", "bool", "date"}
SUPPORTED_OUTLIER_METHODS = {"iqr", "zscore"}

DEFAULT_WEIGHTS = {
    "null": 0.2,
    "duplicate": 0.2,
    "invalid_date": 0.2,
    "invalid_email": 0.2,
    "dtype": 0.1,
    "outlier": 0.1,
}


@dataclass
class ColumnRule:
    name: str
    type: Optional[str] = None
    nullable: bool = True
    check_email: bool = False
    date_format: Optional[str] = None
    outlier_check: bool = False
    outlier_method: str = "iqr"
    outlier_threshold: float = 1.5  # IQR multiplier or z-score threshold


@dataclass
class DuplicateRule:
    enabled: bool = True
    subset: Optional[List[str]] = None  # None == whole row


@dataclass
class DQConfig:
    dataset_name: str
    columns: Dict[str, ColumnRule] = field(default_factory=dict)
    duplicate_rule: DuplicateRule = field(default_factory=DuplicateRule)
    weights: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "DQConfig":
        if "columns" not in raw or not raw["columns"]:
            raise ValueError("Config must define at least one column under 'columns'.")

        dataset_name = raw.get("dataset", {}).get("name", "unnamed_dataset")

        columns: Dict[str, ColumnRule] = {}
        for col_name, col_cfg in raw["columns"].items():
            col_cfg = col_cfg or {}
            col_type = col_cfg.get("type")
            if col_type is not None and col_type not in SUPPORTED_TYPES:
                raise ValueError(
                    f"Column '{col_name}': unsupported type '{col_type}'. "
                    f"Supported types: {sorted(SUPPORTED_TYPES)}"
                )
            method = col_cfg.get("outlier_method", "iqr")
            if method not in SUPPORTED_OUTLIER_METHODS:
                raise ValueError(
                    f"Column '{col_name}': unsupported outlier_method '{method}'. "
                    f"Supported: {sorted(SUPPORTED_OUTLIER_METHODS)}"
                )
            columns[col_name] = ColumnRule(
                name=col_name,
                type=col_type,
                nullable=col_cfg.get("nullable", True),
                check_email=col_cfg.get("check_email", False),
                date_format=col_cfg.get("date_format"),
                outlier_check=col_cfg.get("outlier_check", False),
                outlier_method=method,
                outlier_threshold=col_cfg.get(
                    "outlier_threshold", 1.5 if method == "iqr" else 3.0
                ),
            )

        dup_cfg = raw.get("checks", {}).get("duplicates", {})
        duplicate_rule = DuplicateRule(
            enabled=dup_cfg.get("enabled", True),
            subset=dup_cfg.get("subset"),
        )

        weights = dict(DEFAULT_WEIGHTS)
        weights.update(raw.get("scoring", {}).get("weights", {}))
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("Sum of scoring weights must be greater than 0.")
        # Normalize so weights always sum to 1.0, regardless of user input.
        weights = {k: v / total for k, v in weights.items()}

        return cls(
            dataset_name=dataset_name,
            columns=columns,
            duplicate_rule=duplicate_rule,
            weights=weights,
        )


def load_config(path: Union[str, Path]) -> DQConfig:
    """Load and validate a YAML rules file into a DQConfig."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return DQConfig.from_dict(raw)
