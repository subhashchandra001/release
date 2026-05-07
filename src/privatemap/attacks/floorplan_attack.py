"""Floor-plan leakage attacks for occupancy maps."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from privatemap.io.map_io import OccupancyMap
from privatemap.metrics.segmentation_metrics import (
    intersection_over_union,
    precision_recall_f1,
)


class FloorPlanAttackError(ValueError):
    """Raised when floor-plan attack inputs are invalid."""


@dataclass(frozen=True)
class FloorPlanAttackResult:
    attack_name: str
    metrics: dict[str, float]


def _occupancy_array(map_or_grid: OccupancyMap | np.ndarray) -> np.ndarray:
    if isinstance(map_or_grid, OccupancyMap):
        array = map_or_grid.data
    else:
        array = np.asarray(map_or_grid)
    if array.ndim != 2:
        raise FloorPlanAttackError("Occupancy input must be a 2-D grid")
    invalid = set(np.unique(array).tolist()) - {-1, 0, 100}
    if invalid:
        raise FloorPlanAttackError(f"Occupancy grid contains invalid labels: {sorted(invalid)}")
    return array


def floor_plan_leakage(
    reference: OccupancyMap | np.ndarray,
    released: OccupancyMap | np.ndarray,
) -> FloorPlanAttackResult:
    """Measure how much occupied floor-plan structure remains in a released map.

    The attack treats occupied cells as the recoverable floor-plan signal and
    reports overlap-style metrics between the private reference map and released
    map. Unknown cells in either map are counted as not recovered.
    """

    reference_grid = _occupancy_array(reference)
    released_grid = _occupancy_array(released)
    if reference_grid.shape != released_grid.shape:
        raise FloorPlanAttackError(
            "reference and released occupancy grids must have the same shape: "
            f"{reference_grid.shape} != {released_grid.shape}"
        )

    truth = reference_grid == 100
    prediction = released_grid == 100
    prf = precision_recall_f1(truth, prediction)
    reference_occupied = int(truth.sum())
    released_occupied = int(prediction.sum())
    known_reference = reference_grid != -1
    known_released = released_grid != -1
    known_overlap = int(np.logical_and(known_reference, known_released).sum())
    known_union = int(np.logical_or(known_reference, known_released).sum())

    metrics = {
        "occupied_iou": intersection_over_union(truth, prediction),
        "occupied_precision": prf["precision"],
        "occupied_recall": prf["recall"],
        "occupied_f1": prf["f1"],
        "occupied_retention": (
            float(released_occupied / reference_occupied) if reference_occupied else 1.0
        ),
        "known_cell_iou": float(known_overlap / known_union) if known_union else 1.0,
    }
    return FloorPlanAttackResult("floor_plan_leakage", metrics)
