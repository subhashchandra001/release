from __future__ import annotations

import numpy as np

from privatemap.attacks.object_leakage_attack import class_leakage_counts, sensitive_object_recall
from privatemap.filters.keyframe_filters import Detection
from privatemap.filters.semantic_filters import redact_classes


def _det(cls: str, sensitive: bool, box=(1, 1, 4, 4)) -> Detection:
    return Detection("run", "kf0", "rgb.png", cls, 1.0, *box, None, None, sensitive)


def test_semantic_redaction_masks_requested_sensitive_class() -> None:
    image = np.full((6, 6, 3), 200, dtype=np.uint8)
    redacted = redact_classes(image, [_det("screen", True)], ["screen"], fill_value=(5, 5, 5))
    assert np.all(redacted[1:4, 1:4] == 5)
    assert np.all(redacted[0, 0] == 200)


def test_object_leakage_recall_matches_boxes() -> None:
    truth = [_det("screen", True)]
    observed = [_det("screen", False, box=(1, 1, 4, 4))]
    metrics = sensitive_object_recall(truth, observed)
    assert metrics["recall"] == 1.0
    assert class_leakage_counts(truth) == {"screen": 1}
