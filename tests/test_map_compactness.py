from __future__ import annotations

import numpy as np
import pytest

from privatemap.utility.map_compactness import compactness_metrics


def test_compactness_metrics_for_square_component() -> None:
    grid = np.array(
        [
            [0, 0, 0, 0],
            [0, 100, 100, 0],
            [0, 100, 100, 0],
            [0, 0, 0, 0],
        ],
        dtype=np.int8,
    )

    metrics = compactness_metrics(grid)

    assert metrics["area_cells"] == 4.0
    assert metrics["perimeter_edges"] == 8.0
    assert metrics["component_count"] == 1.0
    assert metrics["largest_component_fraction"] == 1.0
    assert metrics["bbox_fill_ratio"] == 1.0
    assert metrics["compactness"] == pytest.approx(np.pi / 4)


def test_compactness_metrics_for_empty_target() -> None:
    metrics = compactness_metrics(np.zeros((2, 2), dtype=np.int8))

    assert metrics["area_cells"] == 0.0
    assert metrics["compactness"] == 0.0
