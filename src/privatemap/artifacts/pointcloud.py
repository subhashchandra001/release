"""Point-cloud artifact helpers."""

from __future__ import annotations

from pathlib import Path

from privatemap.io.pointcloud_io import read_point_cloud, write_point_cloud


class PointCloudArtifactError(ValueError):
    """Raised when point-cloud artifact inputs are missing or invalid."""


def read_pointcloud_artifact(path: str | Path):
    """Read an Open3D-supported point-cloud artifact."""

    return read_point_cloud(path)


def write_pointcloud_artifact(cloud, path: str | Path) -> None:
    """Write an Open3D-supported point-cloud artifact."""

    write_point_cloud(cloud, path)


def export_from_rosbag(*_args: object, **_kwargs: object) -> None:
    """Fail clearly until live ROS extraction is implemented."""

    raise NotImplementedError(
        "Point-cloud export from ROS bags is not implemented. Provide a PCD/PLY "
        "artifact exported by a ROS/Open3D tool under data/processed/<run_id>/."
    )
