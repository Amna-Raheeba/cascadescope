"""Command-line interface for CascadeScope."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyze import analyze
from .evaluation import run_evaluation, write_results
from .graph import SystemGraph
from .models import Change, ChangeKind
from .report import render_markdown
from .simulate import oracle_affected, score_analyzer

HERE = Path(__file__).resolve().parent.parent
DATA_DIR = HERE / "data"
SYSTEMS_DIR = DATA_DIR / "systems"
SCENARIOS_PATH = DATA_DIR / "scenarios.json"


def _system_path(name: str) -> Path:
    path = Path(name)
    if path.exists():
        return path
    return SYSTEMS_DIR / (name + ".json")


def cmd_demo(_args: argparse.Namespace) -> int:
    """Run the bundled clinic demo and print the scope report."""
    graph = SystemGraph.load(str(SYSTEMS_DIR / "clinic.json"))
    changes = [
        Change("mem_guidelines", ChangeKind.MEMORY_EDIT, 1.0,
               "Guideline memory updated: sepsis threshold 2.0 -> 1.5",
               keys=["sepsis_threshold"]),
        Change("tool_lab_api", ChangeKind.TOOL_UPDATE, 1.0,
               "Lab API tool updated: result units mg/dL -> mmol/L"),
        Change("model_triage", ChangeKind.MODEL_SWAP, 0.8,
               "Triage model swapped to a smaller distilled model"),
    ]
    for change in changes:
        report = analyze(graph, change)
        oracle = oracle_affected(graph, change)
        scores = score_analyzer(report.actually_affected, oracle.affected)
        print(report.summary())
        print("Oracle-affected: " + str(len(oracle.affected))
              + " | analyzer precision %.3f recall %.3f"
              % (scores["precision"], scores["recall"]))
        print("-" * 60)
    return 0


def cmd_scope(args: argparse.Namespace) -> int:
    graph = SystemGraph.load(str(_system_path(args.system)))
    change = Change(
        args.node,
        ChangeKind(args.kind),
        args.severity,
        args.description or (args.kind + " on " + args.node),
        keys=args.keys or [],
    )
    report = analyze(graph, change)
    oracle = oracle_affected(graph, change)
    scores = score_analyzer(report.actually_affected, oracle.affected)
    if args.format == "json":
        payload = {
            "system": report.system,
            "change": change.to_dict(),
            "directly_affected": report.directly_affected,
            "reachable": report.reachable,
            "actually_affected": report.actually_affected,
            "reachable_but_unaffected": report.reachable_but_unaffected,
            "unaffected": report.unaffected,
            "hop_distance": report.hop_distance,
            "delta": report.delta,
            "blast_radius": report.blast_radius,
            "max_depth": report.max_depth,
            "overreach": report.overreach,
            "regression_set": report.regression_set,
            "regression_coverage": report.regression_coverage,
            "oracle_affected": oracle.affected,
            "oracle_scores": scores,
        }
        print(json.dumps(payload, indent=2))
    elif args.format == "md":
        print(render_markdown(report))
    else:
        print(report.summary())
        print("Oracle-affected: " + str(len(oracle.affected))
              + " | analyzer precision %.3f recall %.3f"
              % (scores["precision"], scores["recall"]))
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_markdown(report), encoding="utf-8")
        print("Report written to " + str(out))
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    results = run_evaluation(str(SYSTEMS_DIR), str(SCENARIOS_PATH))
    write_results(results, args.out)
    agg = results["aggregate"]
    print("Scenarios: " + str(agg["scenarios"]))
    print("Mean precision: %.4f" % agg["mean_precision"])
    print("Mean recall: %.4f" % agg["mean_recall"])
    print("Mean F1: %.4f" % agg["mean_f1"])
    print("Mean BFS overreach: %.3f" % agg["mean_bfs_overreach"])
    print("Mean regression set / affected: %.3f"
          % agg["mean_regression_vs_affected"])
    print("Mean regression-set oracle coverage: %.4f"
          % agg["mean_oracle_coverage"])
    print("Results written to " + args.out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cascadescope",
        description="Forward blast-radius analysis for agentic systems.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo", help="Run the bundled clinic demo.")

    scope = sub.add_parser("scope", help="Scope one change.")
    scope.add_argument("--system", required=True,
                       help="System name (clinic, research, phm) or path.")
    scope.add_argument("--node", required=True,
                       help="Node the change is applied to.")
    scope.add_argument("--kind", required=True,
                       choices=[k.value for k in ChangeKind],
                       help="Kind of change.")
    scope.add_argument("--severity", type=float, default=1.0,
                       help="Change severity in (0, 1] (default 1.0).")
    scope.add_argument("--description", default="",
                       help="Human-readable description of the change.")
    scope.add_argument("--keys", nargs="*", default=[],
                       help="Record keys touched (memory edits).")
    scope.add_argument("--format", choices=["text", "json", "md"],
                       default="text")
    scope.add_argument("--out", default="",
                       help="Also write a Markdown report to this path.")

    evaluate = sub.add_parser("evaluate", help="Run the full evaluation.")
    evaluate.add_argument("--out", default="results",
                          help="Output directory (default: results).")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "demo":
        return cmd_demo(args)
    if args.command == "scope":
        return cmd_scope(args)
    if args.command == "evaluate":
        return cmd_evaluate(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
