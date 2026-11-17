"""Regenerate every number in results/ from the shipped data.

Run: python scripts/reproduce_results.py
Writes results/evaluation.json, results/evaluation.csv, and
results/evaluation_summary.md. Fails (exit 1) if any headline
aggregate drifts from the values recorded in results/HEADLINE.md,
so a stale results directory cannot silently ship.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from cascadescope.evaluation import run_evaluation, write_results

RECORDED = {
    "scenarios": 36,
    "mean_precision": 0.6167,
    "mean_recall": 1.0,
    "mean_f1": 0.6779,
    "mean_bfs_overreach": 3.8027,
    "mean_regression_vs_affected": 0.4334,
    "mean_oracle_coverage": 1.0,
}


def main() -> int:
    results = run_evaluation(str(HERE / "data" / "systems"),
                             str(HERE / "data" / "scenarios.json"))
    write_results(results, str(HERE / "results"))
    agg = results["aggregate"]
    print("Scenarios: %d" % agg["scenarios"])
    print("Mean precision: %.4f" % agg["mean_precision"])
    print("Mean recall: %.4f" % agg["mean_recall"])
    print("Mean F1: %.4f" % agg["mean_f1"])
    print("Mean BFS overreach: %.3f" % agg["mean_bfs_overreach"])
    print("Mean regression set / affected: %.3f"
          % agg["mean_regression_vs_affected"])
    print("Mean regression-set oracle coverage: %.4f"
          % agg["mean_oracle_coverage"])
    drifted = []
    for key, expected in RECORDED.items():
        actual = agg[key]
        if abs(float(actual) - float(expected)) > 0.001:
            drifted.append("%s: recorded %.4f, got %.4f"
                           % (key, expected, actual))
    if drifted:
        print("HEADLINE DRIFT:")
        for line in drifted:
            print("  " + line)
        print("Update RECORDED in scripts/reproduce_results.py and "
              "results/HEADLINE.md only if the data really changed.")
        return 1
    print("Headlines match recorded values. Results written to results/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
