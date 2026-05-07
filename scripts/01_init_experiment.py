#!/usr/bin/env python
"""Initialize configured experiment output directories."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from privatemap.io.config import load_experiment_config, load_yaml, resolve_repo_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    args = parser.parse_args()

    config = load_experiment_config(args.config)
    paths = load_yaml(config["paths_config"])
    for key in [
        "processed_dir",
        "filtered_dir",
        "results_dir",
        "figures_dir",
        "tables_dir",
    ]:
        if key not in paths:
            raise KeyError(f"paths config is missing required key: {key}")
        resolve_repo_path(paths[key]).mkdir(parents=True, exist_ok=True)
    print("Experiment directories are initialized.")


if __name__ == "__main__":
    main()
