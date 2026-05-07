"""Paper figure generation from existing result artifacts."""

from __future__ import annotations

from pathlib import Path

from privatemap.viz.plot_privacy_utility import plot_metric_bars


def write_result_summary_figure(records: list[dict], path: str | Path, *, title: str = "") -> None:
    plot_metric_bars(records, path, title=title)
