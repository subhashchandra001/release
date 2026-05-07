"""Statistical utilities for benchmark result summaries."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from privatemap.metrics.trajectory_metrics import bootstrap_ci


class StatsError(ValueError):
    """Raised when statistical helpers receive invalid inputs."""


def summarize(values: Sequence[float]) -> dict[str, float]:
    """Return count, mean, sample std, min, and max for numeric values."""

    sample = np.asarray(values, dtype=float)
    if sample.ndim != 1 or sample.size == 0:
        raise StatsError("values must be a non-empty 1-D sequence")
    std = float(np.std(sample, ddof=1)) if sample.size > 1 else 0.0
    return {
        "count": float(sample.size),
        "mean": float(np.mean(sample)),
        "std": std,
        "min": float(np.min(sample)),
        "max": float(np.max(sample)),
    }


def mean_ci(
    values: Sequence[float],
    *,
    confidence: float = 0.95,
    n_resamples: int = 1000,
    seed: int | None = None,
) -> dict[str, float]:
    """Return bootstrap mean and percentile confidence interval."""

    mean, low, high = bootstrap_ci(
        values,
        confidence=confidence,
        n_resamples=n_resamples,
        seed=seed,
    )
    return {"mean": mean, "ci_low": low, "ci_high": high}
