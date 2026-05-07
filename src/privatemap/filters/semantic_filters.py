"""Semantic redaction helpers for annotated object classes."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from privatemap.filters.keyframe_filters import Detection, mask_regions


def redact_classes(
    image: np.ndarray,
    detections: Iterable[Detection],
    classes: Iterable[str],
    *,
    fill_value: int | tuple[int, int, int] = 0,
    sensitive_only: bool = True,
) -> np.ndarray:
    """Redact bounding boxes whose class names match ``classes``.

    Manual annotations are the default source for detections. Optional detector
    integrations should write the same detection schema before using this
    function.
    """

    wanted = {name.lower() for name in classes}
    selected = [
        detection
        for detection in detections
        if detection.class_name.lower() in wanted
        and (detection.is_sensitive or not sensitive_only)
    ]
    return mask_regions(image, selected, fill_value=fill_value)


def redact_sensitive_objects(
    image: np.ndarray,
    detections: Iterable[Detection],
    *,
    fill_value: int | tuple[int, int, int] = 0,
) -> np.ndarray:
    return mask_regions(image, [d for d in detections if d.is_sensitive], fill_value=fill_value)
