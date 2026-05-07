"""ORB descriptor extraction for keyframe images."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from privatemap.io.image_io import read_grayscale_image


class DescriptorError(ValueError):
    """Raised when descriptor extraction fails."""


def _cv2():
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise DescriptorError("OpenCV is required for ORB descriptor extraction") from exc
    return cv2


def extract_orb_descriptors(image: np.ndarray, *, nfeatures: int = 500) -> np.ndarray:
    if nfeatures <= 0:
        raise DescriptorError("nfeatures must be positive")
    array = np.asarray(image)
    if array.ndim == 3:
        cv2 = _cv2()
        array = cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)
    if array.ndim != 2:
        raise DescriptorError("ORB extraction expects a grayscale or RGB image")
    cv2 = _cv2()
    orb = cv2.ORB_create(nfeatures=int(nfeatures))
    _, descriptors = orb.detectAndCompute(array.astype(np.uint8, copy=False), None)
    if descriptors is None:
        return np.empty((0, 32), dtype=np.uint8)
    return descriptors.astype(np.uint8, copy=False)


def extract_orb_descriptors_from_file(path: str | Path, *, nfeatures: int = 500) -> np.ndarray:
    return extract_orb_descriptors(read_grayscale_image(path), nfeatures=nfeatures)


def save_descriptors(path: str | Path, descriptors: np.ndarray) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    np.save(destination, np.asarray(descriptors, dtype=np.uint8))


def load_descriptors(path: str | Path) -> np.ndarray:
    descriptor_path = Path(path)
    if not descriptor_path.exists():
        raise DescriptorError(f"Descriptor file does not exist: {descriptor_path}")
    array = np.load(descriptor_path)
    if array.ndim != 2 or array.shape[1] != 32:
        raise DescriptorError("Descriptor array must have shape Nx32")
    return array.astype(np.uint8, copy=False)
