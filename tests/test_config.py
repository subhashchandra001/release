from __future__ import annotations

import pytest

from privatemap.io.config import ConfigError, load_experiment_config, load_yaml


def test_load_experiment_config() -> None:
    config = load_experiment_config("configs/experiment_neurips2026.yaml")
    assert config["experiment"]["anonymous"] is True
    assert config["paths_config"] == "configs/paths.yaml"
    assert len(config["experiment"]["runs"]) == 15


def test_load_yaml_rejects_missing_file() -> None:
    with pytest.raises(ConfigError, match="does not exist"):
        load_yaml("tests/fixtures/missing.yaml")
