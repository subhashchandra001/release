from __future__ import annotations

import numpy as np
import pytest

from privatemap.artifacts.keyframes import (
    Keyframe,
    make_keyframes,
    read_keyframes_csv,
    write_keyframes_csv,
)
from privatemap.filters.keyframe_filters import Detection, mask_sensitive_objects


def test_keyframe_csv_roundtrip(tmp_path) -> None:
    keyframes = make_keyframes(
        [
            Keyframe("run", "kf0", 1.0, "rgb.png", "", 0, 0, 0, 0, 0, 0, 1, 0),
        ]
    )
    path = tmp_path / "keyframes.csv"
    write_keyframes_csv(keyframes, path)
    loaded = read_keyframes_csv(path)
    assert loaded.by_id()["kf0"].rgb_path == "rgb.png"


def test_keyframe_masking_uses_sensitive_annotations_only() -> None:
    image = np.full((5, 5, 3), 255, dtype=np.uint8)
    detections = [
        Detection("run", "kf0", "rgb.png", "photo", 1.0, 1, 1, 3, 3, None, None, True),
        Detection("run", "kf0", "rgb.png", "chair", 1.0, 3, 3, 5, 5, None, None, False),
    ]
    masked = mask_sensitive_objects(image, detections, fill_value=(0, 0, 0))
    assert masked[1:3, 1:3].sum() == 0
    assert np.all(masked[3:5, 3:5] == 255)


def test_make_keyframes_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one"):
        make_keyframes([])
