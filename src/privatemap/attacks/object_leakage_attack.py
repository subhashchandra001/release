"""Object leakage attack based on manual object annotations."""

from __future__ import annotations

from collections.abc import Iterable

from privatemap.filters.keyframe_filters import Detection


def sensitive_object_recall(
    ground_truth: Iterable[Detection],
    observed: Iterable[Detection],
    *,
    iou_threshold: float = 0.5,
) -> dict[str, float]:
    """Measure how many sensitive annotated objects remain observable."""

    truth = [d for d in ground_truth if d.is_sensitive]
    candidates = list(observed)
    if not truth:
        return {"sensitive_count": 0.0, "matched_count": 0.0, "recall": 1.0}
    matched = 0
    for target in truth:
        if any(
            target.keyframe_id == candidate.keyframe_id
            and target.class_name == candidate.class_name
            and bbox_iou(target, candidate) >= iou_threshold
            for candidate in candidates
        ):
            matched += 1
    return {
        "sensitive_count": float(len(truth)),
        "matched_count": float(matched),
        "recall": float(matched / len(truth)),
    }


def class_leakage_counts(detections: Iterable[Detection]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for detection in detections:
        if detection.is_sensitive:
            counts[detection.class_name] = counts.get(detection.class_name, 0) + 1
    return counts


def bbox_iou(a: Detection, b: Detection) -> float:
    x0 = max(a.xmin, b.xmin)
    y0 = max(a.ymin, b.ymin)
    x1 = min(a.xmax, b.xmax)
    y1 = min(a.ymax, b.ymax)
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    area_a = max(0, a.xmax - a.xmin) * max(0, a.ymax - a.ymin)
    area_b = max(0, b.xmax - b.xmin) * max(0, b.ymax - b.ymin)
    union = area_a + area_b - inter
    return float(inter / union) if union else 0.0
