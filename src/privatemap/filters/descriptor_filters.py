"""Descriptor privacy filters."""

from __future__ import annotations

import numpy as np


class DescriptorFilterError(ValueError):
    """Raised when descriptor filters receive invalid input."""


def _descriptors(descriptors: np.ndarray) -> np.ndarray:
    array = np.asarray(descriptors)
    if array.ndim != 2 or array.shape[1] != 32:
        raise DescriptorFilterError("ORB descriptors must have shape Nx32")
    return array.astype(np.uint8, copy=False)


def randomize_descriptors(
    descriptors: np.ndarray,
    *,
    bit_flip_probability: float = 0.1,
    seed: int | None = None,
) -> np.ndarray:
    if not 0 <= bit_flip_probability <= 1:
        raise DescriptorFilterError("bit_flip_probability must be in [0, 1]")
    array = _descriptors(descriptors)
    rng = np.random.default_rng(seed)
    bits = np.unpackbits(array, axis=1)
    flips = rng.random(bits.shape) < bit_flip_probability
    randomized = np.bitwise_xor(bits, flips.astype(np.uint8))
    return np.packbits(randomized, axis=1).astype(np.uint8)


def subsample_descriptors(
    descriptors: np.ndarray,
    keep_fraction: float,
    *,
    seed: int | None = None,
) -> np.ndarray:
    if not 0 < keep_fraction <= 1:
        raise DescriptorFilterError("keep_fraction must be in (0, 1]")
    array = _descriptors(descriptors)
    if len(array) == 0:
        return array.copy()
    rng = np.random.default_rng(seed)
    keep = max(1, int(round(len(array) * keep_fraction)))
    indices = np.sort(rng.choice(len(array), size=keep, replace=False))
    return array[indices].copy()
