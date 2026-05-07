from __future__ import annotations

import pytest

from privatemap.artifacts.occupancy import read_occupancy_artifact
from privatemap.artifacts.semantics import read_semantic_detections, sensitive_class_names
from privatemap.artifacts.trajectory import read_trajectory_artifact
from privatemap.filters.combined_filter import apply_occupancy_filter, apply_trajectory_filter
from privatemap.io.rosbag_reader import RosbagReaderError, assert_rosbag_exists
from privatemap.utility.coverage_utility import trajectory_coverage


def test_artifact_wrappers_read_fixture_aliases() -> None:
    occupancy = read_occupancy_artifact("tests/fixtures/small_map.yaml")
    trajectory = read_trajectory_artifact("tests/fixtures/small_trajectory.csv")
    detections = read_semantic_detections("tests/fixtures/fake_detections.csv")

    assert occupancy.shape == (4, 4)
    assert len(trajectory) == 4
    assert sensitive_class_names(detections) == {"screen"}


def test_combined_filter_dispatch_and_coverage() -> None:
    occupancy = read_occupancy_artifact("tests/fixtures/small_map.yaml")
    trajectory = read_trajectory_artifact("tests/fixtures/small_trajectory.csv")

    downsampled = apply_occupancy_filter(occupancy, "downsample", {"factor": 2})
    filtered_trajectory = apply_trajectory_filter(trajectory, "downsample", {"step": 2})
    coverage = trajectory_coverage(trajectory)

    assert downsampled.shape == (2, 2)
    assert len(filtered_trajectory) == 2
    assert coverage["num_poses"] == 4
    assert coverage["path_length"] == 3.0


def test_rosbag_reader_reports_missing_path() -> None:
    with pytest.raises(RosbagReaderError, match="does not exist"):
        assert_rosbag_exists("tests/fixtures/no_such_bag")
