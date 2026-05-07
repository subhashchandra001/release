#!/usr/bin/env python
"""Run configured privacy attacks on existing filtered artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from privatemap.attacks.floorplan_attack import floor_plan_leakage
from privatemap.attacks.room_graph_attack import load_room_boxes, room_graph_leakage
from privatemap.attacks.routine_attack import routine_leakage
from privatemap.attacks.trajectory_attack import trajectory_leakage
from privatemap.io.config import load_experiment_config, load_yaml, resolve_repo_path
from privatemap.io.map_io import load_occupancy_map
from privatemap.io.results_io import PrivacyResultRow, write_privacy_results
from privatemap.io.trajectory_io import read_trajectory_csv


def _runs(config: dict) -> list[dict]:
    runs = config["experiment"].get("runs", [])
    if not isinstance(runs, list):
        raise ValueError("experiment.runs must be a list")
    return [{"run_id": item} if isinstance(item, str) else item for item in runs]


def _run_id(run: dict) -> str:
    run_id = str(run.get("run_id", ""))
    if not run_id:
        raise ValueError("Each run mapping must contain run_id")
    return run_id


def _environment_id(run_id: str) -> str:
    return run_id.split("_", 1)[0]


def _input_path(run: dict, keys: tuple[str, ...], default: Path) -> Path:
    for key in keys:
        if key in run:
            return resolve_repo_path(run[key])
    return default


def _occupancy_filter_names(filters: dict) -> list[str]:
    names = [
        name
        for name, params in filters.get("occupancy_filters", {}).items()
        if name in {"downsample", "blur", "noise", "remove_small_components"}
        and (not isinstance(params, dict) or params.get("enabled", True))
    ]
    names.extend(str(item["name"]) for item in filters.get("sweeps", {}).get("occupancy", []))
    return names


def _add_result_rows(
    rows: list[PrivacyResultRow],
    *,
    run_id: str,
    artifact_type: str,
    filter_name: str,
    attack_name: str,
    metrics: dict[str, float],
) -> None:
    rows.extend(
        PrivacyResultRow(
            run_id=run_id,
            artifact_type=artifact_type,
            filter_name=filter_name,
            attack_name=attack_name,
            metric_name=metric,
            value=value,
        )
        for metric, value in metrics.items()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    args = parser.parse_args()

    config = load_experiment_config(args.config)
    paths = load_yaml(config["paths_config"])
    attacks = load_yaml(config["attacks_config"]).get("attacks", {})
    filters = load_yaml(config["filters_config"])

    processed_dir = resolve_repo_path(paths["processed_dir"])
    filtered_dir = resolve_repo_path(paths["filtered_dir"])
    results_dir = resolve_repo_path(paths["results_dir"])
    annotations_dir = resolve_repo_path(paths.get("annotations_dir", "data/annotations"))
    rooms_geojson = annotations_dir / "rooms.geojson"

    rows: list[PrivacyResultRow] = []

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

        if attacks.get("floor_plan_leakage", {}).get("enabled", False) or attacks.get(
            "room_graph_leakage", {}
        ).get("enabled", False):
            if not map_path.exists():
                raise FileNotFoundError(f"Required reference map does not exist: {map_path}")

            reference_map = load_occupancy_map(map_path)

            for filter_name in _occupancy_filter_names(filters):
                released_path = filtered_dir / run_id / "occupancy" / f"{filter_name}.yaml"
                if not released_path.exists():
                    raise FileNotFoundError(
                        f"Required filtered occupancy map does not exist: {released_path}"
                    )

                released_map = load_occupancy_map(released_path)
                if released_map.shape != reference_map.shape:
                    print(
                        f"Skipping occupancy filter {filter_name!r} for run {run_id!r}: "
                        f"shape mismatch {reference_map.shape} != {released_map.shape}"
                    )
                    continue

                if attacks.get("floor_plan_leakage", {}).get("enabled", False):
                    result = floor_plan_leakage(reference_map, released_map)
                    _add_result_rows(
                        rows,
                        run_id=run_id,
                        artifact_type="occupancy_map",
                        filter_name=filter_name,
                        attack_name=result.attack_name,
                        metrics=result.metrics,
                    )

                if attacks.get("room_graph_leakage", {}).get("enabled", False):
                    room_boxes = load_room_boxes(rooms_geojson, _environment_id(run_id))
                    result = room_graph_leakage(
                        reference_map,
                        released_map,
                        room_boxes=room_boxes,
                    )
                    _add_result_rows(
                        rows,
                        run_id=run_id,
                        artifact_type="occupancy_map",
                        filter_name=filter_name,
                        attack_name=result.attack_name,
                        metrics=result.metrics,
                    )

        if attacks.get("trajectory_leakage", {}).get("enabled", False) or attacks.get(
            "routine_leakage", {}
        ).get("enabled", False):
            if not trajectory_path.exists():
                raise FileNotFoundError(
                    f"Required reference trajectory does not exist: {trajectory_path}"
                )

            reference_trajectory = read_trajectory_csv(trajectory_path)
            room_cfg = filters.get("trajectory_filters", {}).get("room_sequence", {})
            rooms = room_cfg.get("rooms") if isinstance(room_cfg, dict) else None

            trajectory_filter_names = [
                name
                for name, params in filters.get("trajectory_filters", {}).items()
                if name in {"downsample", "spatial_quantize"}
                and (not isinstance(params, dict) or params.get("enabled", True))
            ]
            trajectory_filter_names.extend(
                str(item["name"]) for item in filters.get("sweeps", {}).get("trajectory", [])
            )

            for filter_name in trajectory_filter_names:
                released_path = filtered_dir / run_id / "trajectory" / f"{filter_name}.csv"
                if not released_path.exists():
                    raise FileNotFoundError(
                        f"Required filtered trajectory CSV does not exist: {released_path}"
                    )

                released_trajectory = read_trajectory_csv(released_path)

                if attacks.get("trajectory_leakage", {}).get("enabled", False):
                    result = trajectory_leakage(
                        reference_trajectory,
                        released_trajectory,
                        rooms=rooms,
                    )
                    _add_result_rows(
                        rows,
                        run_id=run_id,
                        artifact_type="trajectory",
                        filter_name=filter_name,
                        attack_name=result.attack_name,
                        metrics=result.metrics,
                    )

                if attacks.get("routine_leakage", {}).get("enabled", False):
                    result = routine_leakage(reference_trajectory, released_trajectory)
                    _add_result_rows(
                        rows,
                        run_id=run_id,
                        artifact_type="trajectory",
                        filter_name=filter_name,
                        attack_name=result.attack_name,
                        metrics=result.metrics,
                    )

    if rows:
        write_privacy_results(rows, results_dir / "privacy_results.csv")
        print(f"Wrote {len(rows)} privacy result row(s).")
    else:
        print("No privacy attacks were enabled; no result files were written.")


if __name__ == "__main__":
    main()
