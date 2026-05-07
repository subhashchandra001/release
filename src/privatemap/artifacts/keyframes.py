"""Keyframe CSV support."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class KeyframeIOError(ValueError):
    """Raised when keyframe CSV data are missing or malformed."""


KEYFRAME_COLUMNS = [
    "run_id",
    "keyframe_id",
    "timestamp",
    "rgb_path",
    "depth_path",
    "x",
    "y",
    "z",
    "qx",
    "qy",
    "qz",
    "qw",
    "yaw",
]
NUMERIC_KEYFRAME_COLUMNS = ["timestamp", "x", "y", "z", "qx", "qy", "qz", "qw", "yaw"]


@dataclass(frozen=True)
class Keyframe:
    run_id: str
    keyframe_id: str
    timestamp: float
    rgb_path: str
    depth_path: str
    x: float
    y: float
    z: float
    qx: float
    qy: float
    qz: float
    qw: float
    yaw: float

    def to_row(self) -> dict[str, str | float]:
        return {column: getattr(self, column) for column in KEYFRAME_COLUMNS}


@dataclass(frozen=True)
class KeyframeSet:
    keyframes: tuple[Keyframe, ...]

    def __post_init__(self) -> None:
        if not self.keyframes:
            raise KeyframeIOError("KeyframeSet must contain at least one row")

    def __iter__(self) -> Iterator[Keyframe]:
        return iter(self.keyframes)

    def __len__(self) -> int:
        return len(self.keyframes)

    def by_id(self) -> dict[str, Keyframe]:
        return {frame.keyframe_id: frame for frame in self.keyframes}

    def to_rows(self) -> list[dict[str, str | float]]:
        return [frame.to_row() for frame in self.keyframes]


def _parse_keyframe(row: dict[str, Any], *, row_number: int) -> Keyframe:
    missing = [column for column in KEYFRAME_COLUMNS if column not in row]
    if missing:
        raise KeyframeIOError(f"Keyframe row {row_number} missing column(s): {missing}")
    for column in ["run_id", "keyframe_id", "rgb_path"]:
        if not str(row[column]):
            raise KeyframeIOError(f"Keyframe row {row_number}: {column} must be non-empty")
    try:
        numeric = {column: float(row[column]) for column in NUMERIC_KEYFRAME_COLUMNS}
    except (TypeError, ValueError) as exc:
        raise KeyframeIOError(f"Keyframe row {row_number} contains non-numeric values") from exc
    return Keyframe(
        run_id=str(row["run_id"]),
        keyframe_id=str(row["keyframe_id"]),
        rgb_path=str(row["rgb_path"]),
        depth_path=str(row.get("depth_path", "")),
        **numeric,
    )


def make_keyframes(rows: Iterable[dict[str, Any] | Keyframe]) -> KeyframeSet:
    frames: list[Keyframe] = []
    for index, row in enumerate(rows, start=1):
        frames.append(row if isinstance(row, Keyframe) else _parse_keyframe(row, row_number=index))
    return KeyframeSet(tuple(frames))


def read_keyframes_csv(path: str | Path) -> KeyframeSet:
    csv_path = Path(path)
    if not csv_path.exists():
        raise KeyframeIOError(f"Keyframe CSV does not exist: {csv_path}")
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise KeyframeIOError(f"Keyframe CSV is empty: {csv_path}")
        missing = [column for column in KEYFRAME_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise KeyframeIOError(f"Keyframe CSV missing column(s): {missing}")
        return make_keyframes(reader)


def write_keyframes_csv(keyframes: KeyframeSet, path: str | Path) -> None:
    if not isinstance(keyframes, KeyframeSet) or not keyframes.keyframes:
        raise KeyframeIOError("Expected a non-empty KeyframeSet")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=KEYFRAME_COLUMNS)
        writer.writeheader()
        writer.writerows(keyframes.to_rows())
