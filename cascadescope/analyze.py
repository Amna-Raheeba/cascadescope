"""Forward scope analysis: what a change will affect.

The analyzer works only from the graph — edge gates and attenuation
— never from the oracle's per-node transfer functions. That
separation is deliberate: the analyzer is the cheap approximation a
team would actually run before a change, and the oracle in
simulate.py is the independent ground truth it is scored against.

A node is *actually affected* when a change delta reaches it above
the threshold. A delta starts at ``change.severity`` on the changed
node, crosses an edge only if the edge's gate allows the change
kind, and is multiplied by the edge attenuation at every hop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from .graph import SystemGraph
from .models import Change

# A node counts as affected when the arriving delta is at least this.
AFFECT_THRESHOLD = 0.10


@dataclass
class ScopeReport:
    """The ranked scope of one change."""

    system: str
    change: Change
    directly_affected: List[str] = field(default_factory=list)
    reachable: List[str] = field(default_factory=list)
    actually_affected: List[str] = field(default_factory=list)
    reachable_but_unaffected: List[str] = field(default_factory=list)
    unaffected: List[str] = field(default_factory=list)
    hop_distance: Dict[str, int] = field(default_factory=dict)
    delta: Dict[str, float] = field(default_factory=dict)
    blast_radius: float = 0.0
    max_depth: int = 0
    overreach: float = 0.0
    regression_set: List[str] = field(default_factory=list)
    regression_coverage: float = 0.0

    def summary(self) -> str:
        lines = [
            "Change: " + self.change.description,
            "System: " + self.system,
            "Directly affected (hop 1): " + str(len(self.directly_affected)),
            "Reachable (forward closure): " + str(len(self.reachable)),
            "Actually affected: " + str(len(self.actually_affected)),
            "Reachable but unaffected: "
            + str(len(self.reachable_but_unaffected)),
            "Provably unaffected: " + str(len(self.unaffected)),
            "Blast radius: %.3f" % self.blast_radius,
            "Max cascade depth: " + str(self.max_depth),
            "Overreach (reachable / affected): %.2f" % self.overreach,
            "Greedy regression set: " + str(len(self.regression_set))
            + " checks, coverage %.3f" % self.regression_coverage,
        ]
        return "\n".join(lines)


def propagate_deltas(graph: SystemGraph, change: Change) -> Dict[str, float]:
    """Propagate a change delta through the graph.

    Deterministic breadth-first propagation: at each node keep the
    largest arriving delta (a node is affected by its strongest
    incoming path, not by the sum — a change does not add up across
    independent paths). Returns the delta at every node the change
    reaches, including the changed node itself.
    """
    deltas: Dict[str, float] = {change.node_id: change.severity}
    frontier = [change.node_id]
    while frontier:
        current = frontier.pop(0)
        current_delta = deltas[current]
        for edge in graph.out_edges(current):
            if not edge.allows(change.kind.value):
                continue
            arriving = current_delta * edge.attenuation
            if arriving < AFFECT_THRESHOLD:
                continue
            if arriving > deltas.get(edge.target, 0.0):
                deltas[edge.target] = arriving
                frontier.append(edge.target)
    return deltas


def analyze(graph: SystemGraph, change: Change) -> ScopeReport:
    """Compute the full scope report for one change."""
    if change.node_id not in graph.nodes:
        raise ValueError("change node not in graph: " + change.node_id)

    closure = graph.forward_closure(change.node_id)
    deltas = propagate_deltas(graph, change)

    reachable = sorted(
        (node_id for node_id in closure if node_id != change.node_id),
        key=lambda n: (closure[n], n),
    )
    affected = sorted(
        (node_id for node_id in deltas if node_id != change.node_id),
        key=lambda n: (closure.get(n, 0), n),
    )
    affected_set = set(affected)
    reachable_but_unaffected = [n for n in reachable if n not in affected_set]
    unaffected = sorted(
        n for n in graph.nodes
        if n != change.node_id and n not in closure
    )
    directly = sorted(
        (n for n in graph.successors(change.node_id)),
        key=lambda n: n,
    )
    max_depth = max((closure[n] for n in affected), default=0)
    blast_radius = len(affected) / max(1, len(graph.nodes) - 1)
    overreach = len(reachable) / max(1, len(affected))

    report = ScopeReport(
        system=graph.name,
        change=change,
        directly_affected=directly,
        reachable=reachable,
        actually_affected=affected,
        reachable_but_unaffected=reachable_but_unaffected,
        unaffected=unaffected,
        hop_distance={n: closure[n] for n in reachable},
        delta={n: round(deltas[n], 4) for n in affected},
        blast_radius=round(blast_radius, 4),
        max_depth=max_depth,
        overreach=round(overreach, 3),
    )
    checks, coverage = regression_set(graph, report)
    report.regression_set = checks
    report.regression_coverage = coverage
    return report


def regression_set(
    graph: SystemGraph, report: ScopeReport
) -> tuple:
    """Greedy minimal regression set covering the affected scope.

    A check on node X covers X itself and every affected node that
    X directly feeds (its affected successors): verifying X and
    re-running its immediate downstream checks catches a regression
    anywhere in the affected scope. The greedy set cover picks, at
    each step, the check covering the most still-uncovered affected
    nodes, breaking ties by lowest hop distance then node id, so the
    result is deterministic. Coverage is the fraction of affected
    nodes covered; it is 1.0 by construction, because a node always
    covers itself — the interesting number is the set size versus
    checking every affected node.
    """
    affected = set(report.actually_affected)
    if not affected:
        return [], 1.0
    coverage_of: Dict[str, Set[str]] = {}
    for node_id in affected:
        covered = {node_id}
        for target in graph.successors(node_id):
            if target in affected:
                covered.add(target)
        coverage_of[node_id] = covered
    uncovered = set(affected)
    chosen: List[str] = []
    while uncovered:
        best = max(
            coverage_of,
            key=lambda n: (
                len(coverage_of[n] & uncovered),
                -report.hop_distance.get(n, 0),
            ),
        )
        gain = coverage_of[best] & uncovered
        if not gain:
            break
        chosen.append(best)
        uncovered -= gain
    coverage = 1.0 - len(uncovered) / len(affected)
    return sorted(chosen), round(coverage, 4)
