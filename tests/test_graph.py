"""Tests for the system graph."""

import tempfile
from pathlib import Path

import pytest

from cascadescope.graph import SystemGraph
from cascadescope.models import Edge, Node, NodeKind


def build_chain():
    graph = SystemGraph("chain")
    for node_id in ("a", "b", "c", "d"):
        graph.add_node(Node(node_id, NodeKind.TOOL))
    graph.add_edge(Edge("a", "b"))
    graph.add_edge(Edge("b", "c"))
    graph.add_edge(Edge("c", "d"))
    return graph


def test_forward_closure_reports_hop_distances():
    graph = build_chain()
    assert graph.forward_closure("a") == {"a": 0, "b": 1, "c": 2, "d": 3}


def test_forward_closure_of_leaf_is_just_itself():
    graph = build_chain()
    assert graph.forward_closure("d") == {"d": 0}


def test_backward_closure():
    graph = build_chain()
    assert graph.backward_closure("d") == {"d": 0, "c": 1, "b": 2, "a": 3}


def test_closure_rejects_unknown_node():
    graph = build_chain()
    with pytest.raises(ValueError):
        graph.forward_closure("zzz")


def test_cycles_do_not_hang_closure():
    graph = SystemGraph("cycle")
    for node_id in ("a", "b", "c"):
        graph.add_node(Node(node_id, NodeKind.AGENT))
    graph.add_edge(Edge("a", "b"))
    graph.add_edge(Edge("b", "c"))
    graph.add_edge(Edge("c", "a"))
    assert graph.forward_closure("a") == {"a": 0, "b": 1, "c": 2}
    assert graph.has_cycle()


def test_acyclic_graph_has_no_cycle():
    assert not build_chain().has_cycle()


def test_duplicate_node_rejected():
    graph = SystemGraph("dup")
    graph.add_node(Node("a", NodeKind.TOOL))
    with pytest.raises(ValueError):
        graph.add_node(Node("a", NodeKind.TOOL))


def test_edge_to_unknown_node_rejected():
    graph = SystemGraph("bad")
    graph.add_node(Node("a", NodeKind.TOOL))
    with pytest.raises(ValueError):
        graph.add_edge(Edge("a", "ghost"))
    with pytest.raises(ValueError):
        graph.add_edge(Edge("ghost", "a"))


def test_successors_and_predecessors():
    graph = build_chain()
    assert graph.successors("b") == ["c"]
    assert graph.predecessors("c") == ["b"]
    assert graph.successors("d") == []


def test_save_and_load_round_trip():
    graph = build_chain()
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "g.json")
        graph.save(path)
        loaded = SystemGraph.load(path)
    assert loaded.name == "chain"
    assert set(loaded.nodes) == {"a", "b", "c", "d"}
    assert len(loaded.edges) == 3
    assert loaded.forward_closure("a") == {"a": 0, "b": 1, "c": 2, "d": 3}


def test_load_real_clinic_system():
    graph = SystemGraph.load("data/systems/clinic.json")
    assert len(graph.nodes) == 22
    assert len(graph.edges) == 28


def test_load_real_phm_system_has_a_cycle():
    # agent_planner -> plan_maintenance -> ... -> agent_planner
    graph = SystemGraph.load("data/systems/phm.json")
    assert len(graph.nodes) == 24
    assert graph.has_cycle()
    # ...and the closure still terminates.
    assert len(graph.forward_closure("agent_monitor")) > 10
