"""Geometry leakage attack using point-cloud similarity metrics."""

from __future__ import annotations

from privatemap.metrics.geometry_metrics import chamfer_distance, centroid_distance


def geometry_leakage_score(reference: object, observed: object) -> dict[str, float]:
    chamfer = chamfer_distance(reference, observed)
    centroid = centroid_distance(reference, observed)
    return {
        "chamfer_distance": float(chamfer),
        "centroid_distance": float(centroid),
        "similarity": float(1.0 / (1.0 + chamfer)),
    }
