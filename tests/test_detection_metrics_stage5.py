from __future__ import annotations

import pytest

from privatemap.metrics.detection_metrics import (
    BoundingBox,
    bbox_iou,
    precision_recall_f1_detections,
)


def test_bbox_iou_and_detection_scores() -> None:
    truth = [BoundingBox(0, 0, 10, 10, "screen")]
    predictions = [
        BoundingBox(0, 0, 10, 10, "screen"),
        BoundingBox(20, 20, 30, 30, "screen"),
    ]

    assert bbox_iou(truth[0], predictions[0]) == 1.0
    assert precision_recall_f1_detections(truth, predictions) == {
        "precision": 0.5,
        "recall": 1.0,
        "f1": pytest.approx(2 / 3),
    }


def test_invalid_box_is_rejected() -> None:
    with pytest.raises(ValueError, match="positive area"):
        BoundingBox(1, 1, 1, 2)
