"""Point-cloud I/O helpers with optional Open3D support."""

from __future__ import annotations

from pathlib import Path

import numpy as np


class PointCloudIOError(ValueError):
    """Raised when point-cloud I/O fails."""


def _open3d():
    try:
        import open3d as o3d  # type: ignore
    except ImportError as exc:
        raise PointCloudIOError("Open3D is required for point-cloud I/O") from exc
    return o3d


def open3d_available() -> bool:
    try:
        _open3d()
    except PointCloudIOError:
        return False
    return True


def read_point_cloud(path: str | Path):
    cloud_path = Path(path)
    if not cloud_path.exists():
        raise PointCloudIOError(f"Point cloud does not exist: {cloud_path}")
    o3d = _open3d()
    cloud = o3d.io.read_point_cloud(str(cloud_path))
    if cloud.is_empty():
        raise PointCloudIOError(f"Point cloud contains no points: {cloud_path}")
    return cloud


def write_point_cloud(cloud, path: str | Path) -> None:
    o3d = _open3d()
    if cloud is None or cloud.is_empty():
        raise PointCloudIOError("Refusing to write an empty point cloud")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not o3d.io.write_point_cloud(str(destination), cloud):
        raise PointCloudIOError(f"Failed to write point cloud: {destination}")


def point_cloud_from_xyz(points: np.ndarray):
    o3d = _open3d()
    array = np.asarray(points, dtype=float)
    if array.ndim != 2 or array.shape[1] != 3 or len(array) == 0:
        raise PointCloudIOError("points must be a non-empty Nx3 array")
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(array)
    return cloud


def point_cloud_to_xyz(cloud) -> np.ndarray:
    if cloud is None or cloud.is_empty():
        raise PointCloudIOError("Point cloud is empty")
    return np.asarray(cloud.points, dtype=float)
