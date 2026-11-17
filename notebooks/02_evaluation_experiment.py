"""Notebook 02: evaluation experiment.

Runs all 36 scenarios, scores the analyzer against the oracle, and
prints the aggregate table plus the worst-precision scenarios.
Run: python notebooks/02_evaluation_experiment.py
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cascadescope.evaluation import run_evaluation

SYSTEMS_DIR = "data/systems"
SCENARIOS_PATH = "data/scenarios.json"


def main() -> None:
    results = run_evaluation(SYSTEMS_DIR, SCENARIOS_PATH)
    agg = results["aggregate"]
    print("CascadeScope evaluation: %d scenarios" % agg["scenarios"])
    print()
    print("mean precision   %.4f  (median %.4f)"
          % (agg["mean_precision"], agg["median_precision"]))
    print("mean recall      %.4f" % agg["mean_recall"])
    print("mean F1          %.4f  (median %.4f)"
          % (agg["mean_f1"], agg["median_f1"]))
    print("mean BFS overreach  %.3f  (median %.3f)"
          % (agg["mean_bfs_overreach"], agg["median_bfs_overreach"]))
    print("regression set / affected  %.3f" % agg["mean_regression_vs_affected"])
    print("regression-set oracle coverage  %.4f"
          % agg["mean_oracle_coverage"])
    print()
    print("Worst-precision scenarios (where the analyzer over-claims):")
    rows = sorted(results["rows"], key=lambda r: (r["precision"], r["scenario"]))
    for row in rows[:6]:
        print("  %-12s precision %.3f  analyzer %d vs oracle %d  (%s)"
              % (row["scenario"], row["precision"],
                 row["analyzer_affected"], row["oracle_affected"],
                 row["change"]))
    print()
    print("Best-precision scenarios:")
    for row in sorted(results["rows"], key=lambda r: (-r["precision"], r["scenario"]))[:5]:
        print("  %-12s precision %.3f  analyzer %d vs oracle %d"
              % (row["scenario"], row["precision"],
                 row["analyzer_affected"], row["oracle_affected"]))


if __name__ == "__main__":
    main()
