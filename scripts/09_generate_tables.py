#!/usr/bin/env python
"""Generate NeurIPS 2026 paper tables from real configs and result CSVs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from privatemap.io.config import load_experiment_config, load_yaml, resolve_repo_path


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Required CSV does not exist: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_markdown(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote table: {path}")


def _latex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _write_latex(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    align = "l" * len(headers)
    lines = [
        rf"\begin{{tabular}}{{{align}}}",
        r"\toprule",
        " & ".join(_latex_escape(h) for h in headers) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(_latex_escape(item) for item in row) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote table: {path}")


def _write_both(tables_dir: Path, name: str, headers: list[str], rows: list[list[object]]) -> None:
    _write_markdown(tables_dir / f"{name}.md", headers, rows)
    _write_latex(tables_dir / f"{name}.tex", headers, rows)


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def _mean(values: Iterable[float]) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else 0.0


def _safe_float(value: str) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out or out in {float("inf"), float("-inf")}:
        return None
    return out


def _run_metadata(config: dict, tables_dir: Path) -> None:
    rows = []
    for run in config["experiment"]["runs"]:
        run_id = run["run_id"]
        rows.append(
            [
                run_id,
                run.get("environment_id", run_id.split("_", 1)[0]),
                run.get("purpose", ""),
                run.get("map_yaml", ""),
                run.get("trajectory_csv", ""),
            ]
        )
    _write_both(
        tables_dir,
        "run_metadata",
        ["run_id", "environment", "purpose", "map", "trajectory"],
        rows,
    )


def _artifact_modality(config: dict, tables_dir: Path) -> None:
    runs = config["experiment"]["runs"]
    envs = sorted({run.get("environment_id", run["run_id"].split("_", 1)[0]) for run in runs})
    rows = [
        ["TurtleBot4 raw ROS bags", len(runs), "private, not committed"],
        ["Moving-SLAM maps", len(envs), "processed, review required"],
        ["Trajectories", len(runs), "processed CSV"],
        ["RGB keyframe sets", len(runs), "300 frames per run, review required"],
        ["Detections", len(runs), "header-only until manual review"],
        ["Contact sheets", len(runs), "manual safety review only"],
    ]
    _write_both(tables_dir, "artifact_modality_table", ["artifact", "count", "release_status"], rows)


def _filter_table(filters: dict, tables_dir: Path) -> None:
    rows = []
    for family, key in [("occupancy", "occupancy_filters"), ("trajectory", "trajectory_filters")]:
        for name, params in filters.get(key, {}).items():
            if isinstance(params, dict):
                rows.append([family, name, params.get("enabled", True), json.dumps(params, sort_keys=True)])
    for family in ["occupancy", "trajectory"]:
        for sweep in filters.get("sweeps", {}).get(family, []):
            rows.append([family, sweep["name"], True, json.dumps(sweep, sort_keys=True)])
    _write_both(tables_dir, "filter_parameter_table", ["family", "filter", "enabled", "parameters"], rows)


def _attack_metric_table(privacy_rows: list[dict[str, str]], tables_dir: Path) -> None:
    metrics = defaultdict(set)
    for row in privacy_rows:
        metrics[row["attack_name"]].add(row["metric_name"])
    rows = [[attack, ", ".join(sorted(values))] for attack, values in sorted(metrics.items())]
    _write_both(tables_dir, "attack_metric_table", ["attack", "metrics"], rows)


def _utility_metric_table(utility_rows: list[dict[str, str]], tables_dir: Path) -> None:
    metrics = defaultdict(set)
    for row in utility_rows:
        name = row["metric_name"]
        if "_route_" in name:
            name = name.split("_route_", 1)[1]
        metrics[row["utility_name"]].add(name)
    rows = [[utility, ", ".join(sorted(values))] for utility, values in sorted(metrics.items())]
    _write_both(tables_dir, "utility_metric_table", ["utility", "metrics"], rows)


def _aggregate_highlights(
    privacy_rows: list[dict[str, str]],
    utility_rows: list[dict[str, str]],
    tables_dir: Path,
) -> None:
    rows = []

    checks = [
        ("floor_plan_leakage", "occupied_f1", privacy_rows, "privacy"),
        ("room_graph_leakage", "skeleton_iou", privacy_rows, "privacy"),
        ("routine_leakage", "visit_order_similarity", privacy_rows, "privacy"),
    ]
    for name, metric, source, family in checks:
        grouped = defaultdict(list)
        for row in source:
            if row.get("attack_name") == name and row.get("metric_name") == metric:
                value = _safe_float(row["value"])
                if value is not None:
                    grouped[row["filter_name"]].append(value)
        for filter_name, values in sorted(grouped.items()):
            rows.append([family, name, filter_name, metric, _fmt(_mean(values))])

    grouped = defaultdict(list)
    for row in utility_rows:
        if row.get("utility_name") == "astar_navigation" and row.get("metric_name", "").endswith("_route_success"):
            value = _safe_float(row["value"])
            if value is not None:
                grouped[row["filter_name"]].append(value)
    for filter_name, values in sorted(grouped.items()):
        rows.append(["utility", "astar_navigation", filter_name, "route_success", _fmt(_mean(values))])

    _write_both(
        tables_dir,
        "aggregate_highlights",
        ["family", "name", "filter", "metric", "mean"],
        rows,
    )


def _release_table(tables_dir: Path) -> None:
    rows = [
        ["raw ROS bags", "no", "private lab data; never commit"],
        ["unreviewed RGB keyframes", "no", "private until manual safety review"],
        ["contact sheets", "no by default", "review artifact only"],
        ["processed maps", "conditional", "release only after privacy review"],
        ["trajectories", "conditional", "release only after privacy review"],
        ["aggregate CSVs", "yes", "safe if derived from reviewed artifacts"],
        ["figures/tables", "yes", "safe if derived from aggregate CSVs"],
        ["code/configs/docs", "yes", "public reproducibility package"],
    ]
    _write_both(tables_dir, "release_package_table", ["item", "release", "reason"], rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    args = parser.parse_args()

    config = load_experiment_config(args.config)
    paths = load_yaml(config["paths_config"])
    filters = load_yaml(config["filters_config"])

    tables_dir = resolve_repo_path(paths["tables_dir"])
    results_dir = resolve_repo_path(paths["results_dir"])
    privacy_rows = _read_csv(results_dir / "privacy_results.csv")
    utility_rows = _read_csv(results_dir / "utility_results.csv")

    _run_metadata(config, tables_dir)
    _artifact_modality(config, tables_dir)
    _filter_table(filters, tables_dir)
    _attack_metric_table(privacy_rows, tables_dir)
    _utility_metric_table(utility_rows, tables_dir)
    _aggregate_highlights(privacy_rows, utility_rows, tables_dir)
    _release_table(tables_dir)


if __name__ == "__main__":
    main()
