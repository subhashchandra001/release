from __future__ import annotations

import numpy as np
import pytest

from privatemap.io.map_io import (
    MapIOError,
    image_to_occupancy,
    load_occupancy_map,
    save_occupancy_map,
)


def test_load_occupancy_map_from_yaml_and_pgm() -> None:
    occupancy_map = load_occupancy_map("tests/fixtures/simple_map.yaml")
    assert occupancy_map.shape == (4, 4)
    assert occupancy_map.resolution == 0.05
    assert occupancy_map.origin == (1.0, 2.0, 0.0)
    assert occupancy_map.data[0, 0] == 0
    assert occupancy_map.data[0, 2] == 100
    assert occupancy_map.data[1, 1] == -1


def test_save_occupancy_map_roundtrip(tmp_path) -> None:
    occupancy_map = load_occupancy_map("tests/fixtures/simple_map.yaml")
    destination = tmp_path / "roundtrip.yaml"
    save_occupancy_map(occupancy_map, destination)
    loaded = load_occupancy_map(destination)
    np.testing.assert_array_equal(loaded.data, occupancy_map.data)
    assert loaded.origin == occupancy_map.origin


def test_image_to_occupancy_rejects_rgb() -> None:
    with pytest.raises(MapIOError, match="grayscale"):
        image_to_occupancy(np.zeros((2, 2, 3), dtype=np.uint8))
