"""Privacy filters for Open3D point clouds."""

from __future__ import annotations

import numpy as np

from privatemap.io.pointcloud_io import PointCloudIOError, point_cloud_from_xyz, point_cloud_to_xyz


class PointCloudFilterError(ValueError):
    """Raised when point-cloud filter parameters are invalid."""


def voxel_downsample(cloud, voxel_size: float):
    if voxel_size <= 0:
        raise PointCloudFilterError("voxel_size must be positive")
    if cloud is None or cloud.is_empty():
        raise PointCloudFilterError("Point cloud is empty")
    return cloud.voxel_down_sample(voxel_size)


def crop_bounds(
    cloud,
    min_bound: tuple[float, float, float],
    max_bound: tuple[float, float, float],
):
    points = point_cloud_to_xyz(cloud)
    min_array = np.asarray(min_bound, dtype=float)
    max_array = np.asarray(max_bound, dtype=float)
    if min_array.shape != (3,) or max_array.shape != (3,):
        raise PointCloudFilterError("Bounds must be 3-D")
    mask = np.all((points >= min_array) & (points <= max_array), axis=1)
    if not np.any(mask):
        raise PointCloudIOError("Crop removed every point")
    return point_cloud_from_xyz(points[mask])


def add_gaussian_noise(cloud, sigma: float, *, seed: int | None = None):
    if sigma < 0:
        raise PointCloudFilterError("sigma must be non-negative")
    points = point_cloud_to_xyz(cloud)
    rng = np.random.default_rng(seed)
    return point_cloud_from_xyz(points + rng.normal(0.0, sigma, size=points.shape))


def remove_radius_outliers(cloud, nb_points: int, radius: float):
    if nb_points <= 0 or radius <= 0:
        raise PointCloudFilterError("nb_points and radius must be positive")
    filtered, _ = cloud.remove_radius_outlier(nb_points=nb_points, radius=radius)
    if filtered.is_empty():
        raise PointCloudFilterError("Outlier removal removed every point")
    return filtered
