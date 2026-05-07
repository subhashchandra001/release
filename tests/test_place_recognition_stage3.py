from __future__ import annotations

import numpy as np

from privatemap.utility.place_recognition import recognize_place, top_k_places


def test_place_recognition_selects_best_descriptor_match() -> None:
    query = np.zeros((2, 32), dtype=np.uint8)
    database = {
        "near": np.zeros((2, 32), dtype=np.uint8),
        "far": np.full((2, 32), 255, dtype=np.uint8),
    }
    place_id, score = recognize_place(query, database, max_distance=0)
    assert place_id == "near"
    assert score == 1.0
    assert top_k_places(query, database, k=1, max_distance=0)[0][0] == "near"
