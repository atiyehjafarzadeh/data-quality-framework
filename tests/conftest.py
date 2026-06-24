"""
Shared pytest fixtures for the Data Quality Framework test suite.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Make `src` importable as a top-level package when running tests
# directly (e.g. `pytest tests/`) without installing the project.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config_loader import DQConfig  # noqa: E402


@pytest.fixture
def clean_df() -> pd.DataFrame:
    """A small, fully valid DataFrame with no quality issues."""
    return pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4, 5, 6, 7, 8],
            "full_name": [
                "Alice Smith",
                "Bob Jones",
                "Carla Diaz",
                "David Lee",
                "Eve Adams",
                "Frank Moore",
                "Grace Kim",
                "Hank Cole",
            ],
            "email": [
                "alice@example.com",
                "bob@example.com",
                "carla@example.com",
                "david@example.com",
                "eve@example.com",
                "frank@example.com",
                "grace@example.com",
                "hank@example.com",
            ],
            "signup_date": [
                "2023-01-01",
                "2023-01-05",
                "2023-01-09",
                "2023-01-13",
                "2023-01-17",
                "2023-01-21",
                "2023-01-25",
                "2023-01-29",
            ],
            "age": [25, 30, 35, 28, 42, 31, 27, 39],
            "annual_spend": [500.0, 520.0, 480.0, 510.0, 495.0, 505.0, 515.0, 490.0],
        }
    )


@pytest.fixture
def dirty_df() -> pd.DataFrame:
    """A DataFrame deliberately containing one of every issue type."""
    return pd.DataFrame(
        {
            "customer_id": [1, 2, 2, 4, 5, "abc", 7, 8],
            "full_name": ["Alice", None, "Carla", "David", "Eve", "Frank", "Grace", "Hank"],
            "email": [
                "alice@example.com",
                "bob@example.com",
                "not-an-email",
                "missing@domain",
                None,
                "spaced out@example.com",
                "grace@example.com",
                "hank@example.com",
            ],
            "signup_date": [
                "2023-01-01",
                "not-a-date",
                "2023-01-09",
                "2023-13-45",
                "2023-01-17",
                "2023-01-21",
                None,
                "2023-01-29",
            ],
            "age": [25, 30, 35, 28, 42, 31, 27, 9999],
            "annual_spend": [500.0, 520.0, 480.0, 510.0, 495.0, 505.0, 515.0, "N/A"],
        }
    )


@pytest.fixture
def base_config_dict() -> dict:
    """A minimal valid raw config dict, used to build DQConfig instances."""
    return {
        "dataset": {"name": "test_dataset"},
        "columns": {
            "customer_id": {"type": "int", "nullable": False},
            "full_name": {"type": "str", "nullable": False},
            "email": {"type": "str", "nullable": False, "check_email": True},
            "signup_date": {
                "type": "date",
                "nullable": False,
                "date_format": "%Y-%m-%d",
            },
            "age": {
                "type": "int",
                "nullable": True,
                "outlier_check": True,
                "outlier_method": "iqr",
            },
            "annual_spend": {
                "type": "float",
                "nullable": True,
                "outlier_check": True,
                "outlier_method": "zscore",
            },
        },
        "checks": {"duplicates": {"enabled": True, "subset": ["customer_id"]}},
        "scoring": {
            "weights": {
                "null": 0.2,
                "duplicate": 0.2,
                "invalid_date": 0.15,
                "invalid_email": 0.15,
                "dtype": 0.15,
                "outlier": 0.15,
            }
        },
    }


@pytest.fixture
def base_config(base_config_dict) -> DQConfig:
    return DQConfig.from_dict(base_config_dict)
