"""Trajectory metrics."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np

from privatemap.io.trajectory_io import Trajectory, validate_trajectory


class TrajectoryMetricError(ValueError):
    """Raised when trajectory metrics receive invalid inputs."""


def trajectory_rmse(
    reference: Trajectory,
    estimate: Trajectory,
    *,
    columns: Sequence[str] = ("x", "y"),
) -> float:
    """Compute pose RMSE over matching row order."""

    validate_trajectory(reference)
    validate_trajectory(estimate)
    if len(reference) != len(estimate):
        raise TrajectoryMetricError("reference and estimate must have the same number of poses")
    ref = np.array(reference.numeric_matrix(columns), dtype=float)
    est = np.array(estimate.numeric_matrix(columns), dtype=float)
    return float(np.sqrt(np.mean(np.sum((ref - est) ** 2, axis=1))))


def edit_distance(a: Sequence[object], b: Sequence[object]) -> int:
    """Compute Levenshtein edit distance between two sequences."""

    rows = len(a) + 1
    cols = len(b) + 1
    dp = np.zeros((rows, cols), dtype=int)
    dp[:, 0] = np.arange(rows)
    dp[0, :] = np.arange(cols)
    for i in range(1, rows):
        for j in range(1, cols):
            substitution = 0 if a[i - 1] == b[j - 1] else 1
            dp[i, j] = min(
                dp[i - 1, j] + 1,
                dp[i, j - 1] + 1,
                dp[i - 1, j - 1] + substitution,
            )
    return int(dp[-1, -1])


def bootstrap_ci(
    values: Sequence[float],
    statistic: Callable[[np.ndarray], float] | None = None,
    *,
    confidence: float = 0.95,
    n_resamples: int = 1000,
    seed: int | None = None,
) -> tuple[float, float, float]:
    """Return statistic and percentile bootstrap confidence interval."""

    sample = np.asarray(values, dtype=float)
    if sample.ndim != 1 or sample.size == 0:
        raise TrajectoryMetricError("values must be a non-empty 1-D sequence")
    if not 0 < confidence < 1:
        raise TrajectoryMetricError("confidence must be in (0, 1)")
    if n_resamples <= 0:
        raise TrajectoryMetricError("n_resamples must be positive")

    stat = statistic or (lambda array: float(np.mean(array)))
    rng = np.random.default_rng(seed)
    estimates = np.empty(n_resamples, dtype=float)
    for index in range(n_resamples):
        resample = rng.choice(sample, size=sample.size, replace=True)
        estimates[index] = stat(resample)
    alpha = 1.0 - confidence
    low, high = np.quantile(estimates, [alpha / 2.0, 1.0 - alpha / 2.0])
    return float(stat(sample)), float(low), float(high)
