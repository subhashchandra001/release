#!/usr/bin/env python
"""Check that Stage 2 configuration and Python dependencies are available."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from privatemap.io.config import ConfigError, load_experiment_config, load_yaml


REQUIRED_MODULES = ["numpy", "scipy", "pandas", "yaml", "PIL"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    args = parser.parse_args()

    config = load_experiment_config(args.config)
    repo_root = Path(__file__).resolve().parents[1]
    for key in [
        "paths_config",
        "topics_config",
        "filters_config",
        "attacks_config",
        "utility_config",
        "paper_config",
    ]:
        path = Path(config[key])
        if not path.is_absolute():
            path = repo_root / path
        load_yaml(path)

    missing = []
    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(module)
    if missing:
        raise ConfigError(f"Missing required Python module(s): {', '.join(missing)}")
    print("Environment check passed.")


if __name__ == "__main__":
    main()
