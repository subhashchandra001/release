"""Small image I/O helpers for keyframe artifacts."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


class ImageIOError(ValueError):
    """Raised when an image cannot be read or written."""


def read_rgb_image(path: str | Path) -> np.ndarray:
    image_path = Path(path)
    if not image_path.exists():
        raise ImageIOError(f"RGB image does not exist: {image_path}")
    try:
        return np.asarray(Image.open(image_path).convert("RGB"), dtype=np.uint8)
    except Exception as exc:
        raise ImageIOError(f"Failed to read RGB image {image_path}: {exc}") from exc


def read_grayscale_image(path: str | Path) -> np.ndarray:
    image_path = Path(path)
    if not image_path.exists():
        raise ImageIOError(f"Image does not exist: {image_path}")
    try:
        return np.asarray(Image.open(image_path).convert("L"), dtype=np.uint8)
    except Exception as exc:
        raise ImageIOError(f"Failed to read image {image_path}: {exc}") from exc


def read_depth_image(path: str | Path) -> np.ndarray:
    image_path = Path(path)
    if not image_path.exists():
        raise ImageIOError(f"Depth image does not exist: {image_path}")
    try:
        return np.asarray(Image.open(image_path))
    except Exception as exc:
        raise ImageIOError(f"Failed to read depth image {image_path}: {exc}") from exc


def write_image(image: np.ndarray, path: str | Path) -> None:
    array = np.asarray(image)
    if array.ndim not in {2, 3}:
        raise ImageIOError("Image must be a 2-D grayscale or 3-D color array")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(array.astype(np.uint8, copy=False)).save(destination)
