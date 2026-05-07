"""Map plotting helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def plot_occupancy_grid(grid: np.ndarray, path: str | Path, *, title: str = "") -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    display = np.asarray(grid)
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(display, cmap="gray_r", interpolation="nearest")
    ax.set_axis_off()
    if title:
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(destination, dpi=200)
    plt.close(fig)
