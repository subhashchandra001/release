"""Place-recognition utility based on descriptor matching."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from privatemap.attacks.descriptor_attack import match_descriptors


def recognize_place(
    query_descriptors: np.ndarray,
    database: Mapping[str, np.ndarray],
    *,
    max_distance: int = 64,
) -> tuple[str | None, float]:
    if not database:
        raise ValueError("Place-recognition database is empty")
    best_id: str | None = None
    best_score = -1.0
    for place_id, descriptors in database.items():
        score = match_descriptors(
            descriptors,
            query_descriptors,
            max_distance=max_distance,
        )["match_rate"]
        if score > best_score:
            best_id = place_id
            best_score = score
    return best_id, float(best_score)


def top_k_places(
    query_descriptors: np.ndarray,
    database: Mapping[str, np.ndarray],
    *,
    k: int = 3,
    max_distance: int = 64,
) -> list[tuple[str, float]]:
    if k <= 0:
        raise ValueError("k must be positive")
    scored = [
        (
            place_id,
            match_descriptors(
                descriptors,
                query_descriptors,
                max_distance=max_distance,
            )["match_rate"],
        )
        for place_id, descriptors in database.items()
    ]
    return sorted(scored, key=lambda item: item[1], reverse=True)[:k]
