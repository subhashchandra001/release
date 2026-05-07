"""Trajectory leakage attacks."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from privatemap.filters.trajectory_filters import coverage_summary, room_sequence
from privatemap.io.trajectory_io import Trajectory, validate_trajectory
from privatemap.metrics.trajectory_metrics import edit_distance, trajectory_rmse


class TrajectoryAttackError(ValueError):
    """Raised when trajectory attack inputs are invalid."""


@dataclass(frozen=True)
class TrajectoryAttackResult:
    attack_name: str
    metrics: dict[str, float]


def _path_length(trajectory: Trajectory) -> float:
    return float(coverage_summary(trajectory)["path_length"])


def _bbox_iou(reference: dict[str, float | int], released: dict[str, float | int]) -> float:
    xmin = max(float(reference["min_x"]), float(released["min_x"]))
    ymin = max(float(reference["min_y"]), float(released["min_y"]))
    xmax = min(float(reference["max_x"]), float(released["max_x"]))
    ymax = min(float(reference["max_y"]), float(released["max_y"]))
    intersection = max(0.0, xmax - xmin) * max(0.0, ymax - ymin)
    ref_area = float(reference["bbox_area"])
    rel_area = float(released["bbox_area"])
    union = ref_area + rel_area - intersection
    return float(intersection / union) if union > 0 else 1.0


def trajectory_leakage(
    reference: Trajectory,
    released: Trajectory,
    *,
    rooms: list[dict[str, object]] | None = None,
) -> TrajectoryAttackResult:
    """Measure recoverability of a released trajectory against a private reference."""

    validate_trajectory(reference)
    validate_trajectory(released)

    reference_summary = coverage_summary(reference)
    released_summary = coverage_summary(released)
    reference_length = _path_length(reference)
    released_length = _path_length(released)
    metrics = {
        "pose_count_retention": float(len(released) / len(reference)),
        "duration_retention": (
            float(released_summary["duration"]) / float(reference_summary["duration"])
            if float(reference_summary["duration"]) > 0
            else 1.0
        ),
        "path_length_retention": (
            released_length / reference_length if reference_length > 0 else 1.0
        ),
        "bbox_iou": _bbox_iou(reference_summary, released_summary),
    }

    if len(reference) == len(released):
        metrics["xy_rmse"] = trajectory_rmse(reference, released, columns=("x", "y"))
    else:
        metrics["xy_rmse"] = float("nan")

    if rooms is not None:
        try:
            ref_rooms = room_sequence(reference, rooms)
            rel_rooms = room_sequence(released, rooms)
        except ValueError as exc:
            raise TrajectoryAttackError(str(exc)) from exc
        distance = edit_distance(ref_rooms, rel_rooms)
        normalizer = max(len(ref_rooms), len(rel_rooms), 1)
        metrics["room_sequence_edit_distance"] = float(distance)
        metrics["room_sequence_similarity"] = float(1.0 - distance / normalizer)

    for name, value in metrics.items():
        if not isinstance(value, float) or (np.isnan(value) and name != "xy_rmse"):
            raise TrajectoryAttackError(f"Invalid trajectory leakage metric {name}: {value}")
    return TrajectoryAttackResult("trajectory_leakage", metrics)
