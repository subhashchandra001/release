from __future__ import annotations

import numpy as np
import pytest

from privatemap.attacks.geometry_attack import geometry_leakage_score
from privatemap.metrics.geometry_metrics import bounding_box_volume, chamfer_distance


def test_chamfer_distance_zero_for_identical_points() -> None:
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
    assert chamfer_distance(points, points) == pytest.approx(0.0)
    assert bounding_box_volume(points) == pytest.approx(0.0)


def test_geometry_attack_similarity_decreases_with_distance() -> None:
    a = np.array([[0, 0, 0], [1, 0, 0]], dtype=float)
    b = np.array([[10, 0, 0], [11, 0, 0]], dtype=float)
    score = geometry_leakage_score(a, b)
    assert score["chamfer_distance"] > 0
    assert 0 < score["similarity"] < 1
