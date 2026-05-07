#!/usr/bin/env python
"""Validate configured offline artifact exports.

This script intentionally avoids live ROS bag parsing. Stage 3 expects
pre-exported artifacts and reports missing setup clearly.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from privatemap.io.config import load_experiment_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    args = parser.parse_args()
    config = load_experiment_config(args.config)
    runs = config["experiment"].get("runs", [])
    if not runs:
        raise SystemExit(
            "No runs configured. Add runs to configs/experiment.yaml before "
            "exporting artifacts."
        )
    print(
        "Live ROS bag parsing is not implemented. Use pre-exported processed "
        "artifacts for configured runs."
    )


if __name__ == "__main__":
    main()
