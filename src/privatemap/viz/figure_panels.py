"""Helpers for composing simple figure panels."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image


def combine_images_grid(image_paths: list[str | Path], output_path: str | Path, *, columns: int = 2) -> None:
    if not image_paths:
        raise ValueError("No image paths provided")
    if columns <= 0:
        raise ValueError("columns must be positive")
    images = [Image.open(path).convert("RGB") for path in image_paths]
    rows = (len(images) + columns - 1) // columns
    fig, axes = plt.subplots(rows, columns, figsize=(4 * columns, 3 * rows))
    flat_axes = list(getattr(axes, "flat", [axes]))
    for ax, image in zip(flat_axes, images, strict=False):
        ax.imshow(image)
        ax.set_axis_off()
    for ax in flat_axes[len(images) :]:
        ax.set_axis_off()
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(destination, dpi=200)
    plt.close(fig)
