"""Data model: nodes, edges, and changes in an agent system.

A system is a directed graph. Nodes are the things that can change
or be affected (tools, memory records, plans, decisions, agents,
prompts, models, configs). Edges are dependency relations: the
target consumes something the source produces. An edge carries an
attenuation (how much of a change survives the hop) and a gate (which
change kinds are allowed to propagate across it at all).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class NodeKind(str, Enum):
    TOOL = "tool"
    MEMORY = "memory"
    PLAN = "plan"
    DECISION = "decision"
    AGENT = "agent"
    PROMPT = "prompt"
    MODEL = "model"
    CONFIG = "config"


class ChangeKind(str, Enum):
    TOOL_UPDATE = "tool_update"
    MEMORY_EDIT = "memory_edit"
    PROMPT_CHANGE = "prompt_change"
    MODEL_SWAP = "model_swap"
    CONFIG_CHANGE = "config_change"


# Every change kind, for edges that propagate everything.
ALL_CHANGE_KINDS = [k.value for k in ChangeKind]


@dataclass
class Node:
    """One element of an agent system.

    ``transfer`` describes how the node transforms an incoming change
    delta into an outgoing delta, used only by the oracle simulator
    (see simulate.py). Types:

    - ``passthrough``: out = factor * in (default factor 1.0).
    - ``scale``: out = factor * in, factor < 1 damps the change.
    - ``threshold``: out = in if in >= threshold else 0.0 — a
      decision node that only flips when the change is big enough.
    - ``keyed``: out = in if the change touches one of ``keys``
      (e.g. a memory reader only sees edits to the keys it reads),
      else 0.0.
    - ``absorbing``: out = 0.0 always — a validator/normaliser that
      swallows the change.
    """

    node_id: str
    kind: NodeKind
    label: str = ""
    transfer: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id must not be empty")
        if not isinstance(self.kind, NodeKind):
            self.kind = NodeKind(self.kind)
        if not self.label:
            self.label = self.node_id
        if not isinstance(self.transfer, dict):
            raise ValueError("transfer must be a dict")

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.node_id,
            "kind": self.kind.value,
            "label": self.label,
            "transfer": self.transfer,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Node":
        return cls(
            node_id=str(data["id"]),
            kind=NodeKind(str(data["kind"])),
            label=str(data.get("label", data["id"])),
            transfer=dict(data.get("transfer", {}) or {}),
        )


@dataclass
class Edge:
    """A dependency: ``target`` consumes something ``source`` produces.

    ``attenuation`` in [0, 1]: the fraction of a change delta that
    survives this hop. ``gate``: the change kinds allowed to
    propagate across this edge at all. An empty gate blocks
    everything; ``ALL_CHANGE_KINDS`` propagates everything.
    """

    source: str
    target: str
    edge_type: str = "depends_on"
    attenuation: float = 1.0
    gate: List[str] = field(default_factory=lambda: list(ALL_CHANGE_KINDS))

    def __post_init__(self) -> None:
        if not self.source or not self.target:
            raise ValueError("edge endpoints must not be empty")
        if not 0.0 <= self.attenuation <= 1.0:
            raise ValueError("attenuation must be in [0, 1]")
        for kind in self.gate:
            if kind not in ALL_CHANGE_KINDS:
                raise ValueError("unknown change kind in gate: " + str(kind))

    def allows(self, change_kind: str) -> bool:
        return change_kind in self.gate

    def to_dict(self) -> Dict[str, object]:
        return {
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type,
            "attenuation": self.attenuation,
            "gate": list(self.gate),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Edge":
        return cls(
            source=str(data["source"]),
            target=str(data["target"]),
            edge_type=str(data.get("edge_type", "depends_on")),
            attenuation=float(data.get("attenuation", 1.0)),
            gate=list(data.get("gate", ALL_CHANGE_KINDS)),
        )


@dataclass
class Change:
    """A change applied to one node of the system.

    ``severity`` in (0, 1]: how large the change is at its origin
    (1.0 = the node's output is fully replaced). ``keys``: for a
    memory edit, the record keys touched; used by ``keyed`` oracle
    transfers and by the analyzer's key gate.
    """

    node_id: str
    kind: ChangeKind
    severity: float = 1.0
    description: str = ""
    keys: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id must not be empty")
        if not isinstance(self.kind, ChangeKind):
            self.kind = ChangeKind(self.kind)
        if not 0.0 < self.severity <= 1.0:
            raise ValueError("severity must be in (0, 1]")
        if not self.description:
            self.description = self.kind.value + " on " + self.node_id

    def to_dict(self) -> Dict[str, object]:
        return {
            "node_id": self.node_id,
            "kind": self.kind.value,
            "severity": self.severity,
            "description": self.description,
            "keys": list(self.keys),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Change":
        return cls(
            node_id=str(data["node_id"]),
            kind=ChangeKind(str(data["kind"])),
            severity=float(data.get("severity", 1.0)),
            description=str(data.get("description", "")),
            keys=list(data.get("keys", [])),
        )
