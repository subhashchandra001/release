"""A* navigation utility on occupancy grids."""

from __future__ import annotations

import heapq
from collections.abc import Iterable
from dataclasses import dataclass
from math import hypot

import numpy as np

from privatemap.io.map_io import OccupancyMap


GridCell = tuple[int, int]


class NavigationUtilityError(ValueError):
    """Raised when navigation planning inputs are invalid."""


@dataclass(frozen=True)
class NavigationPlan:
    path: tuple[GridCell, ...]
    cost: float
    expanded_nodes: int

    @property
    def success(self) -> bool:
        return bool(self.path)


def _grid(map_or_grid: OccupancyMap | np.ndarray) -> np.ndarray:
    array = map_or_grid.data if isinstance(map_or_grid, OccupancyMap) else np.asarray(map_or_grid)
    if array.ndim != 2:
        raise NavigationUtilityError("Occupancy grid must be 2-D")
    invalid = set(np.unique(array).tolist()) - {-1, 0, 100}
    if invalid:
        raise NavigationUtilityError(f"Occupancy grid contains invalid labels: {sorted(invalid)}")
    return array


def traversable_mask(
    map_or_grid: OccupancyMap | np.ndarray,
    *,
    obstacle_threshold: int = 50,
    allow_unknown: bool = False,
) -> np.ndarray:
    """Return a boolean mask of cells that A* may traverse."""

    array = _grid(map_or_grid)
    if obstacle_threshold <= 0:
        raise NavigationUtilityError("obstacle_threshold must be positive")
    traversable = (array >= 0) & (array < obstacle_threshold)
    if allow_unknown:
        traversable = traversable | (array == -1)
    return traversable


def _validate_cell(cell: GridCell, shape: tuple[int, int], *, name: str) -> GridCell:
    row, col = int(cell[0]), int(cell[1])
    if not (0 <= row < shape[0] and 0 <= col < shape[1]):
        raise NavigationUtilityError(f"{name} cell {cell} is outside grid shape {shape}")
    return row, col


def _neighbors(cell: GridCell, *, diagonal: bool) -> Iterable[tuple[GridCell, float]]:
    row, col = cell
    steps = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0)]
    if diagonal:
        root2 = 2.0**0.5
        steps.extend([(-1, -1, root2), (-1, 1, root2), (1, -1, root2), (1, 1, root2)])
    for dr, dc, cost in steps:
        yield (row + dr, col + dc), cost


def astar_plan(
    map_or_grid: OccupancyMap | np.ndarray,
    start: GridCell,
    goal: GridCell,
    *,
    obstacle_threshold: int = 50,
    allow_unknown: bool = False,
    diagonal: bool = False,
) -> NavigationPlan:
    """Plan a path between grid cells using A*.

    Cells are addressed as ``(row, column)``. Occupied cells and unknown cells
    are blocked by default.
    """

    free = traversable_mask(
        map_or_grid,
        obstacle_threshold=obstacle_threshold,
        allow_unknown=allow_unknown,
    )
    start = _validate_cell(start, free.shape, name="start")
    goal = _validate_cell(goal, free.shape, name="goal")
    if not free[start]:
        raise NavigationUtilityError(f"start cell {start} is not traversable")
    if not free[goal]:
        raise NavigationUtilityError(f"goal cell {goal} is not traversable")

    frontier: list[tuple[float, int, GridCell]] = [(0.0, 0, start)]
    came_from: dict[GridCell, GridCell | None] = {start: None}
    cost_so_far: dict[GridCell, float] = {start: 0.0}
    counter = 1
    expanded = 0

    while frontier:
        _, _, current = heapq.heappop(frontier)
        expanded += 1
        if current == goal:
            break
        for neighbor, step_cost in _neighbors(current, diagonal=diagonal):
            row, col = neighbor
            if not (0 <= row < free.shape[0] and 0 <= col < free.shape[1]):
                continue
            if not free[neighbor]:
                continue
            new_cost = cost_so_far[current] + step_cost
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + hypot(goal[0] - row, goal[1] - col)
                heapq.heappush(frontier, (priority, counter, neighbor))
                counter += 1
                came_from[neighbor] = current

    if goal not in came_from:
        return NavigationPlan(path=(), cost=float("inf"), expanded_nodes=expanded)

    path: list[GridCell] = []
    current: GridCell | None = goal
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return NavigationPlan(tuple(path), float(cost_so_far[goal]), expanded)


def world_to_grid(map_data: OccupancyMap, x: float, y: float) -> GridCell:
    """Convert map-frame world coordinates to nearest grid cell."""

    col = int(round((x - map_data.origin[0]) / map_data.resolution))
    row_from_bottom = int(round((y - map_data.origin[1]) / map_data.resolution))
    row = map_data.data.shape[0] - 1 - row_from_bottom
    return row, col
