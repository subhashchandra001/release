"""Segmentation metrics for binary occupancy masks."""

from __future__ import annotations

import numpy as np


class SegmentationMetricError(ValueError):
    """Raised when segmentation metrics receive incompatible inputs."""


def _binary_arrays(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    truth = np.asarray(y_true)
    pred = np.asarray(y_pred)
    if truth.shape != pred.shape:
        raise SegmentationMetricError(
            f"Shape mismatch: y_true has {truth.shape}, y_pred has {pred.shape}"
        )
    return truth.astype(bool), pred.astype(bool)


def intersection_over_union(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    truth, pred = _binary_arrays(y_true, y_pred)
    union = np.logical_or(truth, pred).sum()
    if union == 0:
        return 1.0
    return float(np.logical_and(truth, pred).sum() / union)


def precision_recall_f1(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    truth, pred = _binary_arrays(y_true, y_pred)
    tp = int(np.logical_and(truth, pred).sum())
    fp = int(np.logical_and(~truth, pred).sum())
    fn = int(np.logical_and(truth, ~pred).sum())
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": float(precision), "recall": float(recall), "f1": float(f1)}
