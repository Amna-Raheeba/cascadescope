"""Tests for the scope analyzer and the regression set."""

import pytest

from cascadescope.analyze import analyze, propagate_deltas
from cascadescope.graph import SystemGraph
from cascadescope.models import Change, ChangeKind, Edge, Node, NodeKind


def build_diamond():
    """a -> b -> d, a -> c -> d, plus an isolated node e."""
    graph = SystemGraph("diamond")
    for node_id in ("a", "b", "c", "d", "e"):
        graph.add_node(Node(node_id, NodeKind.TOOL))
    graph.add_edge(Edge("a", "b", attenuation=0.9))
    graph.add_edge(Edge("a", "c", attenuation=0.5))
    graph.add_edge(Edge("b", "d", attenuation=0.9))
    graph.add_edge(Edge("c", "d", attenuation=0.9))
    return graph


def test_directly_affected_is_hop_one():
    report = analyze(build_diamond(),
                     Change("a", ChangeKind.TOOL_UPDATE, 1.0))
    assert report.directly_affected == ["b", "c"]


def test_reachable_includes_transitive_nodes():
    report = analyze(build_diamond(),
                     Change("a", ChangeKind.TOOL_UPDATE, 1.0))
    assert report.reachable == ["b", "c", "d"]
    assert report.hop_distance == {"b": 1, "c": 1, "d": 2}
    assert report.max_depth == 2


def test_unaffected_nodes_are_the_rest():
    report = analyze(build_diamond(),
                     Change("a", ChangeKind.TOOL_UPDATE, 1.0))
    assert report.unaffected == ["e"]


def test_blast_radius_is_affected_over_others():
    report = analyze(build_diamond(),
                     Change("a", ChangeKind.TOOL_UPDATE, 1.0))
    assert report.blast_radius == 0.75  # 3 of the other 4 nodes


def test_gate_blocks_propagation():
    graph = SystemGraph("gated")
    for node_id in ("model", "agent", "plan"):
        graph.add_node(Node(node_id, NodeKind.TOOL))
    graph.add_edge(Edge("model", "agent", attenuation=1.0,
                        gate=["model_swap"]))
    graph.add_edge(Edge("agent", "plan", attenuation=1.0))
    # A memory edit on the model node cannot cross the model gate.
    report = analyze(graph, Change("model", ChangeKind.MEMORY_EDIT, 1.0))
    assert report.actually_affected == []
    assert report.reachable == ["agent", "plan"]
    assert report.reachable_but_unaffected == ["agent", "plan"]
    assert report.overreach == 2.0  # reachable 2, affected 0 -> capped at 2/1


def test_gate_allows_matching_kind():
    graph = SystemGraph("gated")
    for node_id in ("model", "agent"):
        graph.add_node(Node(node_id, NodeKind.TOOL))
    graph.add_edge(Edge("model", "agent", attenuation=1.0,
                        gate=["model_swap"]))
    report = analyze(graph, Change("model", ChangeKind.MODEL_SWAP, 1.0))
    assert report.actually_affected == ["agent"]


def test_attenuation_below_threshold_stops_the_cascade():
    graph = SystemGraph("damped")
    for node_id in ("a", "b", "c"):
        graph.add_node(Node(node_id, NodeKind.TOOL))
    graph.add_edge(Edge("a", "b", attenuation=0.05))
    graph.add_edge(Edge("b", "c", attenuation=1.0))
    report = analyze(graph, Change("a", ChangeKind.TOOL_UPDATE, 1.0))
    assert report.actually_affected == []
    assert report.reachable == ["b", "c"]


def test_small_severity_can_still_reach_one_hop():
    graph = SystemGraph("small")
    for node_id in ("a", "b", "c"):
        graph.add_node(Node(node_id, NodeKind.TOOL))
    graph.add_edge(Edge("a", "b", attenuation=0.9))
    graph.add_edge(Edge("b", "c", attenuation=0.9))
    report = analyze(graph, Change("a", ChangeKind.TOOL_UPDATE, 0.15))
    # 0.15 * 0.9 = 0.135 reaches b; 0.135 * 0.9 = 0.1215 reaches c too.
    assert report.actually_affected == ["b", "c"]


def test_delta_keeps_the_strongest_path():
    graph = build_diamond()
    deltas = propagate_deltas(graph, Change("a", ChangeKind.TOOL_UPDATE, 1.0))
    # d via b: 0.9 * 0.9 = 0.81; via c: 0.5 * 0.9 = 0.45. Max wins.
    assert deltas["d"] == pytest.approx(0.81)


def test_analyze_rejects_change_on_unknown_node():
    with pytest.raises(ValueError):
        analyze(build_diamond(), Change("ghost", ChangeKind.TOOL_UPDATE, 1.0))


def test_regression_set_covers_all_affected():
    graph = build_diamond()
    report = analyze(graph, Change("a", ChangeKind.TOOL_UPDATE, 1.0))
    assert report.regression_coverage == 1.0
    assert len(report.regression_set) < len(report.actually_affected)


def test_regression_set_is_smaller_than_full_scope():
    graph = SystemGraph.load("data/systems/clinic.json")
    report = analyze(graph, Change("tool_lab_api", ChangeKind.TOOL_UPDATE, 1.0))
    assert len(report.regression_set) <= 5
    assert len(report.actually_affected) == 11
    assert report.regression_coverage == 1.0


def test_regression_set_empty_when_nothing_affected():
    graph = SystemGraph("gated")
    for node_id in ("model", "agent"):
        graph.add_node(Node(node_id, NodeKind.TOOL))
    graph.add_edge(Edge("model", "agent", attenuation=1.0,
                        gate=["model_swap"]))
    report = analyze(graph, Change("model", ChangeKind.MEMORY_EDIT, 1.0))
    assert report.regression_set == []
    assert report.regression_coverage == 1.0


def test_regression_set_is_deterministic():
    graph = SystemGraph.load("data/systems/phm.json")
    change = Change("tool_vibration", ChangeKind.TOOL_UPDATE, 1.0)
    first = analyze(graph, change).regression_set
    second = analyze(graph, change).regression_set
    assert first == second


def test_cycle_does_not_loop_forever():
    graph = SystemGraph.load("data/systems/phm.json")
    report = analyze(graph, Change("agent_monitor", ChangeKind.TOOL_UPDATE, 1.0))
    assert report.actually_affected
    assert report.max_depth <= len(graph.nodes)


def test_summary_contains_headline_numbers():
    report = analyze(build_diamond(),
                     Change("a", ChangeKind.TOOL_UPDATE, 1.0))
    text = report.summary()
    assert "Actually affected: 3" in text
    assert "Blast radius: 0.750" in text
