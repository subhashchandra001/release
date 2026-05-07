"""Simple descriptor matching leakage attack."""

from __future__ import annotations

import numpy as np


class DescriptorAttackError(ValueError):
    """Raised when descriptor attack inputs are invalid."""


def hamming_distance_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    first = np.asarray(a, dtype=np.uint8)
    second = np.asarray(b, dtype=np.uint8)
    if first.ndim != 2 or second.ndim != 2 or first.shape[1] != second.shape[1]:
        raise DescriptorAttackError("Descriptor arrays must be NxD and MxD with the same D")
    xor = np.bitwise_xor(first[:, None, :], second[None, :, :])
    return np.unpackbits(xor, axis=2).sum(axis=2)


def match_descriptors(
    reference: np.ndarray,
    observed: np.ndarray,
    *,
    max_distance: int = 64,
) -> dict[str, float]:
    if max_distance < 0:
        raise DescriptorAttackError("max_distance must be non-negative")
    if len(reference) == 0:
        return {"reference_count": 0.0, "match_count": 0.0, "match_rate": 1.0}
    if len(observed) == 0:
        return {"reference_count": float(len(reference)), "match_count": 0.0, "match_rate": 0.0}
    distances = hamming_distance_matrix(reference, observed)
    nearest = distances.min(axis=1)
    matches = int(np.count_nonzero(nearest <= max_distance))
    return {
        "reference_count": float(len(reference)),
        "match_count": float(matches),
        "match_rate": float(matches / len(reference)),
    }
