#!/usr/bin/env python
"""Run configured occupancy and trajectory privacy filters."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from privatemap.filters import occupancy_filters, trajectory_filters
from privatemap.io.config import load_experiment_config, load_yaml, resolve_repo_path
from privatemap.io.map_io import OccupancyMap, load_occupancy_map, save_occupancy_map
from privatemap.io.trajectory_io import read_trajectory_csv, write_trajectory_csv


def _runs(config: dict) -> list[dict]:
    runs = config["experiment"].get("runs", [])
    if not isinstance(runs, list):
        raise ValueError("experiment.runs must be a list")
    normalized = []
    for item in runs:
        if isinstance(item, str):
            normalized.append({"run_id": item})
        elif isinstance(item, dict):
            normalized.append(item)
        else:
            raise ValueError("Each run must be a string run_id or mapping")
    return normalized


def _run_id(run: dict) -> str:
    run_id = str(run.get("run_id", ""))
    if not run_id:
        raise ValueError("Each run mapping must contain run_id")
    return run_id


def _input_path(run: dict, keys: tuple[str, ...], default: Path) -> Path:
    for key in keys:
        if key in run:
            return resolve_repo_path(run[key])
    return default


def _enabled_base_filters(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    enabled: dict[str, dict[str, Any]] = {}
    for name, params in config.items():
        if not isinstance(params, dict) or params.get("enabled", True):
            enabled[name] = dict(params or {})
    return enabled


def _occupancy_jobs(filter_config: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    jobs: list[tuple[str, str, dict[str, Any]]] = []

    for name, params in _enabled_base_filters(filter_config.get("occupancy_filters", {})).items():
        if name in {"downsample", "blur", "noise", "remove_small_components"}:
            jobs.append((name, name, params))

    for sweep in filter_config.get("sweeps", {}).get("occupancy", []):
        jobs.append((str(sweep["name"]), str(sweep["filter"]), dict(sweep)))

    return jobs


def _trajectory_jobs(filter_config: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    jobs: list[tuple[str, str, dict[str, Any]]] = []

    for name, params in _enabled_base_filters(filter_config.get("trajectory_filters", {})).items():
        if name in {"downsample", "spatial_quantize"}:
            jobs.append((name, name, params))

    for sweep in filter_config.get("sweeps", {}).get("trajectory", []):
        jobs.append((str(sweep["name"]), str(sweep["filter"]), dict(sweep)))

    return jobs


def _apply_occupancy_filter(source_map: OccupancyMap, filter_type: str, params: dict[str, Any], seed: int):
    if filter_type == "downsample":
        return occupancy_filters.downsample(source_map.data, int(params["factor"]))
    if filter_type == "blur":
        return occupancy_filters.blur(source_map.data, float(params["sigma"]))
    if filter_type == "noise":
        return occupancy_filters.add_noise(
            source_map.data,
            float(params["probability"]),
            seed=int(params.get("seed", seed)),
        )
    if filter_type == "remove_small_components":
        return occupancy_filters.remove_small_components(
            source_map.data,
            int(params["min_size"]),
        )
    raise ValueError(f"Unknown occupancy filter type: {filter_type}")


def _apply_trajectory_filter(source_trajectory, filter_type: str, params: dict[str, Any]):
    if filter_type == "downsample":
        return trajectory_filters.downsample(source_trajectory, int(params["step"]))
    if filter_type == "spatial_quantize":
        return trajectory_filters.spatial_quantize(
            source_trajectory,
            float(params["grid_size"]),
        )
    raise ValueError(f"Unknown trajectory filter type: {filter_type}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    args = parser.parse_args()

    config = load_experiment_config(args.config)
    paths = load_yaml(config["paths_config"])
    filter_config = load_yaml(config["filters_config"])

    processed_dir = resolve_repo_path(paths["processed_dir"])
    filtered_dir = resolve_repo_path(paths["filtered_dir"])
    seed = int(config["experiment"].get("random_seed", 0))
    output_count = 0

    occupancy_jobs = _occupancy_jobs(filter_config)
    trajectory_jobs = _trajectory_jobs(filter_config)

    for run in _runs(config):
        run_id = _run_id(run)
        map_path = _input_path(
            run,
            ("map_yaml", "occupancy_map", "map_path"),
            processed_dir / run_id / "map.yaml",
        )
        trajectory_path = _input_path(
            run,
            ("trajectory_csv", "trajectory_path"),
            processed_dir / run_id / "trajectory.csv",
        )

        if occupancy_jobs:
            if not map_path.exists():
                raise FileNotFoundError(f"Required occupancy map does not exist: {map_path}")
            source_map = load_occupancy_map(map_path)

            for output_name, filter_type, params in occupancy_jobs:
                data = _apply_occupancy_filter(source_map, filter_type, params, seed)
                save_occupancy_map(
                    OccupancyMap(
                        data=data,
                        resolution=source_map.resolution,
                        origin=source_map.origin,
                        negate=source_map.negate,
                        occupied_thresh=source_map.occupied_thresh,
                        free_thresh=source_map.free_thresh,
                    ),
                    filtered_dir / run_id / "occupancy" / f"{output_name}.yaml",
                )
                output_count += 1

        if trajectory_jobs:
            if not trajectory_path.exists():
                raise FileNotFoundError(f"Required trajectory CSV does not exist: {trajectory_path}")
            source_trajectory = read_trajectory_csv(trajectory_path)

            for output_name, filter_type, params in trajectory_jobs:
                trajectory = _apply_trajectory_filter(source_trajectory, filter_type, params)
                write_trajectory_csv(
                    trajectory,
                    filtered_dir / run_id / "trajectory" / f"{output_name}.csv",
                )
                output_count += 1

    print(f"Wrote {output_count} filtered artifact(s).")


if __name__ == "__main__":
    main()
