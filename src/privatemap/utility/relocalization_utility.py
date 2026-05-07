"""Relocalization utility wrappers."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from privatemap.utility.place_recognition import recognize_place, top_k_places


class RelocalizationUtilityError(ValueError):
    """Raised when relocalization inputs are invalid."""


def relocalization_score(
    query_descriptors: np.ndarray,
    database: Mapping[str, np.ndarray],
    *,
    expected_place_id: str | None = None,
    max_distance: int = 64,
) -> dict[str, float | str | None]:
    """Return top place-recognition score and optional correctness flag."""

    place_id, score = recognize_place(
        query_descriptors,
        database,
        max_distance=max_distance,
    )
    result: dict[str, float | str | None] = {
        "predicted_place_id": place_id,
        "match_rate": float(score),
    }
    if expected_place_id is not None:
        result["correct"] = 1.0 if place_id == expected_place_id else 0.0
    return result


def relocalization_top_k(
    query_descriptors: np.ndarray,
    database: Mapping[str, np.ndarray],
    *,
    k: int = 3,
    max_distance: int = 64,
) -> list[tuple[str, float]]:
    """Return ranked place-recognition candidates."""

    return top_k_places(query_descriptors, database, k=k, max_distance=max_distance)
