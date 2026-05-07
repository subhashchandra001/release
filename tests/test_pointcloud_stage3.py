from __future__ import annotations

import importlib.util

import numpy as np
import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("open3d") is None,
    reason="Open3D unavailable",
)

from privatemap.filters.pointcloud_filters import add_gaussian_noise, crop_bounds, voxel_downsample
from privatemap.io.pointcloud_io import point_cloud_from_xyz, point_cloud_to_xyz


def test_pointcloud_filters_with_open3d() -> None:
    cloud = point_cloud_from_xyz(
        np.array([[0, 0, 0], [0.01, 0, 0], [1, 1, 1], [2, 2, 2]], dtype=float)
    )
    downsampled = voxel_downsample(cloud, 0.05)
    assert len(point_cloud_to_xyz(downsampled)) <= 4
    cropped = crop_bounds(cloud, (0, 0, 0), (1, 1, 1))
    assert len(point_cloud_to_xyz(cropped)) == 3
    noisy = add_gaussian_noise(cropped, 0.0, seed=1)
    assert np.allclose(point_cloud_to_xyz(noisy), point_cloud_to_xyz(cropped))
