"""Trajectory plotting helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from privatemap.io.trajectory_io import Trajectory


def plot_trajectory(trajectory: Trajectory, path: str | Path, *, title: str = "") -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    xs = [pose.x for pose in trajectory]
    ys = [pose.y for pose in trajectory]
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.plot(xs, ys, marker="o", linewidth=1)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(destination, dpi=200)
    plt.close(fig)
