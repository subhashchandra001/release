from __future__ import annotations

import importlib.util

import numpy as np
import pytest

from privatemap.attacks.descriptor_attack import match_descriptors
from privatemap.artifacts.descriptors import extract_orb_descriptors
from privatemap.filters.descriptor_filters import randomize_descriptors, subsample_descriptors


def test_descriptor_randomization_and_matching() -> None:
    descriptors = np.zeros((4, 32), dtype=np.uint8)
    randomized = randomize_descriptors(descriptors, bit_flip_probability=1.0, seed=1)
    assert np.all(randomized == 255)
    metrics = match_descriptors(descriptors, descriptors, max_distance=0)
    assert metrics["match_rate"] == 1.0
    assert len(subsample_descriptors(descriptors, 0.5, seed=1)) == 2


@pytest.mark.skipif(importlib.util.find_spec("cv2") is None, reason="OpenCV unavailable")
def test_orb_descriptor_extraction_returns_orb_width() -> None:
    image = np.zeros((80, 80), dtype=np.uint8)
    image[20:60, 20:60] = 255
    descriptors = extract_orb_descriptors(image, nfeatures=50)
    assert descriptors.shape[1] == 32
