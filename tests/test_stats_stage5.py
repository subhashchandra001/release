from __future__ import annotations

from privatemap.metrics.stats import mean_ci, summarize


def test_summarize_and_mean_ci() -> None:
    summary = summarize([1.0, 2.0, 3.0])
    assert summary["count"] == 3.0
    assert summary["mean"] == 2.0
    assert summary["min"] == 1.0
    assert summary["max"] == 3.0

    interval = mean_ci([1.0, 2.0, 3.0], n_resamples=50, seed=5)
    assert interval["ci_low"] <= interval["mean"] <= interval["ci_high"]
