from __future__ import annotations

import json

import pytest

from privatemap.io.results_io import (
    PrivacyResultRow,
    ResultsIOError,
    aggregate_results,
    read_privacy_results,
    write_json_records,
    write_privacy_results,
)


def test_results_roundtrip_and_aggregation(tmp_path) -> None:
    csv_path = tmp_path / "privacy_results.csv"
    write_privacy_results(
        [
            PrivacyResultRow("run_a", "occupancy_map", "blur", "floor", "iou", 0.5),
            PrivacyResultRow("run_b", "occupancy_map", "blur", "floor", "iou", 1.0),
        ],
        csv_path,
    )

    frame = read_privacy_results(csv_path)
    aggregated = aggregate_results([frame])

    assert aggregated[0]["count"] == 2
    assert aggregated[0]["mean"] == pytest.approx(0.75)

    json_path = tmp_path / "aggregated.json"
    write_json_records(aggregated, json_path)
    records = json.loads(json_path.read_text(encoding="utf-8"))
    assert records[0]["metric_name"] == "iou"


def test_results_io_refuses_empty_outputs(tmp_path) -> None:
    with pytest.raises(ResultsIOError, match="empty"):
        write_privacy_results([], tmp_path / "privacy_results.csv")
