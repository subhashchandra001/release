from privatemap.attacks.routine_attack import routine_leakage
from privatemap.io.trajectory_io import Trajectory


def _trajectory(points):
    rows = []
    for i, (x, y) in enumerate(points):
        rows.append(
            {
                "run_id": "r",
                "timestamp": float(i),
                "x": float(x),
                "y": float(y),
                "z": 0.0,
                "qx": 0.0,
                "qy": 0.0,
                "qz": 0.0,
                "qw": 1.0,
                "yaw": 0.0,
            }
        )
    return Trajectory(rows)


def test_routine_leakage_identical_route_scores_high():
    points = [(0, 0), (1, 0), (2, 0), (1, 0), (0, 0), (1, 0), (2, 0), (1, 0), (0, 0)]
    result = routine_leakage(_trajectory(points), _trajectory(points), grid_size=0.5)

    assert result.attack_name == "routine_leakage"
    assert result.metrics["visit_order_similarity"] == 1.0
    assert result.metrics["route_class_accuracy"] == 1.0
    assert result.metrics["loop_similarity"] >= 0.9
