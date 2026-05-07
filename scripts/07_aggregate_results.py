#!/usr/bin/env python
"""Aggregate existing privacy and utility result CSV files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from privatemap.io.config import load_experiment_config, load_yaml, resolve_repo_path
from privatemap.io.results_io import (
    ResultsIOError,
    aggregate_results,
    read_privacy_results,
    read_utility_results,
    write_json_records,
    write_result_records_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    args = parser.parse_args()

    config = load_experiment_config(args.config)
    paths = load_yaml(config["paths_config"])
    results_dir = resolve_repo_path(paths["results_dir"])
    frames = []
    privacy_path = results_dir / "privacy_results.csv"
    utility_path = results_dir / "utility_results.csv"
    if privacy_path.exists():
        frames.append(read_privacy_results(privacy_path))
    if utility_path.exists():
        frames.append(read_utility_results(utility_path))
    if not frames:
        raise ResultsIOError(
            f"No result CSV files found in {results_dir}; run attacks or utility eval first"
        )

    aggregated = aggregate_results(frames)
    csv_path = results_dir / "aggregated_results.csv"
    json_path = results_dir / "aggregated_results.json"
    write_result_records_csv(aggregated, csv_path)
    write_json_records(aggregated, json_path)
    print(f"Wrote {csv_path} and {json_path}.")


if __name__ == "__main__":
    main()
