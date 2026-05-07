#!/usr/bin/env python
"""Build NeurIPS 2026 paper assets from existing result files."""

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

    load_experiment_config(args.config)
    root = Path(__file__).resolve().parents[1]

    for script in ["08_generate_figures.py", "09_generate_tables.py"]:
        completed = subprocess.run(
            [sys.executable, str(root / "scripts" / script), "--config", args.config],
            check=False,
        )
        if completed.returncode != 0:
            raise SystemExit(f"{script} failed; paper assets were not fully built.")

    print("Paper assets built from existing result files.")


if __name__ == "__main__":
    main()
