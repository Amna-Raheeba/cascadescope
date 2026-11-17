"""Notebook 01: demo run.

Loads the clinic triage system, scopes three different changes, and
prints each scope report with the oracle comparison.
Run: python notebooks/01_demo_run.py
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cascadescope.analyze import analyze
from cascadescope.graph import SystemGraph
from cascadescope.models import Change, ChangeKind
from cascadescope.simulate import oracle_affected, score_analyzer


def main() -> None:
    graph = SystemGraph.load("data/systems/clinic.json")
    print("System: clinic (%d nodes, %d edges)"
          % (len(graph.nodes), len(graph.edges)))
    print()
    changes = [
        Change("mem_guidelines", ChangeKind.MEMORY_EDIT, 1.0,
               "Guideline memory updated: sepsis threshold 2.0 -> 1.5",
               keys=["sepsis_threshold"]),
        Change("tool_lab_api", ChangeKind.TOOL_UPDATE, 1.0,
               "Lab API tool updated: result units mg/dL -> mmol/L"),
        Change("model_triage", ChangeKind.MODEL_SWAP, 0.8,
               "Triage model swapped to a smaller distilled model"),
        Change("mem_patient_history", ChangeKind.MEMORY_EDIT, 1.0,
               "Patient history edited: unrelated key changed",
               keys=["insurance_id"]),
    ]
    for change in changes:
        report = analyze(graph, change)
        oracle = oracle_affected(graph, change)
        scores = score_analyzer(report.actually_affected, oracle.affected)
        print(report.summary())
        print("Oracle-affected: %d | precision %.3f recall %.3f"
              % (len(oracle.affected), scores["precision"],
                 scores["recall"]))
        print("Actually affected: " + ", ".join(report.actually_affected))
        print("Reachable but unaffected: "
              + ", ".join(report.reachable_but_unaffected))
        print("Greedy regression set: "
              + ", ".join(report.regression_set))
        print("-" * 60)


if __name__ == "__main__":
    main()
