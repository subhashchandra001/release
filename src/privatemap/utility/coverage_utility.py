"""Coverage utility helpers for benchmark trajectories."""

from __future__ import annotations

from privatemap.filters.trajectory_filters import coverage_summary
from privatemap.io.trajectory_io import Trajectory


class CoverageUtilityError(ValueError):
    """Raised when coverage utility inputs are invalid."""


def trajectory_coverage(trajectory: Trajectory) -> dict[str, float | int]:
    """Compute simple path and bounding-box coverage metrics."""

    return coverage_summary(trajectory)
