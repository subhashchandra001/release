"""Semantic annotation artifact helpers."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from privatemap.filters.keyframe_filters import Detection, read_detections_csv


class SemanticsArtifactError(ValueError):
    """Raised when semantic annotations are missing or invalid."""


def read_semantic_detections(path: str | Path) -> list[Detection]:
    """Read detections using the benchmark annotation schema."""

    return read_detections_csv(path)


def sensitive_class_names(detections: Iterable[Detection]) -> set[str]:
    """Return lower-case class names marked sensitive in detections."""

    return {detection.class_name.lower() for detection in detections if detection.is_sensitive}


def export_from_detector(*_args: object, **_kwargs: object) -> None:
    """Fail clearly until detector integration is implemented."""

    raise NotImplementedError(
        "Detector integration is not implemented. Create or review "
        "detections.csv manually using docs/annotation_guide.md."
    )
