"""The system graph: nodes, edges, reachability, JSON load/save."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .models import Edge, Node


class SystemGraph:
    """A directed dependency graph of an agent system."""

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._successors: Dict[str, List[Edge]] = {}
        self._predecessors: Dict[str, List[Edge]] = {}

    # -- construction -------------------------------------------------

    def add_node(self, node: Node) -> "SystemGraph":
        if node.node_id in self.nodes:
            raise ValueError("duplicate node id: " + node.node_id)
        self.nodes[node.node_id] = node
        self._successors.setdefault(node.node_id, [])
        self._predecessors.setdefault(node.node_id, [])
        return self

    def add_edge(self, edge: Edge) -> "SystemGraph":
        if edge.source not in self.nodes:
            raise ValueError("unknown edge source: " + edge.source)
        if edge.target not in self.nodes:
            raise ValueError("unknown edge target: " + edge.target)
        self.edges.append(edge)
        self._successors[edge.source].append(edge)
        self._predecessors[edge.target].append(edge)
        return self

    # -- queries ------------------------------------------------------

    def successors(self, node_id: str) -> List[str]:
        return [e.target for e in self._successors.get(node_id, [])]

    def predecessors(self, node_id: str) -> List[str]:
        return [e.source for e in self._predecessors.get(node_id, [])]

    def out_edges(self, node_id: str) -> List[Edge]:
        return list(self._successors.get(node_id, []))

    def in_edges(self, node_id: str) -> List[Edge]:
        return list(self._predecessors.get(node_id, []))

    def forward_closure(self, start: str) -> Dict[str, int]:
        """All nodes reachable from ``start``, with hop distance.

        Cycles are safe: each node is visited once, at its shortest
        distance. The start node itself is returned at distance 0.
        """
        if start not in self.nodes:
            raise ValueError("unknown node: " + start)
        distance: Dict[str, int] = {start: 0}
        frontier = [start]
        while frontier:
            current = frontier.pop(0)
            for target in self.successors(current):
                if target not in distance:
                    distance[target] = distance[current] + 1
                    frontier.append(target)
        return distance

    def backward_closure(self, start: str) -> Dict[str, int]:
        """All nodes that can reach ``start`` — the reverse question."""
        if start not in self.nodes:
            raise ValueError("unknown node: " + start)
        distance: Dict[str, int] = {start: 0}
        frontier = [start]
        while frontier:
            current = frontier.pop(0)
            for source in self.predecessors(current):
                if source not in distance:
                    distance[source] = distance[current] + 1
                    frontier.append(source)
        return distance

    def has_cycle(self) -> bool:
        """True if the graph contains a directed cycle."""
        WHITE, GREY, BLACK = 0, 1, 2
        colour = {node_id: WHITE for node_id in self.nodes}

        def visit(node_id: str) -> bool:
            colour[node_id] = GREY
            for target in self.successors(node_id):
                if colour[target] == GREY:
                    return True
                if colour[target] == WHITE and visit(target):
                    return True
            colour[node_id] = BLACK
            return False

        for node_id in self.nodes:
            if colour[node_id] == WHITE and visit(node_id):
                return True
        return False

    # -- serialisation ------------------------------------------------

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "SystemGraph":
        graph = cls(name=str(data.get("name", "")))
        for node_data in data.get("nodes", []):
            graph.add_node(Node.from_dict(node_data))
        for edge_data in data.get("edges", []):
            graph.add_edge(Edge.from_dict(edge_data))
        return graph

    @classmethod
    def load(cls, path: str) -> "SystemGraph":
        with open(path, "r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2)
            handle.write("\n")
