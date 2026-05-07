from __future__ import annotations

import pytest

from privatemap.attacks.trajectory_attack import trajectory_leakage
from privatemap.filters.trajectory_filters import downsample, shifted
from privatemap.io.trajectory_io import read_trajectory_csv


def test_trajectory_leakage_for_shifted_same_length_trajectory() -> None:
    reference = read_trajectory_csv("tests/fixtures/trajectory.csv")
    released = shifted(reference, dx=0.5)

    result = trajectory_leakage(reference, released)

    assert result.attack_name == "trajectory_leakage"
    assert result.metrics["pose_count_retention"] == 1.0
    assert result.metrics["xy_rmse"] == 0.5
    assert result.metrics["path_length_retention"] == 1.0


def test_trajectory_leakage_for_downsampled_trajectory() -> None:
    reference = read_trajectory_csv("tests/fixtures/trajectory.csv")
    released = downsample(reference, 2)

    result = trajectory_leakage(reference, released)

    assert result.metrics["pose_count_retention"] == 0.5
    assert result.metrics["xy_rmse"] != result.metrics["xy_rmse"]


def test_trajectory_leakage_room_sequence_metrics() -> None:
    reference = read_trajectory_csv("tests/fixtures/trajectory.csv")
    rooms = [
        {"name": "left", "bounds": [-1, -1, 0.5, 2]},
        {"name": "right", "bounds": [0.5, -1, 3, 2]},
    ]

    result = trajectory_leakage(reference, reference, rooms=rooms)

    assert result.metrics["room_sequence_edit_distance"] == 0.0
    assert result.metrics["room_sequence_similarity"] == pytest.approx(1.0)
