"""Room-graph leakage attacks for occupancy maps and reviewed zone annotations."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np

from privatemap.io.map_io import OccupancyMap


class RoomGraphAttackError(ValueError):
    """Raised when room-graph attack inputs are invalid."""


@dataclass(frozen=True)
class RoomGraphAttackResult:
    attack_name: str
    metrics: dict[str, float]


def _occupancy_array(map_or_grid: OccupancyMap | np.ndarray) -> np.ndarray:
    if isinstance(map_or_grid, OccupancyMap):
        array = map_or_grid.data
    else:
        array = np.asarray(map_or_grid)
    if array.ndim != 2:
        raise RoomGraphAttackError("Occupancy input must be a 2-D grid")
    return array


def _bbox_from_polygon(feature: dict) -> tuple[int, int, int, int]:
    coords = feature.get("geometry", {}).get("coordinates", [])
    if not coords or not coords[0]:
        raise RoomGraphAttackError("Room feature must contain polygon coordinates")
    xs = [float(p[0]) for p in coords[0]]
    ys = [float(p[1]) for p in coords[0]]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def load_room_boxes(path: str | Path, environment_id: str | None = None) -> list[dict[str, object]]:
    """Load reviewed room/zone boxes from a GeoJSON FeatureCollection."""

    data = json.loads(Path(path).read_text())
    features = data.get("features", [])
    boxes: list[dict[str, object]] = []
    for feature in features:
        props = feature.get("properties", {})
        if environment_id is not None and props.get("environment_id") != environment_id:
            continue
        xmin, ymin, xmax, ymax = _bbox_from_polygon(feature)
        boxes.append(
            {
                "name": props.get("room_name", f"room_{len(boxes)}"),
                "bbox": (xmin, ymin, xmax, ymax),
            }
        )
    return boxes


def _zone_free_ratio(grid: np.ndarray, bbox: tuple[int, int, int, int]) -> float:
    h, w = grid.shape
    xmin, ymin, xmax, ymax = bbox
    xmin = max(0, min(w - 1, xmin))
    xmax = max(0, min(w, xmax))
    ymin = max(0, min(h - 1, ymin))
    ymax = max(0, min(h, ymax))
    if xmax <= xmin or ymax <= ymin:
        return 0.0
    patch = grid[ymin:ymax, xmin:xmax]
    known = patch != -1
    if not np.any(known):
        return 0.0
    return float(np.logical_and(known, patch == 0).sum() / known.sum())


def _zone_center(bbox: tuple[int, int, int, int]) -> tuple[int, int]:
    xmin, ymin, xmax, ymax = bbox
    return int((xmin + xmax) / 2), int((ymin + ymax) / 2)


def _is_free(grid: np.ndarray, x: int, y: int) -> bool:
    h, w = grid.shape
    return 0 <= x < w and 0 <= y < h and grid[y, x] == 0


def _path_exists(grid: np.ndarray, start: tuple[int, int], goal: tuple[int, int]) -> bool:
    """Grid BFS over free cells. Returns False if centers are blocked/out of bounds."""

    if not _is_free(grid, *start) or not _is_free(grid, *goal):
        return False

    q: deque[tuple[int, int]] = deque([start])
    seen = {start}
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            return True
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in seen and _is_free(grid, nx, ny):
                seen.add((nx, ny))
                q.append((nx, ny))
    return False


def _connectivity_edges(grid: np.ndarray, boxes: list[dict[str, object]]) -> set[tuple[int, int]]:
    centers = [_zone_center(box["bbox"]) for box in boxes]  # type: ignore[index]
    edges: set[tuple[int, int]] = set()
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            if _path_exists(grid, centers[i], centers[j]):
                edges.add((i, j))
    return edges


def _structural_mask(grid: np.ndarray) -> np.ndarray:
    """Lightweight skeleton proxy using occupied/free boundaries.

    This avoids adding heavy dependencies while still measuring recoverable
    structural layout signal.
    """

    occupied = grid == 100
    known = grid != -1
    up = np.roll(occupied, 1, axis=0)
    down = np.roll(occupied, -1, axis=0)
    left = np.roll(occupied, 1, axis=1)
    right = np.roll(occupied, -1, axis=1)
    boundary = occupied & (~(up & down & left & right))
    return boundary & known


def _iou(a: np.ndarray, b: np.ndarray) -> float:
    intersection = int(np.logical_and(a, b).sum())
    union = int(np.logical_or(a, b).sum())
    return float(intersection / union) if union else 1.0


def room_graph_leakage(
    reference: OccupancyMap | np.ndarray,
    released: OccupancyMap | np.ndarray,
    *,
    room_boxes: list[dict[str, object]],
    free_ratio_threshold: float = 0.05,
) -> RoomGraphAttackResult:
    """Measure recovery of room/zone graph structure in a released map."""

    if not room_boxes:
        raise RoomGraphAttackError("room_boxes must contain at least one room/zone")

    reference_grid = _occupancy_array(reference)
    released_grid = _occupancy_array(released)
    if reference_grid.shape != released_grid.shape:
        raise RoomGraphAttackError(
            f"reference and released grids must have same shape: {reference_grid.shape} != {released_grid.shape}"
        )

    ref_active = [
        idx
        for idx, box in enumerate(room_boxes)
        if _zone_free_ratio(reference_grid, box["bbox"]) >= free_ratio_threshold  # type: ignore[index]
    ]
    rel_active = [
        idx
        for idx, box in enumerate(room_boxes)
        if _zone_free_ratio(released_grid, box["bbox"]) >= free_ratio_threshold  # type: ignore[index]
    ]

    ref_nodes = set(ref_active)
    rel_nodes = set(rel_active)
    ref_edges = _connectivity_edges(reference_grid, room_boxes)
    rel_edges = _connectivity_edges(released_grid, room_boxes)

    node_union = len(ref_nodes | rel_nodes)
    edge_union = len(ref_edges | rel_edges)
    node_iou = len(ref_nodes & rel_nodes) / node_union if node_union else 1.0
    edge_iou = len(ref_edges & rel_edges) / edge_union if edge_union else 1.0

    graph_edit_distance = float(len(ref_nodes ^ rel_nodes) + len(ref_edges ^ rel_edges))
    doorway_recall = float(len(ref_edges & rel_edges) / len(ref_edges)) if ref_edges else 1.0
    skeleton_iou = _iou(_structural_mask(reference_grid), _structural_mask(released_grid))

    metrics = {
        "room_node_count": float(len(rel_nodes)),
        "reference_room_node_count": float(len(ref_nodes)),
        "doorway_count": float(len(rel_edges)),
        "reference_doorway_count": float(len(ref_edges)),
        "connectivity_similarity": float(np.mean([node_iou, edge_iou])),
        "graph_edit_distance": graph_edit_distance,
        "doorway_recall": doorway_recall,
        "skeleton_iou": skeleton_iou,
    }
    return RoomGraphAttackResult("room_graph_leakage", metrics)
