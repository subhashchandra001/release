"""Dispatch helpers for configured privacy filters."""

from __future__ import annotations

from typing import Any

from privatemap.filters import occupancy_filters, trajectory_filters
from privatemap.io.map_io import OccupancyMap
from privatemap.io.trajectory_io import Trajectory


class CombinedFilterError(ValueError):
    """Raised when a configured filter name or parameter set is invalid."""


def apply_occupancy_filter(
    map_data: OccupancyMap,
    name: str,
    params: dict[str, Any] | None = None,
) -> OccupancyMap:
    """Apply one named occupancy filter and preserve map metadata."""

    params = params or {}
    if name == "downsample":
        data = occupancy_filters.downsample(map_data.data, int(params["factor"]))
    elif name == "blur":
        data = occupancy_filters.blur(map_data.data, float(params["sigma"]))
    elif name == "noise":
        data = occupancy_filters.add_noise(
            map_data.data,
            float(params["probability"]),
            seed=params.get("seed"),
        )
    elif name == "remove_small_components":
        data = occupancy_filters.remove_small_components(
            map_data.data,
            int(params["min_size"]),
        )
    else:
        raise CombinedFilterError(f"Unknown occupancy filter: {name}")
    return OccupancyMap(
        data=data,
        resolution=map_data.resolution,
        origin=map_data.origin,
        negate=map_data.negate,
        occupied_thresh=map_data.occupied_thresh,
        free_thresh=map_data.free_thresh,
        image=map_data.image,
    )


def apply_trajectory_filter(
    trajectory: Trajectory,
    name: str,
    params: dict[str, Any] | None = None,
) -> Trajectory | list[str] | dict[str, float | int]:
    """Apply one named trajectory filter or summary operation."""

    params = params or {}
    if name == "downsample":
        return trajectory_filters.downsample(trajectory, int(params["step"]))
    if name == "spatial_quantize":
        return trajectory_filters.spatial_quantize(trajectory, float(params["grid_size"]))
    if name == "room_sequence":
        return trajectory_filters.room_sequence(trajectory, params.get("rooms", []))
    if name == "coverage_summary":
        return trajectory_filters.coverage_summary(trajectory)
    raise CombinedFilterError(f"Unknown trajectory filter: {name}")
