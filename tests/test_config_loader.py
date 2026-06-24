"""Unit tests for src.config_loader"""

import pytest

from src.config_loader import DQConfig


def test_loads_basic_config(base_config_dict):
    config = DQConfig.from_dict(base_config_dict)
    assert config.dataset_name == "test_dataset"
    assert "customer_id" in config.columns
    assert config.columns["customer_id"].nullable is False


def test_default_dataset_name_when_missing():
    raw = {"columns": {"a": {"type": "int"}}}
    config = DQConfig.from_dict(raw)
    assert config.dataset_name == "unnamed_dataset"


def test_missing_columns_raises():
    with pytest.raises(ValueError):
        DQConfig.from_dict({"dataset": {"name": "x"}})


def test_unsupported_type_raises():
    raw = {"columns": {"a": {"type": "weird_type"}}}
    with pytest.raises(ValueError):
        DQConfig.from_dict(raw)


def test_unsupported_outlier_method_raises():
    raw = {"columns": {"a": {"type": "int", "outlier_method": "bogus"}}}
    with pytest.raises(ValueError):
        DQConfig.from_dict(raw)


def test_weights_are_normalized_to_sum_one(base_config_dict):
    config = DQConfig.from_dict(base_config_dict)
    assert abs(sum(config.weights.values()) - 1.0) < 1e-9


def test_duplicate_rule_defaults_to_enabled():
    raw = {"columns": {"a": {"type": "int"}}}
    config = DQConfig.from_dict(raw)
    assert config.duplicate_rule.enabled is True
    assert config.duplicate_rule.subset is None


def test_duplicate_rule_respects_config():
    raw = {
        "columns": {"a": {"type": "int"}},
        "checks": {"duplicates": {"enabled": False, "subset": ["a"]}},
    }
    config = DQConfig.from_dict(raw)
    assert config.duplicate_rule.enabled is False
    assert config.duplicate_rule.subset == ["a"]
