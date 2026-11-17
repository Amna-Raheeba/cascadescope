"""Tests for the oracle simulator and analyzer scoring."""

import pytest

from cascadescope.analyze import analyze
from cascadescope.graph import SystemGraph
from cascadescope.models import Change, ChangeKind, Edge, Node, NodeKind
from cascadescope.simulate import oracle_affected, score_analyzer


def build_keyed_system():
    graph = SystemGraph("keyed")
    graph.add_node(Node("mem", NodeKind.MEMORY, transfer={
        "type": "keyed", "keys": ["dosage"]}))
    graph.add_node(Node("reader", NodeKind.TOOL, transfer={
        "type": "keyed", "keys": ["dosage"]}))
    graph.add_node(Node("plan", NodeKind.PLAN))
    graph.add_edge(Edge("mem", "reader"))
    graph.add_edge(Edge("reader", "plan"))
    return graph


def test_oracle_propagates_matching_key():
    graph = build_keyed_system()
    result = oracle_affected(
        graph, Change("mem", ChangeKind.MEMORY_EDIT, 1.0, keys=["dosage"]))
    assert result.affected == ["plan", "reader"]


def test_oracle_blocks_non_matching_key():
    graph = build_keyed_system()
    result = oracle_affected(
        graph, Change("mem", ChangeKind.MEMORY_EDIT, 1.0, keys=["supplier"]))
    assert result.affected == []


def test_oracle_threshold_blocks_small_change():
    graph = SystemGraph("threshold")
    graph.add_node(Node("a", NodeKind.TOOL))
    graph.add_node(Node("d", NodeKind.DECISION, transfer={
        "type": "threshold", "threshold": 0.6}))
    graph.add_node(Node("b", NodeKind.TOOL))
    graph.add_edge(Edge("a", "d"))
    graph.add_edge(Edge("d", "b"))
    small = oracle_affected(graph, Change("a", ChangeKind.TOOL_UPDATE, 0.3))
    assert small.affected == []
    big = oracle_affected(graph, Change("a", ChangeKind.TOOL_UPDATE, 1.0))
    assert big.affected == ["b", "d"]


def test_oracle_absorbing_node_swallows_change():
    graph = SystemGraph("absorbing")
    graph.add_node(Node("a", NodeKind.TOOL))
    graph.add_node(Node("v", NodeKind.TOOL, transfer={"type": "absorbing"}))
    graph.add_node(Node("b", NodeKind.TOOL))
    graph.add_edge(Edge("a", "v"))
    graph.add_edge(Edge("v", "b"))
    result = oracle_affected(graph, Change("a", ChangeKind.TOOL_UPDATE, 1.0))
    assert result.affected == []


def test_oracle_scale_damps_delta():
    graph = SystemGraph("scale")
    graph.add_node(Node("a", NodeKind.TOOL))
    graph.add_node(Node("s", NodeKind.TOOL, transfer={
        "type": "scale", "factor": 0.05}))
    graph.add_node(Node("b", NodeKind.TOOL))
    graph.add_edge(Edge("a", "s"))
    graph.add_edge(Edge("s", "b"))
    result = oracle_affected(graph, Change("a", ChangeKind.TOOL_UPDATE, 1.0))
    assert result.affected == []


def test_oracle_converges_on_cycles():
    graph = SystemGraph.load("data/systems/phm.json")
    result = oracle_affected(
        graph, Change("agent_monitor", ChangeKind.TOOL_UPDATE, 1.0))
    assert result.iterations <= 100
    assert result.affected


def test_oracle_rejects_unknown_node():
    graph = build_keyed_system()
    with pytest.raises(ValueError):
        oracle_affected(graph, Change("ghost", ChangeKind.TOOL_UPDATE, 1.0))


def test_score_analyzer_perfect():
    scores = score_analyzer(["a", "b"], ["a", "b"])
    assert scores["precision"] == 1.0
    assert scores["recall"] == 1.0
    assert scores["f1"] == 1.0


def test_score_analyzer_counts_errors():
    scores = score_analyzer(["a", "b", "c"], ["a", "b"])
    assert scores["precision"] == 0.6667
    assert scores["recall"] == 1.0
    assert scores["false_positives"] == 1
    assert scores["false_negatives"] == 0


def test_score_analyzer_empty_truth():
    scores = score_analyzer([], [])
    assert scores["precision"] == 1.0
    assert scores["recall"] == 1.0


def test_analyzer_never_misses_oracle_on_clinic():
    # Soundness spot-check: on the shipped clinic system the analyzer
    # is a superset of the oracle for every shipped scenario.
    from cascadescope.evaluation import load_scenarios
    graph = SystemGraph.load("data/systems/clinic.json")
    for scenario in load_scenarios("data/scenarios.json"):
        if scenario["system"] != "clinic":
            continue
        change = Change.from_dict(scenario["change"])
        predicted = set(analyze(graph, change).actually_affected)
        truth = set(oracle_affected(graph, change).affected)
        assert truth <= predicted, scenario["id"]
