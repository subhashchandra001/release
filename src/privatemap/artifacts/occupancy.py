"""Occupancy-map artifact helpers."""

from __future__ import annotations

from pathlib import Path

from privatemap.io.map_io import OccupancyMap, load_occupancy_map, save_occupancy_map


class OccupancyArtifactError(ValueError):
    """Raised when occupancy artifact inputs are missing or invalid."""


def read_occupancy_artifact(path: str | Path) -> OccupancyMap:
    """Read a ROS map-server YAML/PGM artifact."""

    return load_occupancy_map(path)


def write_occupancy_artifact(map_data: OccupancyMap, path: str | Path) -> None:
    """Write a ROS map-server YAML/PGM artifact."""

    save_occupancy_map(map_data, path)


def export_from_rosbag(*_args: object, **_kwargs: object) -> None:
    """Fail clearly until live ROS extraction is implemented."""

    raise NotImplementedError(
        "Occupancy export from ROS bags is not implemented. Save a map with "
        "ros2/save_map.sh and place map.yaml plus its PGM under data/processed/<run_id>/."
    )
