"""The oracle: an independent ground truth for what a change affects.

The oracle does NOT use the analyzer's edge gates or attenuation.
It runs each node's own transfer function (declared in the system
data) to fixpoint: a change delta is injected at the changed node
and propagated until no delta changes any more. Because deltas only
shrink (every transfer is non-amplifying), the iteration always
converges.

Transfer types (see models.Node):
- passthrough / scale: out = factor * in.
- threshold: out = in if in >= threshold else 0.0.
- keyed: out = in if the change touches one of the node's keys.
- absorbing: out = 0.0.

The analyzer is scored against this oracle: precision, recall, and
F1 of its "actually affected" set. Where they disagree, the oracle
wins — that is the point of having one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .analyze import AFFECT_THRESHOLD
from .graph import SystemGraph
from .models import Change

MAX_ITERATIONS = 100


@dataclass
class OracleResult:
    system: str
    change: Change
    affected: List[str] = field(default_factory=list)
    delta: Dict[str, float] = field(default_factory=dict)
    iterations: int = 0


def _node_output(node_transfer: Dict[str, object], incoming: float,
                 change: Change) -> float:
    kind = str(node_transfer.get("type", "passthrough"))
    if kind == "absorbing":
        return 0.0
    if kind == "threshold":
        threshold = float(node_transfer.get("threshold", 0.5))
        return incoming if incoming >= threshold else 0.0
    if kind == "keyed":
        keys = node_transfer.get("keys", [])
        if not isinstance(keys, list):
            keys = []
        if change.keys and not set(change.keys) & set(keys):
            return 0.0
        factor = float(node_transfer.get("factor", 1.0))
        return incoming * factor
    factor = float(node_transfer.get("factor", 1.0))
    return incoming * factor


def oracle_affected(graph: SystemGraph, change: Change) -> OracleResult:
    """Run the oracle simulation to fixpoint for one change."""
    if change.node_id not in graph.nodes:
        raise ValueError("change node not in graph: " + change.node_id)
    # The changed node's own transfer applies to the injected delta:
    # a keyed memory node edited on a key nobody reads emits nothing.
    origin = _node_output(graph.nodes[change.node_id].transfer,
                          change.severity, change)
    deltas: Dict[str, float] = {change.node_id: origin}
    iterations = 0
    for step in range(MAX_ITERATIONS):
        iterations = step + 1
        changed = False
        # One sweep over all edges; repeat until nothing moves.
        for edge in graph.edges:
            if edge.source not in deltas:
                continue
            node = graph.nodes[edge.target]
            outgoing = _node_output(node.transfer, deltas[edge.source],
                                    change)
            arriving = outgoing * edge.attenuation
            if arriving > deltas.get(edge.target, 0.0) + 1e-12:
                deltas[edge.target] = arriving
                changed = True
        if not changed:
            break
    affected = sorted(
        n for n, d in deltas.items()
        if n != change.node_id and d >= AFFECT_THRESHOLD
    )
    return OracleResult(
        system=graph.name,
        change=change,
        affected=affected,
        delta={n: round(d, 4) for n, d in deltas.items()
               if n != change.node_id and d >= AFFECT_THRESHOLD},
        iterations=iterations,
    )


def score_analyzer(predicted: List[str], oracle: List[str]) -> Dict[str, float]:
    """Precision / recall / F1 of the analyzer against the oracle."""
    pred = set(predicted)
    truth = set(oracle)
    true_positive = len(pred & truth)
    precision = true_positive / len(pred) if pred else 1.0
    recall = true_positive / len(truth) if truth else 1.0
    f1 = 0.0
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positives": true_positive,
        "false_positives": len(pred - truth),
        "false_negatives": len(truth - pred),
    }
