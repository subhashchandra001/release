"""Routine and repeated-route leakage attacks for trajectories."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from privatemap.io.trajectory_io import Trajectory, validate_trajectory
from privatemap.metrics.trajectory_metrics import edit_distance


class RoutineAttackError(ValueError):
    """Raised when routine attack inputs are invalid."""


@dataclass(frozen=True)
class RoutineAttackResult:
    attack_name: str
    metrics: dict[str, float]


def _pose_xy(row: object) -> tuple[float, float]:
    if hasattr(row, "x") and hasattr(row, "y"):
        return float(row.x), float(row.y)
    if isinstance(row, dict):
        return float(row["x"]), float(row["y"])
    raise RoutineAttackError(f"Unsupported trajectory pose type: {type(row)!r}")


def _xy_points(trajectory: Trajectory) -> np.ndarray:
    return np.asarray([_pose_xy(row) for row in trajectory], dtype=float)


def _compress_symbols(symbols: list[str]) -> list[str]:
    compressed: list[str] = []
    for symbol in symbols:
        if not compressed or compressed[-1] != symbol:
            compressed.append(symbol)
    return compressed


def _route_symbols(points: np.ndarray, grid_size: float) -> list[str]:
    if grid_size <= 0:
        raise RoutineAttackError("grid_size must be positive")
    symbols = [f"{math.floor(x / grid_size)}:{math.floor(y / grid_size)}" for x, y in points]
    return _compress_symbols(symbols)


def _repeat_count(symbols: list[str]) -> int:
    if len(symbols) < 4:
        return 0
    half = len(symbols) // 2
    best = 0
    for window in range(2, max(3, half + 1)):
        chunks = [symbols[i : i + window] for i in range(0, len(symbols) - window + 1, window)]
        if len(chunks) < 2:
            continue
        first = chunks[0]
        repeats = sum(1 for chunk in chunks[1:] if chunk == first)
        best = max(best, repeats)
    return int(best)


def _dwell_histogram(symbols: list[str]) -> dict[str, int]:
    hist: dict[str, int] = {}
    for symbol in symbols:
        hist[symbol] = hist.get(symbol, 0) + 1
    return hist


def _hist_l1_error(a: dict[str, int], b: dict[str, int]) -> float:
    keys = set(a) | set(b)
    total = sum(a.values()) or 1
    return float(sum(abs(a.get(k, 0) - b.get(k, 0)) for k in keys) / total)


def routine_leakage(
    reference: Trajectory,
    released: Trajectory,
    *,
    grid_size: float = 0.75,
) -> RoutineAttackResult:
    """Measure how much repeated route/routine structure survives filtering."""

    validate_trajectory(reference)
    validate_trajectory(released)

    ref_symbols = _route_symbols(_xy_points(reference), grid_size)
    rel_symbols = _route_symbols(_xy_points(released), grid_size)

    distance = edit_distance(ref_symbols, rel_symbols)
    normalizer = max(len(ref_symbols), len(rel_symbols), 1)
    visit_order_similarity = float(1.0 - distance / normalizer)

    ref_repeats = _repeat_count(ref_symbols)
    rel_repeats = _repeat_count(rel_symbols)
    repeat_count_recovery = (
        float(min(ref_repeats, rel_repeats) / ref_repeats) if ref_repeats > 0 else 1.0
    )

    route_class_accuracy = 1.0 if ref_symbols[:1] == rel_symbols[:1] and ref_symbols[-1:] == rel_symbols[-1:] else 0.0
    dwell_time_error = _hist_l1_error(_dwell_histogram(ref_symbols), _dwell_histogram(rel_symbols))
    loop_similarity = float(np.mean([visit_order_similarity, repeat_count_recovery]))

    metrics = {
        "route_class_accuracy": float(route_class_accuracy),
        "repeat_count_recovery": repeat_count_recovery,
        "visit_order_similarity": visit_order_similarity,
        "dwell_time_error": dwell_time_error,
        "loop_similarity": loop_similarity,
        "reference_repeat_count": float(ref_repeats),
        "released_repeat_count": float(rel_repeats),
    }
    return RoutineAttackResult("routine_leakage", metrics)
