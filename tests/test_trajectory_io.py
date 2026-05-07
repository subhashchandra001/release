from __future__ import annotations

import pytest

from privatemap.io.trajectory_io import (
    TRAJECTORY_COLUMNS,
    TrajectoryIOError,
    read_trajectory_csv,
    write_trajectory_csv,
)


def test_read_trajectory_csv() -> None:
    trajectory = read_trajectory_csv("tests/fixtures/trajectory.csv")
    assert len(trajectory) == 4
    assert list(trajectory.to_rows()[0]) == TRAJECTORY_COLUMNS
    assert trajectory.column("x") == [0.0, 1.0, 1.0, 2.0]


def test_write_trajectory_roundtrip(tmp_path) -> None:
    trajectory = read_trajectory_csv("tests/fixtures/trajectory.csv")
    destination = tmp_path / "trajectory.csv"
    write_trajectory_csv(trajectory, destination)
    loaded = read_trajectory_csv(destination)
    assert loaded == trajectory


def test_read_trajectory_rejects_missing_column(tmp_path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("run_id,timestamp,x\nrun_a,0,1\n", encoding="utf-8")
    with pytest.raises(TrajectoryIOError, match="missing required"):
        read_trajectory_csv(bad_csv)
