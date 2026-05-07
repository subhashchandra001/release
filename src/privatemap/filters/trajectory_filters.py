"""Privacy filters and summaries for trajectories."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

import numpy as np

from privatemap.io.trajectory_io import Trajectory, TrajectoryPose, validate_trajectory


class TrajectoryFilterError(ValueError):
    """Raised when trajectory filter inputs are invalid."""


def downsample(trajectory: Trajectory, step: int) -> Trajectory:
    validate_trajectory(trajectory)
    if step <= 0:
        raise TrajectoryFilterError("step must be positive")
    return Trajectory(tuple(trajectory.poses[::step]))


def spatial_quantize(trajectory: Trajectory, grid_size: float) -> Trajectory:
    validate_trajectory(trajectory)
    if grid_size <= 0:
        raise TrajectoryFilterError("grid_size must be positive")
    poses = []
    for pose in trajectory:
        poses.append(
            replace(
                pose,
                x=float(np.round(pose.x / grid_size) * grid_size),
                y=float(np.round(pose.y / grid_size) * grid_size),
                z=float(np.round(pose.z / grid_size) * grid_size),
            )
        )
    return Trajectory(tuple(poses))


def room_sequence(
    trajectory: Trajectory,
    rooms: Sequence[Mapping[str, Any]],
    *,
    unknown_label: str = "unknown",
) -> list[str]:
    """Convert poses to a compressed sequence of room labels."""

    validate_trajectory(trajectory)
    labels: list[str] = []
    for pose in trajectory:
        label_name = unknown_label
        for room in rooms:
            name = room.get("name")
            bounds = room.get("bounds")
            if not isinstance(name, str) or not isinstance(bounds, Sequence) or len(bounds) != 4:
                raise TrajectoryFilterError("Each room must have a string name and four bounds")
            xmin, ymin, xmax, ymax = (float(value) for value in bounds)
            if xmin <= pose.x <= xmax and ymin <= pose.y <= ymax:
                label_name = name
                break
        if not labels or labels[-1] != label_name:
            labels.append(label_name)
    return labels


def coverage_summary(trajectory: Trajectory) -> dict[str, float | int]:
    validate_trajectory(trajectory)
    poses = list(trajectory)
    xy = np.array([[pose.x, pose.y] for pose in poses], dtype=float)
    path_length = float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum()) if len(xy) > 1 else 0.0
    xs = [pose.x for pose in poses]
    ys = [pose.y for pose in poses]
    timestamps = [pose.timestamp for pose in poses]
    min_x = float(min(xs))
    max_x = float(max(xs))
    min_y = float(min(ys))
    max_y = float(max(ys))
    return {
        "num_poses": int(len(poses)),
        "duration": float(max(timestamps) - min(timestamps)),
        "path_length": path_length,
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "bbox_area": float((max_x - min_x) * (max_y - min_y)),
    }


def shifted(trajectory: Trajectory, *, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> Trajectory:
    validate_trajectory(trajectory)
    poses: list[TrajectoryPose] = [
        replace(pose, x=pose.x + dx, y=pose.y + dy, z=pose.z + dz) for pose in trajectory
    ]
    return Trajectory(tuple(poses))
