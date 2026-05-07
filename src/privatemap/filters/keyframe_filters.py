"""Keyframe privacy filters driven by manual sensitive-object annotations."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from privatemap.io.image_io import read_rgb_image, write_image


class KeyframeFilterError(ValueError):
    """Raised when keyframe filtering inputs are malformed."""


DETECTION_COLUMNS = [
    "run_id",
    "keyframe_id",
    "image_path",
    "class_name",
    "confidence",
    "xmin",
    "ymin",
    "xmax",
    "ymax",
    "map_x",
    "map_y",
    "is_sensitive",
]


@dataclass(frozen=True)
class Detection:
    run_id: str
    keyframe_id: str
    image_path: str
    class_name: str
    confidence: float
    xmin: int
    ymin: int
    xmax: int
    ymax: int
    map_x: float | None = None
    map_y: float | None = None
    is_sensitive: bool = False


def _parse_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _optional_float(value: object) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    return float(value)


def read_detections_csv(path: str | Path) -> list[Detection]:
    csv_path = Path(path)
    if not csv_path.exists():
        raise KeyframeFilterError(f"Detections CSV does not exist: {csv_path}")
    detections: list[Detection] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise KeyframeFilterError(f"Detections CSV is empty: {csv_path}")
        missing = [column for column in DETECTION_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise KeyframeFilterError(f"Detections CSV missing column(s): {missing}")
        for row_number, row in enumerate(reader, start=2):
            try:
                detections.append(
                    Detection(
                        run_id=str(row["run_id"]),
                        keyframe_id=str(row["keyframe_id"]),
                        image_path=str(row["image_path"]),
                        class_name=str(row["class_name"]),
                        confidence=float(row["confidence"]),
                        xmin=int(float(row["xmin"])),
                        ymin=int(float(row["ymin"])),
                        xmax=int(float(row["xmax"])),
                        ymax=int(float(row["ymax"])),
                        map_x=_optional_float(row.get("map_x")),
                        map_y=_optional_float(row.get("map_y")),
                        is_sensitive=_parse_bool(row["is_sensitive"]),
                    )
                )
            except (TypeError, ValueError) as exc:
                raise KeyframeFilterError(
                    f"Detections CSV {csv_path} row {row_number} is malformed"
                ) from exc
    if not detections:
        raise KeyframeFilterError(f"Detections CSV contains no rows: {csv_path}")
    return detections


def sensitive_detections(detections: Iterable[Detection]) -> list[Detection]:
    return [detection for detection in detections if detection.is_sensitive]


def mask_regions(
    image: np.ndarray,
    detections: Iterable[Detection],
    *,
    fill_value: int | tuple[int, int, int] = 0,
) -> np.ndarray:
    array = np.asarray(image)
    if array.ndim not in {2, 3}:
        raise KeyframeFilterError("Image must be a 2-D or 3-D array")
    output = array.copy()
    height, width = output.shape[:2]
    for detection in detections:
        xmin = max(0, min(width, detection.xmin))
        xmax = max(0, min(width, detection.xmax))
        ymin = max(0, min(height, detection.ymin))
        ymax = max(0, min(height, detection.ymax))
        if xmax <= xmin or ymax <= ymin:
            continue
        output[ymin:ymax, xmin:xmax] = fill_value
    return output


def mask_sensitive_objects(
    image: np.ndarray,
    detections: Iterable[Detection],
    *,
    fill_value: int | tuple[int, int, int] = 0,
) -> np.ndarray:
    return mask_regions(image, sensitive_detections(detections), fill_value=fill_value)


def mask_keyframe_file(
    image_path: str | Path,
    detections: Iterable[Detection],
    output_path: str | Path,
    *,
    fill_value: int | tuple[int, int, int] = 0,
) -> None:
    image = read_rgb_image(image_path)
    masked = mask_sensitive_objects(image, detections, fill_value=fill_value)
    write_image(masked, output_path)
