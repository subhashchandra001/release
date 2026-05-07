from __future__ import annotations

import numpy as np
import pytest

from privatemap.attacks.floorplan_attack import FloorPlanAttackError, floor_plan_leakage


def test_floor_plan_leakage_reports_overlap_metrics() -> None:
    reference = np.array([[0, 100, 100], [0, -1, 0]], dtype=np.int8)
    released = np.array([[0, 100, 0], [0, -1, 100]], dtype=np.int8)

    result = floor_plan_leakage(reference, released)

    assert result.attack_name == "floor_plan_leakage"
    assert result.metrics["occupied_iou"] == pytest.approx(1 / 3)
    assert result.metrics["occupied_precision"] == pytest.approx(0.5)
    assert result.metrics["occupied_recall"] == pytest.approx(0.5)
    assert result.metrics["known_cell_iou"] == 1.0


def test_floor_plan_leakage_rejects_shape_mismatch() -> None:
    with pytest.raises(FloorPlanAttackError, match="same shape"):
        floor_plan_leakage(np.zeros((2, 2), dtype=np.int8), np.zeros((3, 3), dtype=np.int8))
