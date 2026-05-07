"""CSV and JSON I/O for benchmark result rows."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class ResultsIOError(ValueError):
    """Raised when result files are missing or malformed."""


PRIVACY_RESULT_COLUMNS = [
    "run_id",
    "artifact_type",
    "filter_name",
    "attack_name",
    "metric_name",
    "value",
]
UTILITY_RESULT_COLUMNS = [
    "run_id",
    "artifact_type",
    "filter_name",
    "utility_name",
    "metric_name",
    "value",
]


@dataclass(frozen=True)
class PrivacyResultRow:
    run_id: str
    artifact_type: str
    filter_name: str
    attack_name: str
    metric_name: str
    value: float


@dataclass(frozen=True)
class UtilityResultRow:
    run_id: str
    artifact_type: str
    filter_name: str
    utility_name: str
    metric_name: str
    value: float


def _write_rows(rows: Iterable[object], path: str | Path, columns: list[str]) -> None:
    materialized = [asdict(row) for row in rows]
    if not materialized:
        raise ResultsIOError(f"Refusing to write empty result file: {path}")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(materialized)


def write_privacy_results(rows: Iterable[PrivacyResultRow], path: str | Path) -> None:
    _write_rows(rows, path, PRIVACY_RESULT_COLUMNS)


def write_utility_results(rows: Iterable[UtilityResultRow], path: str | Path) -> None:
    _write_rows(rows, path, UTILITY_RESULT_COLUMNS)


def _read_rows(path: str | Path, columns: list[str]) -> list[dict[str, Any]]:
    csv_path = Path(path)
    if not csv_path.exists():
        raise ResultsIOError(f"Result CSV does not exist: {csv_path}")
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ResultsIOError(f"Result CSV is empty: {csv_path}")
        missing = [column for column in columns if column not in reader.fieldnames]
        if missing:
            raise ResultsIOError(f"Result CSV {csv_path} missing column(s): {missing}")
        rows = []
        for row_number, row in enumerate(reader, start=2):
            parsed = {column: row[column] for column in columns}
            try:
                parsed["value"] = float(parsed["value"])
            except (TypeError, ValueError) as exc:
                raise ResultsIOError(
                    f"Result CSV {csv_path} row {row_number} has a non-numeric value"
                ) from exc
            rows.append(parsed)
    if not rows:
        raise ResultsIOError(f"Result CSV contains no rows: {csv_path}")
    return rows


def read_privacy_results(path: str | Path) -> list[dict[str, Any]]:
    return _read_rows(path, PRIVACY_RESULT_COLUMNS)


def read_utility_results(path: str | Path) -> list[dict[str, Any]]:
    return _read_rows(path, UTILITY_RESULT_COLUMNS)


def aggregate_results(frames: Iterable[Iterable[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Aggregate existing result rows by non-run columns."""

    rows = [dict(row) for frame in frames for row in frame]
    if not rows:
        raise ResultsIOError("No result rows were provided for aggregation")
    all_columns = sorted({column for row in rows for column in row})
    group_columns = [column for column in all_columns if column not in {"run_id", "value"}]
    groups: dict[tuple[Any, ...], list[float]] = {}
    exemplars: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        if "value" not in row:
            raise ResultsIOError("Result rows are missing the value column")
        key = tuple(row.get(column, "") for column in group_columns)
        groups.setdefault(key, []).append(float(row["value"]))
        exemplars.setdefault(key, {column: row.get(column, "") for column in group_columns})

    output = []
    for key, values in groups.items():
        count = len(values)
        mean = sum(values) / count
        variance = (
            sum((value - mean) ** 2 for value in values) / (count - 1) if count > 1 else 0.0
        )
        record = dict(exemplars[key])
        record.update(
            {
                "count": count,
                "mean": mean,
                "std": variance**0.5,
                "min": min(values),
                "max": max(values),
            }
        )
        output.append(record)
    return output


def write_json_records(records: Iterable[dict[str, Any]], path: str | Path) -> None:
    materialized = [dict(record) for record in records]
    if not materialized:
        raise ResultsIOError(f"Refusing to write empty JSON result file: {path}")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(materialized, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_result_records_csv(records: Iterable[dict[str, Any]], path: str | Path) -> None:
    materialized = [dict(record) for record in records]
    if not materialized:
        raise ResultsIOError(f"Refusing to write empty CSV result file: {path}")
    columns = list(materialized[0])
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(materialized)
