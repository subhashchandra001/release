import numpy as np

from privatemap.attacks.room_graph_attack import room_graph_leakage


def test_room_graph_leakage_reports_required_metrics():
    reference = np.full((20, 30), 100, dtype=int)
    released = np.full((20, 30), 100, dtype=int)

    reference[2:8, 2:8] = 0
    reference[2:8, 14:20] = 0
    reference[4:6, 8:14] = 0

    released[2:8, 2:8] = 0
    released[2:8, 14:20] = 0
    released[4:6, 8:14] = 0

    boxes = [
        {"name": "left", "bbox": (2, 2, 8, 8)},
        {"name": "right", "bbox": (14, 2, 20, 8)},
    ]

    result = room_graph_leakage(reference, released, room_boxes=boxes)

    assert result.attack_name == "room_graph_leakage"
    for metric in [
        "room_node_count",
        "doorway_count",
        "connectivity_similarity",
        "graph_edit_distance",
        "doorway_recall",
        "skeleton_iou",
    ]:
        assert metric in result.metrics

    assert result.metrics["connectivity_similarity"] == 1.0
    assert result.metrics["doorway_recall"] == 1.0
