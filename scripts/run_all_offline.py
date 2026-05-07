#!/usr/bin/env python
"""Run the offline pipeline on pre-exported artifacts."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from privatemap.io.config import load_experiment_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    args = parser.parse_args()
    config = load_experiment_config(args.config)
    if not config["experiment"].get("runs"):
        raise SystemExit(
            "No runs configured. Add processed artifacts and runs before "
            "running offline pipeline."
        )
    root = Path(__file__).resolve().parents[1]
    for script in [
        "04_run_filters.py",
        "05_run_attacks.py",
        "06_run_utility_eval.py",
        "07_aggregate_results.py",
        "08_generate_figures.py",
        "09_generate_tables.py",
    ]:
        completed = subprocess.run(
            [sys.executable, str(root / "scripts" / script), "--config", args.config],
            check=False,
        )
        if completed.returncode != 0:
            raise SystemExit(f"Offline pipeline stopped because {script} failed.")


if __name__ == "__main__":
    main()
