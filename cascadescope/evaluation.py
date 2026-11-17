"""Evaluation: score the analyzer against the oracle on scenarios.

A scenario is one change applied to one system. For each scenario
we compute: the analyzer's precision/recall/F1 versus the oracle,
the naive-BFS overreach (reachable / oracle-affected), and the
regression set's size and coverage of the oracle-affected nodes
(a check covers itself plus its affected successors, so coverage
against the oracle is a real measurement, not 1.0 by construction).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List

from .analyze import analyze
from .graph import SystemGraph
from .models import Change
from .simulate import oracle_affected, score_analyzer


def load_scenarios(path: str) -> List[Dict[str, object]]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return list(data.get("scenarios", []))
    return list(data)


def run_evaluation(systems_dir: str, scenarios_path: str) -> Dict[str, object]:
    """Run every scenario and aggregate the measurements."""
    scenarios = load_scenarios(scenarios_path)
    graphs: Dict[str, SystemGraph] = {}
    rows: List[Dict[str, object]] = []
    for scenario in scenarios:
        system = str(scenario["system"])
        if system not in graphs:
            graphs[system] = SystemGraph.load(
                str(Path(systems_dir) / (system + ".json"))
            )
        graph = graphs[system]
        change = Change.from_dict(scenario["change"])
        report = analyze(graph, change)
        oracle = oracle_affected(graph, change)
        scores = score_analyzer(report.actually_affected, oracle.affected)
        oracle_set = set(oracle.affected)
        covered: set = set()
        for check in report.regression_set:
            covered.add(check)
            for target in graph.successors(check):
                if target in oracle_set:
                    covered.add(target)
        oracle_coverage = (
            len(covered & oracle_set) / len(oracle_set)
            if oracle_set else 1.0
        )
        rows.append({
            "scenario": str(scenario.get("id", "")),
            "system": system,
            "change": change.description,
            "nodes": len(graph.nodes),
            "reachable": len(report.reachable),
            "analyzer_affected": len(report.actually_affected),
            "oracle_affected": len(oracle.affected),
            "precision": scores["precision"],
            "recall": scores["recall"],
            "f1": scores["f1"],
            "false_positives": scores["false_positives"],
            "false_negatives": scores["false_negatives"],
            "bfs_overreach": round(
                len(report.reachable) / max(1, len(oracle.affected)), 3),
            "regression_set_size": len(report.regression_set),
            "regression_vs_affected": round(
                len(report.regression_set)
                / max(1, len(report.actually_affected)), 3),
            "oracle_coverage": round(oracle_coverage, 4),
        })
    return {"rows": rows, "aggregate": aggregate(rows)}


def aggregate(rows: List[Dict[str, object]]) -> Dict[str, object]:
    """Mean metrics over all scenarios (empty input -> zeros)."""
    if not rows:
        return {
            "scenarios": 0,
            "mean_precision": 0.0,
            "median_precision": 0.0,
            "mean_recall": 0.0,
            "mean_f1": 0.0,
            "median_f1": 0.0,
            "mean_bfs_overreach": 0.0,
            "median_bfs_overreach": 0.0,
            "mean_regression_vs_affected": 0.0,
            "mean_oracle_coverage": 0.0,
        }

    def mean(key: str) -> float:
        return round(sum(float(r[key]) for r in rows) / len(rows), 4)

    def median(key: str) -> float:
        values = sorted(float(r[key]) for r in rows)
        n = len(values)
        mid = n // 2
        if n % 2:
            return round(values[mid], 4)
        return round((values[mid - 1] + values[mid]) / 2, 4)

    return {
        "scenarios": len(rows),
        "mean_precision": mean("precision"),
        "median_precision": median("precision"),
        "mean_recall": mean("recall"),
        "mean_f1": mean("f1"),
        "median_f1": median("f1"),
        "mean_bfs_overreach": mean("bfs_overreach"),
        "median_bfs_overreach": median("bfs_overreach"),
        "mean_regression_vs_affected": mean("regression_vs_affected"),
        "mean_oracle_coverage": mean("oracle_coverage"),
    }


def write_results(results: Dict[str, object], out_dir: str) -> None:
    """Write evaluation.json, evaluation.csv, evaluation_summary.md."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "evaluation.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
        handle.write("\n")
    rows = results["rows"]
    fields = [
        "scenario", "system", "change", "nodes", "reachable",
        "analyzer_affected", "oracle_affected", "precision", "recall",
        "f1", "false_positives", "false_negatives", "bfs_overreach",
        "regression_set_size", "regression_vs_affected",
        "oracle_coverage",
    ]
    with open(out / "evaluation.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})
    agg = results["aggregate"]
    lines = [
        "# CascadeScope evaluation summary",
        "",
        "Scenarios: " + str(agg["scenarios"]),
        "",
        "| metric | value |",
        "|---|---|",
        "| mean precision (analyzer vs oracle) | %.4f |" % agg["mean_precision"],
        "| median precision | %.4f |" % agg["median_precision"],
        "| mean recall (analyzer vs oracle) | %.4f |" % agg["mean_recall"],
        "| mean F1 | %.4f |" % agg["mean_f1"],
        "| median F1 | %.4f |" % agg["median_f1"],
        "| mean BFS overreach (reachable / oracle-affected) | %.3f |"
        % agg["mean_bfs_overreach"],
        "| median BFS overreach | %.3f |" % agg["median_bfs_overreach"],
        "| mean regression set / affected | %.3f |"
        % agg["mean_regression_vs_affected"],
        "| mean regression-set oracle coverage | %.4f |"
        % agg["mean_oracle_coverage"],
        "",
        "Per-scenario rows: evaluation.csv. Full detail: evaluation.json.",
        "",
    ]
    with open(out / "evaluation_summary.md", "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
