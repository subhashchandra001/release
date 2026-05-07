"""Configuration loading helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when a YAML configuration file is missing or malformed."""


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping from ``path``.

    Empty files are treated as empty mappings. Non-mapping YAML documents are
    rejected because repository configs are expected to be keyed objects.
    """

    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config file does not exist: {config_path}")
    if not config_path.is_file():
        raise ConfigError(f"Config path is not a file: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse YAML config {config_path}: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config {config_path} must contain a YAML mapping")
    return data


def require_keys(config: Mapping[str, Any], keys: Iterable[str], *, source: str) -> None:
    """Validate that ``config`` contains every key in ``keys``."""

    missing = [key for key in keys if key not in config]
    if missing:
        joined = ", ".join(missing)
        raise ConfigError(f"{source} is missing required key(s): {joined}")


def load_experiment_config(path: str | Path = "configs/experiment.yaml") -> dict[str, Any]:
    """Load and minimally validate the experiment config."""

    config = load_yaml(path)
    require_keys(
        config,
        [
            "experiment",
            "paths_config",
            "topics_config",
            "filters_config",
            "attacks_config",
            "utility_config",
            "paper_config",
        ],
        source=str(path),
    )
    if not isinstance(config["experiment"], dict):
        raise ConfigError(f"{path}: 'experiment' must be a mapping")
    require_keys(config["experiment"], ["name", "anonymous", "random_seed", "runs"], source=f"{path}: experiment")
    return config


def resolve_repo_path(path: str | Path, *, repo_root: str | Path = ".") -> Path:
    """Resolve a repository-relative path without requiring it to exist."""

    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return (Path(repo_root) / candidate).resolve()
