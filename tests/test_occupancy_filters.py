from __future__ import annotations

import numpy as np

from privatemap.filters.occupancy_filters import (
    add_noise,
    blur,
    downsample,
    remove_small_components,
)


def test_downsample_uses_block_majority() -> None:
    grid = np.array(
        [
            [0, 0, 100, 100],
            [0, -1, 100, 100],
            [0, 0, 0, 100],
            [-1, -1, 0, 100],
        ],
        dtype=np.int8,
    )
    actual = downsample(grid, factor=2)
    np.testing.assert_array_equal(actual, np.array([[0, 100], [0, 0]], dtype=np.int8))


def test_blur_preserves_shape_and_labels() -> None:
    grid = np.zeros((5, 5), dtype=np.int8)
    grid[2, 2] = 100
    blurred = blur(grid, sigma=1.0)
    assert blurred.shape == grid.shape
    assert set(np.unique(blurred).tolist()) <= {-1, 0, 100}


def test_add_noise_is_seeded() -> None:
    grid = np.array([[0, 100], [100, -1]], dtype=np.int8)
    first = add_noise(grid, probability=0.5, seed=3)
    second = add_noise(grid, probability=0.5, seed=3)
    np.testing.assert_array_equal(first, second)
    assert first[1, 1] == -1


def test_remove_small_components() -> None:
    grid = np.zeros((4, 4), dtype=np.int8)
    grid[0, 0] = 100
    grid[2:4, 2:4] = 100
    filtered = remove_small_components(grid, min_size=2)
    assert filtered[0, 0] == 0
    assert filtered[2, 2] == 100
