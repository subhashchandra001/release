"""Plots for privacy and utility result tables."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def plot_metric_bars(records: list[dict], path: str | Path, *, title: str = "") -> None:
    if not records:
        raise ValueError("No records provided for plotting")
    labels = [
        str(record.get("filter_name") or record.get("utility_name") or record.get("metric_name"))
        for record in records
    ]
    values = [float(record.get("mean", record.get("value", 0.0))) for record in records]
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(4, len(labels) * 0.8), 3))
    ax.bar(labels, values, color="#4c78a8")
    ax.set_ylabel("Value")
    if title:
        ax.set_title(title)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(destination, dpi=200)
    plt.close(fig)
