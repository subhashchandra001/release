#!/usr/bin/env python
"""Run configured utility evaluations on existing filtered artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from privatemap.io.config import load_experiment_config, load_yaml, resolve_repo_path
from privatemap.io.map_io import load_occupancy_map
from privatemap.io.results_io import UtilityResultRow, write_utility_results
from privatemap.utility.map_compactness import compactness_metrics
from privatemap.utility.navigation_utility import NavigationUtilityError, astar_plan, traversable_mask


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


def _environment_id(run: dict, run_id: str) -> str:
    return str(run.get("environment_id") or run_id.split("_", 1)[0])


def _input_path(run: dict, keys: tuple[str, ...], default: Path) -> Path:
    for key in keys:
        if key in run:
            return resolve_repo_path(run[key])
    return default


def _enabled_filters(filters: dict[str, Any]) -> dict[str, Any]:
    enabled = {
        name: params
        for name, params in filters.get("occupancy_filters", {}).items()
        if not isinstance(params, dict) or params.get("enabled", True)
    }
    for sweep in filters.get("sweeps", {}).get("occupancy", []):
        enabled[str(sweep["name"])] = sweep
    return enabled


def _load_routes(astar_cfg: dict[str, Any], env_id: str) -> list[dict[str, Any]]:
    inline_routes = astar_cfg.get("routes", [])
    if inline_routes:
        return list(inline_routes)

    routes_config = astar_cfg.get("routes_config")
    if not routes_config:
        raise ValueError(
            "utility.astar_navigation requires either inline routes or routes_config"
        )

    nav_data = load_yaml(routes_config)
    environments = nav_data.get("environments", {})
    if env_id not in environments:
        raise ValueError(f"No navigation routes found for environment {env_id!r}")
    routes = environments[env_id].get("routes", [])
    if not routes:
        raise ValueError(f"No navigation routes listed for environment {env_id!r}")
    return list(routes)


def _grid_xy_to_cell(point: list[int] | tuple[int, int]) -> tuple[int, int]:
    """Convert annotation grid [x, y] to A* cell (row, col)."""

    x, y = int(point[0]), int(point[1])
    return y, x


def _nearest_traversable_cell(
    map_data,
    cell: tuple[int, int],
    *,
    obstacle_threshold: int,
    allow_unknown: bool,
    max_radius: int = 25,
) -> tuple[int, int] | None:
    free = traversable_mask(
        map_data,
        obstacle_threshold=obstacle_threshold,
        allow_unknown=allow_unknown,
    )
    row, col = cell
    if 0 <= row < free.shape[0] and 0 <= col < free.shape[1] and free[row, col]:
        return row, col

    for radius in range(1, max_radius + 1):
        rmin = max(0, row - radius)
        rmax = min(free.shape[0] - 1, row + radius)
        cmin = max(0, col - radius)
        cmax = min(free.shape[1] - 1, col + radius)
        candidates: list[tuple[int, int, int]] = []
        for rr in range(rmin, rmax + 1):
            for cc in range(cmin, cmax + 1):
                if free[rr, cc]:
                    distance = abs(rr - row) + abs(cc - col)
                    candidates.append((distance, rr, cc))
        if candidates:
            _, rr, cc = min(candidates)
            return rr, cc
    return None


def _plan_or_failure(map_data, start_xy, goal_xy, *, obstacle_threshold: int, allow_unknown: bool, diagonal: bool):
    start_cell = _nearest_traversable_cell(
        map_data,
        _grid_xy_to_cell(start_xy),
        obstacle_threshold=obstacle_threshold,
        allow_unknown=allow_unknown,
    )
    goal_cell = _nearest_traversable_cell(
        map_data,
        _grid_xy_to_cell(goal_xy),
        obstacle_threshold=obstacle_threshold,
        allow_unknown=allow_unknown,
    )
    if start_cell is None or goal_cell is None:
        return None

    try:
        return astar_plan(
            map_data,
            start=start_cell,
            goal=goal_cell,
            obstacle_threshold=obstacle_threshold,
            allow_unknown=allow_unknown,
            diagonal=diagonal,
        )
    except NavigationUtilityError:
        return None


def _add_row(
    rows: list[UtilityResultRow],
    run_id: str,
    artifact_type: str,
    filter_name: str,
    utility_name: str,
    metric_name: str,
    value: float,
) -> None:
    rows.append(
        UtilityResultRow(
            run_id=run_id,
            artifact_type=artifact_type,
            filter_name=filter_name,
            utility_name=utility_name,
            metric_name=metric_name,
            value=value,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    args = parser.parse_args()

    config = load_experiment_config(args.config)
    paths = load_yaml(config["paths_config"])
    filters = load_yaml(config["filters_config"])
    utility = load_yaml(config["utility_config"]).get("utility", {})

    processed_dir = resolve_repo_path(paths["processed_dir"])
    filtered_dir = resolve_repo_path(paths["filtered_dir"])
    results_dir = resolve_repo_path(paths["results_dir"])

    rows: list[UtilityResultRow] = []
    occupancy_filters = _enabled_filters(filters)

    for run in _runs(config):
        run_id = _run_id(run)
        env_id = _environment_id(run, run_id)

        reference_map_path = _input_path(
            run,
            ("map_yaml", "occupancy_map", "map_path"),
            processed_dir / run_id / "map.yaml",
        )
        reference_map = load_occupancy_map(reference_map_path) if reference_map_path.exists() else None

        for filter_name in occupancy_filters:
            map_path = filtered_dir / run_id / "occupancy" / f"{filter_name}.yaml"
            if not map_path.exists():
                if any(value.get("enabled", False) for value in utility.values() if isinstance(value, dict)):
                    raise FileNotFoundError(
                        f"Required filtered occupancy map does not exist: {map_path}"
                    )
                continue

            occupancy_map = load_occupancy_map(map_path)

            compact_cfg = utility.get("map_compactness", {})
            if compact_cfg.get("enabled", False):
                metrics = compactness_metrics(occupancy_map)
                for metric, value in metrics.items():
                    _add_row(
                        rows,
                        run_id,
                        "occupancy_map",
                        filter_name,
                        "map_compactness",
                        metric,
                        value,
                    )

            astar_cfg = utility.get("astar_navigation", {})
            if astar_cfg.get("enabled", False):
                if reference_map is None:
                    raise FileNotFoundError(
                        f"Required reference map does not exist for A* utility: {reference_map_path}"
                    )

                routes = _load_routes(astar_cfg, env_id)
                obstacle_threshold = int(astar_cfg.get("obstacle_threshold", 50))
                allow_unknown = bool(astar_cfg.get("allow_unknown", False))
                diagonal = bool(astar_cfg.get("diagonal", False))

                for index, route in enumerate(routes):
                    start = route["start"]
                    goal = route["goal"]
                    route_name = str(route.get("name", f"route_{index}"))
                    metric_prefix = f"{route_name}"

                    reference_plan = _plan_or_failure(
                        reference_map,
                        start,
                        goal,
                        obstacle_threshold=obstacle_threshold,
                        allow_unknown=allow_unknown,
                        diagonal=diagonal,
                    )
                    released_plan = _plan_or_failure(
                        occupancy_map,
                        start,
                        goal,
                        obstacle_threshold=obstacle_threshold,
                        allow_unknown=allow_unknown,
                        diagonal=diagonal,
                    )

                    reference_success = reference_plan is not None and reference_plan.success
                    released_success = released_plan is not None and released_plan.success

                    reference_cost = (
                        reference_plan.cost if reference_success else float("inf")
                    )
                    released_cost = released_plan.cost if released_success else float("inf")
                    path_overhead = (
                        released_cost / reference_cost
                        if reference_success and released_success and reference_cost > 0
                        else float("inf")
                    )

                    _add_row(
                        rows,
                        run_id,
                        "occupancy_map",
                        filter_name,
                        "astar_navigation",
                        f"{metric_prefix}_route_success",
                        1.0 if released_success else 0.0,
                    )
                    _add_row(
                        rows,
                        run_id,
                        "occupancy_map",
                        filter_name,
                        "astar_navigation",
                        f"{metric_prefix}_path_cost",
                        float(released_cost),
                    )
                    _add_row(
                        rows,
                        run_id,
                        "occupancy_map",
                        filter_name,
                        "astar_navigation",
                        f"{metric_prefix}_path_overhead_vs_reference",
                        float(path_overhead),
                    )
                    _add_row(
                        rows,
                        run_id,
                        "occupancy_map",
                        filter_name,
                        "astar_navigation",
                        f"{metric_prefix}_expanded_nodes",
                        float(released_plan.expanded_nodes if released_plan else 0),
                    )
                    _add_row(
                        rows,
                        run_id,
                        "occupancy_map",
                        filter_name,
                        "astar_navigation",
                        f"{metric_prefix}_connectivity_preserved",
                        1.0 if reference_success and released_success else 0.0,
                    )

    if rows:
        write_utility_results(rows, results_dir / "utility_results.csv")
        print(f"Wrote {len(rows)} utility result row(s).")
    else:
        print("No utility evaluations were enabled; no result files were written.")


if __name__ == "__main__":
    main()
