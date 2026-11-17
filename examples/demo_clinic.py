"""Example: scope a change with the library API.

Run: python examples/demo_clinic.py
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cascadescope.analyze import analyze
from cascadescope.graph import SystemGraph
from cascadescope.models import Change, ChangeKind
from cascadescope.report import render_markdown
from cascadescope.simulate import oracle_affected, score_analyzer


def main() -> None:
    graph = SystemGraph.load("data/systems/clinic.json")
    change = Change(
        "mem_guidelines",
        ChangeKind.MEMORY_EDIT,
        1.0,
        "Guideline memory updated: sepsis threshold 2.0 -> 1.5",
        keys=["sepsis_threshold"],
    )
    report = analyze(graph, change)
    oracle = oracle_affected(graph, change)
    scores = score_analyzer(report.actually_affected, oracle.affected)
    print(report.summary())
    print("Oracle-affected: %d | precision %.3f recall %.3f"
          % (len(oracle.affected), scores["precision"], scores["recall"]))
    print()
    print("Markdown report:")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
