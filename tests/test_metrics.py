from __future__ import annotations

import numpy as np

from privatemap.filters.trajectory_filters import shifted
from privatemap.io.trajectory_io import read_trajectory_csv
from privatemap.metrics.segmentation_metrics import (
    intersection_over_union,
    precision_recall_f1,
)
from privatemap.metrics.trajectory_metrics import bootstrap_ci, edit_distance, trajectory_rmse


def test_segmentation_metrics() -> None:
    truth = np.array([[1, 0], [1, 0]], dtype=bool)
    pred = np.array([[1, 1], [0, 0]], dtype=bool)
    assert intersection_over_union(truth, pred) == 1 / 3
    scores = precision_recall_f1(truth, pred)
    assert scores == {"precision": 0.5, "recall": 0.5, "f1": 0.5}


def test_trajectory_rmse_and_edit_distance() -> None:
    reference = read_trajectory_csv("tests/fixtures/trajectory.csv")
    estimate = shifted(reference, dx=1.0)
    assert trajectory_rmse(reference, estimate) == 1.0
    assert edit_distance(["lab", "hall"], ["lab", "kitchen", "hall"]) == 1


def test_bootstrap_ci_is_seeded() -> None:
    stat, low, high = bootstrap_ci([1, 2, 3, 4], n_resamples=100, seed=4)
    assert stat == 2.5
    assert low <= stat <= high
