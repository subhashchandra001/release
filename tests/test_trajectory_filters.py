from __future__ import annotations

from privatemap.filters.trajectory_filters import (
    coverage_summary,
    downsample,
    room_sequence,
    spatial_quantize,
)
from privatemap.io.trajectory_io import read_trajectory_csv


def test_trajectory_filters_and_summary() -> None:
    trajectory = read_trajectory_csv("tests/fixtures/trajectory.csv")
    assert len(downsample(trajectory, step=2)) == 2
    quantized = spatial_quantize(trajectory, grid_size=1.0)
    assert quantized.column("x") == [0.0, 1.0, 1.0, 2.0]
    summary = coverage_summary(trajectory)
    assert summary["num_poses"] == 4
    assert summary["duration"] == 3.0
    assert summary["path_length"] == 3.0


def test_room_sequence_compresses_repeated_rooms() -> None:
    trajectory = read_trajectory_csv("tests/fixtures/trajectory.csv")
    rooms = [
        {"name": "lab", "bounds": [-1, -1, 1.5, 0.5]},
        {"name": "hall", "bounds": [0.5, 0.5, 3, 2]},
    ]
    assert room_sequence(trajectory, rooms) == ["lab", "hall"]
