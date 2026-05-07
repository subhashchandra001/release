"""Occupancy map I/O for ROS-style ``.yaml`` + ``.pgm`` maps."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image


class MapIOError(ValueError):
    """Raised when an occupancy map cannot be read or written."""


@dataclass(frozen=True)
class OccupancyMap:
    """A ROS occupancy grid represented as int8 values.

    ``data`` uses ``0`` for free, ``100`` for occupied, and ``-1`` for unknown.
    """

    data: np.ndarray
    resolution: float
    origin: tuple[float, float, float]
    negate: int = 0
    occupied_thresh: float = 0.65
    free_thresh: float = 0.196
    image: str | None = None

    def __post_init__(self) -> None:
        array = np.asarray(self.data)
        if array.ndim != 2:
            raise MapIOError("OccupancyMap.data must be a 2-D array")
        if not np.issubdtype(array.dtype, np.integer):
            raise MapIOError("OccupancyMap.data must contain integer occupancy labels")
        invalid = set(np.unique(array).tolist()) - {-1, 0, 100}
        if invalid:
            raise MapIOError(f"OccupancyMap.data contains invalid labels: {sorted(invalid)}")
        if self.resolution <= 0:
            raise MapIOError("OccupancyMap.resolution must be positive")
        if len(self.origin) != 3:
            raise MapIOError("OccupancyMap.origin must contain x, y, yaw")

    @property
    def shape(self) -> tuple[int, int]:
        return self.data.shape


def load_map_yaml(path: str | Path) -> dict[str, Any]:
    yaml_path = Path(path)
    if not yaml_path.exists():
        raise MapIOError(f"Map YAML does not exist: {yaml_path}")
    try:
        with yaml_path.open("r", encoding="utf-8") as handle:
            metadata = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise MapIOError(f"Failed to parse map YAML {yaml_path}: {exc}") from exc
    if not isinstance(metadata, dict):
        raise MapIOError(f"Map YAML must contain a mapping: {yaml_path}")
    required = {"image", "resolution", "origin", "occupied_thresh", "free_thresh"}
    missing = required - set(metadata)
    if missing:
        raise MapIOError(f"Map YAML {yaml_path} missing required key(s): {sorted(missing)}")
    return metadata


def load_occupancy_map(path: str | Path) -> OccupancyMap:
    """Load a ROS map-server style occupancy map from YAML and PGM."""

    yaml_path = Path(path)
    metadata = load_map_yaml(yaml_path)
    image_path = Path(metadata["image"])
    if not image_path.is_absolute():
        image_path = yaml_path.parent / image_path
    if not image_path.exists():
        raise MapIOError(f"Map image does not exist: {image_path}")

    try:
        image = Image.open(image_path).convert("L")
        pixels = np.asarray(image, dtype=np.uint8)
    except Exception as exc:  # Pillow raises several concrete exception types.
        raise MapIOError(f"Failed to read map image {image_path}: {exc}") from exc

    try:
        resolution = float(metadata["resolution"])
        origin_raw = metadata["origin"]
        origin = tuple(float(value) for value in origin_raw)
        negate = int(metadata.get("negate", 0))
        occupied_thresh = float(metadata["occupied_thresh"])
        free_thresh = float(metadata["free_thresh"])
    except (TypeError, ValueError) as exc:
        raise MapIOError(f"Map YAML {yaml_path} contains invalid numeric metadata") from exc

    if len(origin) != 3:
        raise MapIOError(f"Map YAML {yaml_path}: origin must contain three values")

    data = image_to_occupancy(
        pixels,
        negate=negate,
        occupied_thresh=occupied_thresh,
        free_thresh=free_thresh,
    )
    return OccupancyMap(
        data=data,
        resolution=resolution,
        origin=origin,
        negate=negate,
        occupied_thresh=occupied_thresh,
        free_thresh=free_thresh,
        image=str(metadata["image"]),
    )


def image_to_occupancy(
    pixels: np.ndarray,
    *,
    negate: int = 0,
    occupied_thresh: float = 0.65,
    free_thresh: float = 0.196,
) -> np.ndarray:
    """Convert grayscale ROS map pixels to occupancy labels."""

    if pixels.ndim != 2:
        raise MapIOError("PGM image must be grayscale")
    normalized = pixels.astype(float) / 255.0
    occupancy_probability = normalized if negate else 1.0 - normalized
    data = np.full(pixels.shape, -1, dtype=np.int8)
    data[occupancy_probability >= occupied_thresh] = 100
    data[occupancy_probability <= free_thresh] = 0
    return data


def occupancy_to_image(data: np.ndarray) -> np.ndarray:
    """Convert occupancy labels to ROS-compatible grayscale pixels."""

    array = np.asarray(data)
    invalid = set(np.unique(array).tolist()) - {-1, 0, 100}
    if invalid:
        raise MapIOError(f"Cannot convert invalid occupancy labels: {sorted(invalid)}")
    image = np.full(array.shape, 205, dtype=np.uint8)
    image[array == 0] = 254
    image[array == 100] = 0
    return image


def save_occupancy_map(map_data: OccupancyMap, yaml_path: str | Path) -> None:
    """Write an occupancy map as ``.yaml`` plus adjacent ``.pgm`` image."""

    destination = Path(yaml_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image_name = destination.with_suffix(".pgm").name
    image_path = destination.with_name(image_name)
    Image.fromarray(occupancy_to_image(map_data.data), mode="L").save(image_path)
    metadata = {
        "image": image_name,
        "resolution": float(map_data.resolution),
        "origin": [float(value) for value in map_data.origin],
        "negate": int(map_data.negate),
        "occupied_thresh": float(map_data.occupied_thresh),
        "free_thresh": float(map_data.free_thresh),
    }
    with destination.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(metadata, handle, sort_keys=False)
