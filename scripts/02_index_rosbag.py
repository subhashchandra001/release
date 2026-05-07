#!/usr/bin/env python
"""ROS bag indexing is intentionally not implemented in Stage 1."""

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
    load_experiment_config(args.config)
    raise NotImplementedError(
        "ROS bag parsing is not implemented. Export reviewed artifacts into "
        "data/processed/<run_id>/ before running offline stages."
    )


if __name__ == "__main__":
    main()
