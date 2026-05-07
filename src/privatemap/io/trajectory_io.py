"""Trajectory CSV I/O."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class TrajectoryIOError(ValueError):
    """Raised when a trajectory CSV is missing or malformed."""


TRAJECTORY_COLUMNS = [
    "run_id",
    "timestamp",
    "x",
    "y",
    "z",
    "qx",
    "qy",
    "qz",
    "qw",
    "yaw",
]

NUMERIC_TRAJECTORY_COLUMNS = [
    "timestamp",
    "x",
    "y",
    "z",
    "qx",
    "qy",
    "qz",
    "qw",
    "yaw",
]


@dataclass(frozen=True)
class TrajectoryPose:
    run_id: str
    timestamp: float
    x: float
    y: float
    z: float
    qx: float
    qy: float
    qz: float
    qw: float
    yaw: float

    def to_row(self) -> dict[str, str | float]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "qx": self.qx,
            "qy": self.qy,
            "qz": self.qz,
            "qw": self.qw,
            "yaw": self.yaw,
        }


@dataclass(frozen=True)
class Trajectory:
    poses: tuple[TrajectoryPose, ...]

    def __post_init__(self) -> None:
        if not self.poses:
            raise TrajectoryIOError("Trajectory must contain at least one row")

    def __len__(self) -> int:
        return len(self.poses)

    def __iter__(self) -> Iterator[TrajectoryPose]:
        return iter(self.poses)

    def column(self, name: str) -> list[str] | list[float]:
        if name not in TRAJECTORY_COLUMNS:
            raise TrajectoryIOError(f"Unknown trajectory column: {name}")
        return [getattr(pose, name) for pose in self.poses]

    def numeric_matrix(self, columns: Sequence[str]) -> list[list[float]]:
        for column in columns:
            if column not in NUMERIC_TRAJECTORY_COLUMNS:
                raise TrajectoryIOError(f"Column is not numeric: {column}")
        return [[float(getattr(pose, column)) for column in columns] for pose in self.poses]

    def to_rows(self) -> list[dict[str, str | float]]:
        return [pose.to_row() for pose in self.poses]


def _parse_pose(row: dict[str, Any], *, row_number: int) -> TrajectoryPose:
    missing = [column for column in TRAJECTORY_COLUMNS if column not in row]
    if missing:
        raise TrajectoryIOError(f"Trajectory row {row_number} missing column(s): {missing}")
    if not str(row["run_id"]):
        raise TrajectoryIOError(f"Trajectory row {row_number}: run_id must be non-empty")
    try:
        numeric = {column: float(row[column]) for column in NUMERIC_TRAJECTORY_COLUMNS}
    except (TypeError, ValueError) as exc:
        raise TrajectoryIOError(f"Trajectory row {row_number} contains non-numeric values") from exc
    return TrajectoryPose(run_id=str(row["run_id"]), **numeric)


def make_trajectory(rows: Iterable[dict[str, Any] | TrajectoryPose]) -> Trajectory:
    poses: list[TrajectoryPose] = []
    for index, row in enumerate(rows, start=1):
        if isinstance(row, TrajectoryPose):
            poses.append(row)
        else:
            poses.append(_parse_pose(row, row_number=index))
    return Trajectory(tuple(poses))


def validate_trajectory(trajectory: Trajectory) -> None:
    if not isinstance(trajectory, Trajectory):
        raise TrajectoryIOError("Expected a Trajectory instance")
    if not trajectory.poses:
        raise TrajectoryIOError("Trajectory must contain at least one row")


def read_trajectory_csv(path: str | Path) -> Trajectory:
    csv_path = Path(path)
    if not csv_path.exists():
        raise TrajectoryIOError(f"Trajectory CSV does not exist: {csv_path}")
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise TrajectoryIOError(f"Trajectory CSV is empty: {csv_path}")
            missing = [column for column in TRAJECTORY_COLUMNS if column not in reader.fieldnames]
            if missing:
                raise TrajectoryIOError(f"Trajectory is missing required column(s): {missing}")
            return make_trajectory(reader)
    except TrajectoryIOError:
        raise
    except OSError as exc:
        raise TrajectoryIOError(f"Failed to read trajectory CSV {csv_path}: {exc}") from exc


def write_trajectory_csv(trajectory: Trajectory, path: str | Path) -> None:
    validate_trajectory(trajectory)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRAJECTORY_COLUMNS)
        writer.writeheader()
        writer.writerows(trajectory.to_rows())
