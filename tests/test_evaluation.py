"""Tests for the evaluation harness."""

from cascadescope.evaluation import aggregate, load_scenarios, run_evaluation


def test_scenarios_load():
    scenarios = load_scenarios("data/scenarios.json")
    assert len(scenarios) == 36
    systems = {s["system"] for s in scenarios}
    assert systems == {"clinic", "research", "phm"}


def test_evaluation_runs_all_scenarios():
    results = run_evaluation("data/systems", "data/scenarios.json")
    assert len(results["rows"]) == 36
    assert results["aggregate"]["scenarios"] == 36


def test_evaluation_aggregates_are_in_range():
    results = run_evaluation("data/systems", "data/scenarios.json")
    agg = results["aggregate"]
    for key in ("mean_precision", "mean_recall", "mean_f1",
                "mean_oracle_coverage"):
        assert 0.0 <= agg[key] <= 1.0
    assert agg["mean_bfs_overreach"] >= 1.0
    assert agg["mean_regression_vs_affected"] <= 1.0


def test_evaluation_headline_values():
    # Pinned to the values in results/HEADLINE.md; if the data changes
    # on purpose, update the pin here and in reproduce_results.py.
    results = run_evaluation("data/systems", "data/scenarios.json")
    agg = results["aggregate"]
    assert agg["mean_precision"] == 0.6167
    assert agg["mean_recall"] == 1.0
    assert agg["mean_f1"] == 0.6779
    assert agg["mean_bfs_overreach"] == 3.8027
    assert agg["mean_oracle_coverage"] == 1.0


def test_recall_is_one_on_every_scenario():
    results = run_evaluation("data/systems", "data/scenarios.json")
    for row in results["rows"]:
        assert row["recall"] == 1.0, row["scenario"]


def test_regression_set_always_covers_oracle():
    results = run_evaluation("data/systems", "data/scenarios.json")
    for row in results["rows"]:
        assert row["oracle_coverage"] == 1.0, row["scenario"]


def test_aggregate_empty_input():
    agg = aggregate([])
    assert agg["scenarios"] == 0
    assert agg["mean_precision"] == 0.0


def test_aggregate_median():
    rows = [{"precision": 0.5, "recall": 1.0, "f1": 0.6,
             "bfs_overreach": 2.0, "regression_vs_affected": 0.4,
             "oracle_coverage": 1.0},
            {"precision": 0.9, "recall": 1.0, "f1": 0.9,
             "bfs_overreach": 4.0, "regression_vs_affected": 0.5,
             "oracle_coverage": 1.0}]
    agg = aggregate(rows)
    assert agg["median_precision"] == 0.7
    assert agg["median_bfs_overreach"] == 3.0
