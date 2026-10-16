"""Graph backend for the pipeline simulator.

Nodes represent locations (cities, ports, hubs) and edges represent the
pipelines or trade routes connecting them.
"""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass
class Node:
    id: str
    name: str = ""
    region: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            self.name = self.id


@dataclass
class Edge:
    source: str
    target: str
    weight: float = 1.0       # e.g. distance or transport cost
    capacity: float = float("inf")  # e.g. max throughput per tick
    attributes: dict[str, Any] = field(default_factory=dict)

    def other(self, node_id: str) -> str:
        """Return the endpoint opposite to ``node_id``."""
        if node_id == self.source:
            return self.target
        if node_id == self.target:
            return self.source
        raise ValueError(f"{node_id!r} is not an endpoint of this edge")


class Graph:
    """A weighted graph stored as an adjacency map.

    Undirected by default; pass ``directed=True`` for one-way pipelines.
    """

    def __init__(self, directed: bool = False) -> None:
        self.directed = directed
        self._nodes: dict[str, Node] = {}
        # _adj[u][v] -> Edge from u to v
        self._adj: dict[str, dict[str, Edge]] = {}

    # ------------------------------------------------------------------ nodes

    def add_node(self, node_id: str, **kwargs: Any) -> Node:
        if node_id in self._nodes:
            raise ValueError(f"Node {node_id!r} already exists")
        node = Node(node_id, **kwargs)
        self._nodes[node_id] = node
        self._adj[node_id] = {}
        return node

    def remove_node(self, node_id: str) -> None:
        self._require(node_id)
        for other in list(self._adj):
            self._adj[other].pop(node_id, None)
        del self._adj[node_id]
        del self._nodes[node_id]

    def get_node(self, node_id: str) -> Node:
        self._require(node_id)
        return self._nodes[node_id]

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    @property
    def nodes(self) -> list[Node]:
        return list(self._nodes.values())

    # ------------------------------------------------------------------ edges

    def add_edge(self, source: str, target: str, **kwargs: Any) -> Edge:
        self._require(source)
        self._require(target)
        if source == target:
            raise ValueError("Self-loops are not allowed")
        if target in self._adj[source]:
            raise ValueError(f"Edge {source!r} -> {target!r} already exists")
        edge = Edge(source, target, **kwargs)
        self._adj[source][target] = edge
        if not self.directed:
            self._adj[target][source] = edge
        return edge

    def remove_edge(self, source: str, target: str) -> None:
        if not self.has_edge(source, target):
            raise KeyError(f"No edge {source!r} -> {target!r}")
        del self._adj[source][target]
        if not self.directed:
            del self._adj[target][source]

    def get_edge(self, source: str, target: str) -> Edge:
        if not self.has_edge(source, target):
            raise KeyError(f"No edge {source!r} -> {target!r}")
        return self._adj[source][target]

    def has_edge(self, source: str, target: str) -> bool:
        return target in self._adj.get(source, {})

    @property
    def edges(self) -> list[Edge]:
        # Deduplicate undirected edges, which are stored under both endpoints.
        seen: dict[int, Edge] = {}
        for targets in self._adj.values():
            for edge in targets.values():
                seen.setdefault(id(edge), edge)
        return list(seen.values())

    def neighbors(self, node_id: str) -> list[str]:
        self._require(node_id)
        return list(self._adj[node_id])

    def degree(self, node_id: str) -> int:
        self._require(node_id)
        return len(self._adj[node_id])

    # -------------------------------------------------------------- traversal

    def bfs(self, start: str) -> Iterator[str]:
        """Yield node ids reachable from ``start`` in breadth-first order."""
        self._require(start)
        visited = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            yield current
            for nxt in self._adj[current]:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)

    def is_connected(self) -> bool:
        """True if every node can reach every other node.

        For directed graphs this checks strong connectivity.
        """
        if not self._nodes:
            return True
        start = next(iter(self._nodes))
        if sum(1 for _ in self.bfs(start)) != len(self._nodes):
            return False
        if not self.directed:
            return True
        return sum(1 for _ in self.reversed().bfs(start)) == len(self._nodes)

    def connected_components(self) -> list[set[str]]:
        """Return groups of nodes connected to each other (ignores direction)."""
        undirected = self if not self.directed else self.as_undirected()
        remaining = set(self._nodes)
        components: list[set[str]] = []
        while remaining:
            component = set(undirected.bfs(next(iter(remaining))))
            components.append(component)
            remaining -= component
        return components

    def shortest_path(self, source: str, target: str) -> tuple[float, list[str]]:
        """Dijkstra's algorithm on edge weights.

        Returns ``(total_weight, [source, ..., target])``.
        Raises ``ValueError`` if ``target`` is unreachable.
        """
        self._require(source)
        self._require(target)
        dist = {source: 0.0}
        prev: dict[str, str] = {}
        heap = [(0.0, source)]
        while heap:
            d, current = heapq.heappop(heap)
            if current == target:
                break
            if d > dist[current]:
                continue
            for nxt, edge in self._adj[current].items():
                nd = d + edge.weight
                if nd < dist.get(nxt, float("inf")):
                    dist[nxt] = nd
                    prev[nxt] = current
                    heapq.heappush(heap, (nd, nxt))
        if target not in dist:
            raise ValueError(f"No path from {source!r} to {target!r}")
        path = [target]
        while path[-1] != source:
            path.append(prev[path[-1]])
        path.reverse()
        return dist[target], path

    # ---------------------------------------------------------------- helpers

    def reversed(self) -> Graph:
        """Return a copy with every directed edge flipped."""
        g = Graph(directed=self.directed)
        for node in self._nodes.values():
            g.add_node(node.id, name=node.name, region=node.region,
                       attributes=dict(node.attributes))
        for e in self.edges:
            g.add_edge(e.target, e.source, weight=e.weight,
                       capacity=e.capacity, attributes=dict(e.attributes))
        return g

    def as_undirected(self) -> Graph:
        g = Graph(directed=False)
        for node in self._nodes.values():
            g.add_node(node.id, name=node.name, region=node.region,
                       attributes=dict(node.attributes))
        for e in self.edges:
            if not g.has_edge(e.source, e.target):
                g.add_edge(e.source, e.target, weight=e.weight,
                           capacity=e.capacity, attributes=dict(e.attributes))
        return g

    def to_dict(self) -> dict[str, Any]:
        return {
            "directed": self.directed,
            "nodes": [vars(n) for n in self._nodes.values()],
            "edges": [vars(e) for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Graph:
        g = cls(directed=data.get("directed", False))
        for n in data["nodes"]:
            n = dict(n)
            g.add_node(n.pop("id"), **n)
        for e in data["edges"]:
            e = dict(e)
            g.add_edge(e.pop("source"), e.pop("target"), **e)
        return g

    def _require(self, node_id: str) -> None:
        if node_id not in self._nodes:
            raise KeyError(f"Unknown node {node_id!r}")

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, node_id: object) -> bool:
        return node_id in self._nodes

    def __repr__(self) -> str:
        kind = "directed" if self.directed else "undirected"
        return f"<Graph {kind}: {len(self._nodes)} nodes, {len(self.edges)} edges>"


if __name__ == "__main__":
    g = Graph()
    g.add_node("ALG", name="Algiers", region="North Africa")
    g.add_node("TUN", name="Tunis", region="North Africa")
    g.add_node("ROM", name="Rome", region="Europe")
    g.add_node("ATH", name="Athens", region="Europe")
    g.add_node("BEI", name="Beirut", region="Levant")
    g.add_edge("ALG", "TUN", weight=640)
    g.add_edge("TUN", "ROM", weight=600)
    g.add_edge("ROM", "ATH", weight=1050)
    g.add_edge("ATH", "BEI", weight=1150)
    g.add_edge("TUN", "BEI", weight=2300)

    print(g)
    print("Connected:", g.is_connected())
    print("Algiers -> Beirut:", g.shortest_path("ALG", "BEI"))
    assert Graph.from_dict(g.to_dict()).to_dict() == g.to_dict()
