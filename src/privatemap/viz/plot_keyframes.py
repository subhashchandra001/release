"""Keyframe visualization helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from privatemap.filters.keyframe_filters import Detection


def plot_keyframe_with_boxes(
    image: np.ndarray,
    detections: list[Detection],
    path: str | Path,
    *,
    title: str = "",
) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.imshow(image)
    for detection in detections:
        color = "red" if detection.is_sensitive else "yellow"
        rect = plt.Rectangle(
            (detection.xmin, detection.ymin),
            detection.xmax - detection.xmin,
            detection.ymax - detection.ymin,
            fill=False,
            edgecolor=color,
            linewidth=1.5,
        )
        ax.add_patch(rect)
    ax.set_axis_off()
    if title:
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(destination, dpi=200)
    plt.close(fig)
