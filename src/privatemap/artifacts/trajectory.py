"""Trajectory artifact helpers."""

from __future__ import annotations

from pathlib import Path

from privatemap.io.trajectory_io import Trajectory, read_trajectory_csv, write_trajectory_csv


class TrajectoryArtifactError(ValueError):
    """Raised when trajectory artifact inputs are missing or invalid."""


def read_trajectory_artifact(path: str | Path) -> Trajectory:
    """Read a benchmark trajectory CSV artifact."""

    return read_trajectory_csv(path)


def write_trajectory_artifact(trajectory: Trajectory, path: str | Path) -> None:
    """Write a benchmark trajectory CSV artifact."""

    write_trajectory_csv(trajectory, path)


def export_from_rosbag(*_args: object, **_kwargs: object) -> None:
    """Fail clearly until live ROS extraction is implemented."""

    raise NotImplementedError(
        "Trajectory export from ROS bags is not implemented. Provide a "
        "trajectory.csv matching docs/data_schema.md under data/processed/<run_id>/."
    )
