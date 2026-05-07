"""Compactness metrics for occupancy maps."""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from privatemap.io.map_io import OccupancyMap


class MapCompactnessError(ValueError):
    """Raised when compactness inputs are invalid."""


def _grid(map_or_grid: OccupancyMap | np.ndarray) -> np.ndarray:
    array = map_or_grid.data if isinstance(map_or_grid, OccupancyMap) else np.asarray(map_or_grid)
    if array.ndim != 2:
        raise MapCompactnessError("Occupancy grid must be 2-D")
    invalid = set(np.unique(array).tolist()) - {-1, 0, 100}
    if invalid:
        raise MapCompactnessError(f"Occupancy grid contains invalid labels: {sorted(invalid)}")
    return array


def _perimeter_edges(mask: np.ndarray) -> int:
    padded = np.pad(mask.astype(bool), 1, constant_values=False)
    center = padded[1:-1, 1:-1]
    perimeter = 0
    perimeter += int(np.logical_and(center, ~padded[:-2, 1:-1]).sum())
    perimeter += int(np.logical_and(center, ~padded[2:, 1:-1]).sum())
    perimeter += int(np.logical_and(center, ~padded[1:-1, :-2]).sum())
    perimeter += int(np.logical_and(center, ~padded[1:-1, 2:]).sum())
    return perimeter


def compactness_metrics(
    map_or_grid: OccupancyMap | np.ndarray,
    *,
    target_label: int = 100,
) -> dict[str, float]:
    """Compute compactness metrics for cells matching ``target_label``."""

    if target_label not in {-1, 0, 100}:
        raise MapCompactnessError("target_label must be one of -1, 0, or 100")
    array = _grid(map_or_grid)
    mask = array == target_label
    area = int(mask.sum())
    if area == 0:
        return {
            "area_cells": 0.0,
            "perimeter_edges": 0.0,
            "compactness": 0.0,
            "component_count": 0.0,
            "largest_component_fraction": 0.0,
            "bbox_fill_ratio": 0.0,
        }

    perimeter = _perimeter_edges(mask)
    labels, count = ndimage.label(mask)
    component_sizes = ndimage.sum(mask, labels, index=np.arange(1, count + 1))
    largest = float(np.max(component_sizes)) if count else 0.0
    rows, cols = np.where(mask)
    bbox_area = float((rows.max() - rows.min() + 1) * (cols.max() - cols.min() + 1))
    compactness = float((4.0 * np.pi * area) / (perimeter**2)) if perimeter else 0.0
    return {
        "area_cells": float(area),
        "perimeter_edges": float(perimeter),
        "compactness": compactness,
        "component_count": float(count),
        "largest_component_fraction": float(largest / area),
        "bbox_fill_ratio": float(area / bbox_area) if bbox_area else 0.0,
    }
