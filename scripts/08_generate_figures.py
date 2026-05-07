#!/usr/bin/env python
"""Generate NeurIPS 2026 paper figures from real result CSVs."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib.pyplot as plt

from privatemap.io.config import load_experiment_config, load_yaml, resolve_repo_path


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Required CSV does not exist: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _safe_float(value: str) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isinf(out) or math.isnan(out):
        return None
    return out


def _mean(values: Iterable[float]) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else 0.0


def _bar(path: Path, labels: list[str], values: list[float], *, title: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(max(7, len(labels) * 0.8), 4.5))
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=35, labelsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"Wrote figure: {path}")


def _line(path: Path, series: dict[str, list[tuple[str, float]]], *, title: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for name, points in series.items():
        labels = [p[0] for p in points]
        values = [p[1] for p in points]
        ax.plot(labels, values, marker="o", label=name)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=35, labelsize=8)
    ax.grid(axis="y", alpha=0.25)
    if len(series) > 1:
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"Wrote figure: {path}")


def _run_scale_figure(config: dict, figures_dir: Path) -> None:
    runs = config["experiment"]["runs"]
    counts = Counter(str(run.get("environment_id", run["run_id"].split("_", 1)[0])) for run in runs)
    labels = sorted(counts)
    _bar(
        figures_dir / "run_scale_by_environment.png",
        labels,
        [float(counts[label]) for label in labels],
        title="TurtleBot4 runs by environment/layout variant",
        ylabel="Run count",
    )


def _privacy_leakage_figure(privacy_rows: list[dict[str, str]], figures_dir: Path) -> None:
    metrics = {"floor_plan_leakage": "occupied_f1", "room_graph_leakage": "skeleton_iou"}
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in privacy_rows:
        if metrics.get(row["attack_name"]) == row["metric_name"]:
            value = _safe_float(row["value"])
            if value is not None:
                grouped[row["filter_name"]].append(value)
    labels = sorted(grouped)
    _bar(
        figures_dir / "privacy_leakage_by_filter.png",
        labels,
        [_mean(grouped[label]) for label in labels],
        title="Mean structural privacy leakage by filter",
        ylabel="Leakage score",
    )


def _navigation_success_figure(utility_rows: list[dict[str, str]], figures_dir: Path) -> None:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in utility_rows:
        if row["utility_name"] == "astar_navigation" and row["metric_name"].endswith("_route_success"):
            value = _safe_float(row["value"])
            if value is not None:
                grouped[row["filter_name"]].append(value)
    labels = sorted(grouped)
    _bar(
        figures_dir / "navigation_success_by_filter.png",
        labels,
        [_mean(grouped[label]) for label in labels],
        title="A* navigation success by occupancy filter",
        ylabel="Mean route success",
    )


def _tradeoff_figure(
    privacy_rows: list[dict[str, str]],
    utility_rows: list[dict[str, str]],
    figures_dir: Path,
) -> None:
    leakage: dict[str, list[float]] = defaultdict(list)
    utility: dict[str, list[float]] = defaultdict(list)

    for row in privacy_rows:
        if row["attack_name"] == "floor_plan_leakage" and row["metric_name"] == "occupied_f1":
            value = _safe_float(row["value"])
            if value is not None:
                leakage[row["filter_name"]].append(value)

    for row in utility_rows:
        if row["utility_name"] == "astar_navigation" and row["metric_name"].endswith("_route_success"):
            value = _safe_float(row["value"])
            if value is not None:
                utility[row["filter_name"]].append(value)

    labels = sorted(set(leakage) & set(utility))
    fig, ax = plt.subplots(figsize=(6.5, 5.2))
    xs = [_mean(leakage[label]) for label in labels]
    ys = [_mean(utility[label]) for label in labels]
    ax.scatter(xs, ys)
    for label, x, y in zip(labels, xs, ys):
        ax.annotate(label, (x, y), fontsize=7, xytext=(4, 3), textcoords="offset points")
    ax.set_title("Privacy–utility trade-off")
    ax.set_xlabel("Mean floor-plan leakage: occupied F1")
    ax.set_ylabel("Mean A* route success")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out = figures_dir / "privacy_utility_tradeoff.png"
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"Wrote figure: {out}")


def _room_graph_figure(privacy_rows: list[dict[str, str]], figures_dir: Path) -> None:
    series: dict[str, list[tuple[str, float]]] = {}
    for metric in ["connectivity_similarity", "doorway_recall", "skeleton_iou"]:
        grouped: dict[str, list[float]] = defaultdict(list)
        for row in privacy_rows:
            if row["attack_name"] == "room_graph_leakage" and row["metric_name"] == metric:
                value = _safe_float(row["value"])
                if value is not None:
                    grouped[row["filter_name"]].append(value)
        series[metric] = [(label, _mean(grouped[label])) for label in sorted(grouped)]
    _line(
        figures_dir / "room_graph_recovery.png",
        series,
        title="Room-graph recovery metrics",
        ylabel="Mean score",
    )


def _routine_figure(privacy_rows: list[dict[str, str]], figures_dir: Path) -> None:
    series: dict[str, list[tuple[str, float]]] = {}
    for metric in ["visit_order_similarity", "loop_similarity", "repeat_count_recovery"]:
        grouped: dict[str, list[float]] = defaultdict(list)
        for row in privacy_rows:
            if row["attack_name"] == "routine_leakage" and row["metric_name"] == metric:
                value = _safe_float(row["value"])
                if value is not None:
                    grouped[row["filter_name"]].append(value)
        series[metric] = [(label, _mean(grouped[label])) for label in sorted(grouped)]
    _line(
        figures_dir / "routine_leakage.png",
        series,
        title="Routine leakage under trajectory filters",
        ylabel="Mean score",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    args = parser.parse_args()

    config = load_experiment_config(args.config)
    paths = load_yaml(config["paths_config"])
    figures_dir = resolve_repo_path(paths["figures_dir"])
    results_dir = resolve_repo_path(paths["results_dir"])
    figures_dir.mkdir(parents=True, exist_ok=True)

    privacy_rows = _read_rows(results_dir / "privacy_results.csv")
    utility_rows = _read_rows(results_dir / "utility_results.csv")

    _run_scale_figure(config, figures_dir)
    _privacy_leakage_figure(privacy_rows, figures_dir)
    _navigation_success_figure(utility_rows, figures_dir)
    _tradeoff_figure(privacy_rows, utility_rows, figures_dir)
    _room_graph_figure(privacy_rows, figures_dir)
    _routine_figure(privacy_rows, figures_dir)


if __name__ == "__main__":
    main()
