"""Privacy filters for occupancy grids."""

from __future__ import annotations

import numpy as np
from scipy import ndimage


class OccupancyFilterError(ValueError):
    """Raised when an occupancy filter receives invalid parameters."""


def _validate_grid(grid: np.ndarray) -> np.ndarray:
    array = np.asarray(grid)
    if array.ndim != 2:
        raise OccupancyFilterError("Occupancy grid must be a 2-D array")
    invalid = set(np.unique(array).tolist()) - {-1, 0, 100}
    if invalid:
        raise OccupancyFilterError(f"Occupancy grid contains invalid labels: {sorted(invalid)}")
    return array.astype(np.int8, copy=False)


def downsample(grid: np.ndarray, factor: int) -> np.ndarray:
    """Downsample by block majority, preserving unknown when it dominates."""

    array = _validate_grid(grid)
    if factor <= 0:
        raise OccupancyFilterError("factor must be positive")
    if factor == 1:
        return array.copy()

    rows = array.shape[0] // factor
    cols = array.shape[1] // factor
    if rows == 0 or cols == 0:
        raise OccupancyFilterError("factor is larger than the occupancy grid")

    cropped = array[: rows * factor, : cols * factor]
    blocks = cropped.reshape(rows, factor, cols, factor).swapaxes(1, 2)
    output = np.empty((rows, cols), dtype=np.int8)
    labels = np.array([0, 100, -1], dtype=np.int16)
    for row in range(rows):
        for col in range(cols):
            block = blocks[row, col]
            counts = np.array([np.count_nonzero(block == value) for value in labels])
            output[row, col] = labels[int(np.argmax(counts))]
    return output


def blur(grid: np.ndarray, sigma: float) -> np.ndarray:
    """Blur occupancy probabilities and re-threshold to discrete labels."""

    array = _validate_grid(grid)
    if sigma < 0:
        raise OccupancyFilterError("sigma must be non-negative")
    if sigma == 0:
        return array.copy()

    probabilities = np.full(array.shape, 0.5, dtype=float)
    probabilities[array == 0] = 0.0
    probabilities[array == 100] = 1.0
    blurred = ndimage.gaussian_filter(probabilities, sigma=sigma)
    output = np.full(array.shape, -1, dtype=np.int8)
    output[blurred <= 0.25] = 0
    output[blurred >= 0.75] = 100
    return output


def add_noise(grid: np.ndarray, probability: float, *, seed: int | None = None) -> np.ndarray:
    """Randomly flip known free/occupied cells with the given probability."""

    array = _validate_grid(grid)
    if not 0 <= probability <= 1:
        raise OccupancyFilterError("probability must be in [0, 1]")
    rng = np.random.default_rng(seed)
    output = array.copy()
    known = output != -1
    flips = (rng.random(output.shape) < probability) & known
    output[(output == 0) & flips] = 100
    output[(output == 100) & flips] = 0
    return output


def remove_small_components(grid: np.ndarray, min_size: int) -> np.ndarray:
    """Remove connected occupied components smaller than ``min_size`` cells."""

    array = _validate_grid(grid)
    if min_size <= 0:
        raise OccupancyFilterError("min_size must be positive")
    output = array.copy()
    components, count = ndimage.label(array == 100)
    for component_id in range(1, int(count) + 1):
        mask = components == component_id
        if int(mask.sum()) < min_size:
            output[mask] = 0
    return output
