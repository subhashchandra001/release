from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from privatemap.io.config import load_yaml


EXPECTED_DETECTION_FIELDS = [
    "run_id",
    "keyframe_id",
    "image_path",
    "class_name",
    "confidence",
    "xmin",
    "ymin",
    "xmax",
    "ymax",
    "map_x",
    "map_y",
    "is_sensitive",
]


def test_annotation_files_are_parseable() -> None:
    if not Path("data/annotations/nav_goals.yaml").exists():
        pytest.skip("dataset data/ directory is not present in the code release")

    nav_goals = load_yaml("data/annotations/nav_goals.yaml")
    with open("data/annotations/sensitive_objects.csv", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames
    with open("data/annotations/rooms.geojson", encoding="utf-8") as handle:
        rooms = json.load(handle)

    assert rows == []
    assert fieldnames == EXPECTED_DETECTION_FIELDS

    assert rooms["type"] == "FeatureCollection"
    assert isinstance(rooms["features"], list)
    assert len(rooms["features"]) >= 3

    for feature in rooms["features"]:
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Polygon"
        props = feature["properties"]
        assert props["environment_id"] in {"env1", "env2", "env3"}
        assert props["review_status"] == "needs_manual_review"

    assert "environments" in nav_goals
    assert set(nav_goals["environments"]) >= {"env1", "env2", "env3"}

    for env_id, env in nav_goals["environments"].items():
        assert env_id in {"env1", "env2", "env3"}
        assert "map_yaml" in env
        assert len(env["goals"]) >= 5
        assert len(env["routes"]) >= 5
        width, height = env["map_size"]
        for route in env["routes"]:
            for key in ("start", "goal"):
                x, y = route[key]
                assert 0 <= x < width
                assert 0 <= y < height
