"""Detection metrics for manually reviewed object annotations."""

from __future__ import annotations

from dataclasses import dataclass


class DetectionMetricError(ValueError):
    """Raised when detection metric inputs are invalid."""


@dataclass(frozen=True)
class BoundingBox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    class_name: str = ""

    def __post_init__(self) -> None:
        if self.xmax <= self.xmin or self.ymax <= self.ymin:
            raise DetectionMetricError("Bounding boxes must have positive area")


def bbox_iou(a: BoundingBox, b: BoundingBox) -> float:
    """Compute intersection-over-union for two bounding boxes."""

    ixmin = max(a.xmin, b.xmin)
    iymin = max(a.ymin, b.ymin)
    ixmax = min(a.xmax, b.xmax)
    iymax = min(a.ymax, b.ymax)
    intersection = max(0.0, ixmax - ixmin) * max(0.0, iymax - iymin)
    area_a = (a.xmax - a.xmin) * (a.ymax - a.ymin)
    area_b = (b.xmax - b.xmin) * (b.ymax - b.ymin)
    union = area_a + area_b - intersection
    return float(intersection / union) if union else 0.0


def precision_recall_f1_detections(
    truth: list[BoundingBox],
    predictions: list[BoundingBox],
    *,
    iou_threshold: float = 0.5,
    match_classes: bool = True,
) -> dict[str, float]:
    """Greedily match predictions to truth boxes and report PR/F1."""

    if not 0 < iou_threshold <= 1:
        raise DetectionMetricError("iou_threshold must be in (0, 1]")
    matched_truth: set[int] = set()
    true_positive = 0
    for prediction in predictions:
        best_index = None
        best_iou = 0.0
        for index, target in enumerate(truth):
            if index in matched_truth:
                continue
            if match_classes and prediction.class_name != target.class_name:
                continue
            score = bbox_iou(prediction, target)
            if score > best_iou:
                best_index = index
                best_iou = score
        if best_index is not None and best_iou >= iou_threshold:
            matched_truth.add(best_index)
            true_positive += 1

    false_positive = len(predictions) - true_positive
    false_negative = len(truth) - true_positive
    precision = true_positive / (true_positive + false_positive) if predictions else 1.0
    recall = true_positive / (true_positive + false_negative) if truth else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": float(precision), "recall": float(recall), "f1": float(f1)}
