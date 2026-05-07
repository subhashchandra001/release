"""Geometry metrics for point sets and point clouds."""

from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


class GeometryMetricError(ValueError):
    """Raised when geometry metric inputs are invalid."""


def _points(points: object) -> np.ndarray:
    if hasattr(points, "points"):
        array = np.asarray(points.points, dtype=float)
    else:
        array = np.asarray(points, dtype=float)
    if array.ndim != 2 or array.shape[1] != 3 or len(array) == 0:
        raise GeometryMetricError("Expected a non-empty Nx3 point array")
    return array


def chamfer_distance(a: object, b: object) -> float:
    points_a = _points(a)
    points_b = _points(b)
    tree_a = cKDTree(points_a)
    tree_b = cKDTree(points_b)
    dist_ab, _ = tree_b.query(points_a, k=1)
    dist_ba, _ = tree_a.query(points_b, k=1)
    return float(np.mean(dist_ab**2) + np.mean(dist_ba**2))


def centroid_distance(a: object, b: object) -> float:
    points_a = _points(a)
    points_b = _points(b)
    return float(np.linalg.norm(points_a.mean(axis=0) - points_b.mean(axis=0)))


def bounding_box_volume(points: object) -> float:
    array = _points(points)
    extent = array.max(axis=0) - array.min(axis=0)
    return float(np.prod(extent))
