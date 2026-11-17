"""Tests for the data model (Node, Edge, Change)."""

import pytest

from cascadescope.models import (
    ALL_CHANGE_KINDS,
    Change,
    ChangeKind,
    Edge,
    Node,
    NodeKind,
)


def test_node_defaults_label_to_id():
    node = Node("tool_x", NodeKind.TOOL)
    assert node.label == "tool_x"


def test_node_rejects_empty_id():
    with pytest.raises(ValueError):
        Node("", NodeKind.TOOL)


def test_node_kind_coerced_from_string():
    node = Node("m", "memory")
    assert node.kind == NodeKind.MEMORY


def test_node_round_trips_through_dict():
    node = Node("t", NodeKind.TOOL, "My tool",
                {"type": "scale", "factor": 0.5})
    restored = Node.from_dict(node.to_dict())
    assert restored.node_id == "t"
    assert restored.transfer == {"type": "scale", "factor": 0.5}


def test_edge_defaults_gate_to_all_kinds():
    edge = Edge("a", "b")
    assert edge.gate == ALL_CHANGE_KINDS
    assert edge.allows("model_swap")
    assert edge.allows("memory_edit")


def test_edge_rejects_bad_attenuation():
    with pytest.raises(ValueError):
        Edge("a", "b", attenuation=1.5)
    with pytest.raises(ValueError):
        Edge("a", "b", attenuation=-0.1)


def test_edge_rejects_unknown_gate_kind():
    with pytest.raises(ValueError):
        Edge("a", "b", gate=["teleport"])


def test_edge_rejects_empty_endpoints():
    with pytest.raises(ValueError):
        Edge("", "b")
    with pytest.raises(ValueError):
        Edge("a", "")


def test_edge_round_trips_through_dict():
    edge = Edge("a", "b", "reads", 0.7, ["memory_edit"])
    restored = Edge.from_dict(edge.to_dict())
    assert restored.attenuation == 0.7
    assert restored.gate == ["memory_edit"]


def test_change_defaults_description():
    change = Change("n", ChangeKind.TOOL_UPDATE)
    assert "tool_update" in change.description
    assert change.severity == 1.0


def test_change_rejects_bad_severity():
    with pytest.raises(ValueError):
        Change("n", ChangeKind.TOOL_UPDATE, 0.0)
    with pytest.raises(ValueError):
        Change("n", ChangeKind.TOOL_UPDATE, 1.5)


def test_change_kind_coerced_from_string():
    change = Change("n", "model_swap", 0.8)
    assert change.kind == ChangeKind.MODEL_SWAP


def test_change_round_trips_through_dict():
    change = Change("m", ChangeKind.MEMORY_EDIT, 1.0, "edit", ["k1"])
    restored = Change.from_dict(change.to_dict())
    assert restored.keys == ["k1"]
    assert restored.severity == 1.0
