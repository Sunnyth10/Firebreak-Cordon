"""Plain data container for network graph representation.

Zero algorithms: only storage, adjacency indices, and functional transformations.
"""

from __future__ import annotations

from typing import Any
from .models import Edge, EdgeKind, Incident, NetworkMeta, Node


class Network:
    """In-memory representation of network connectivity and functional dependencies."""

    def __init__(
        self,
        meta: NetworkMeta | None = None,
        nodes: dict[str, Node] | None = None,
        edges: dict[str, Edge] | None = None,
        incidents: dict[str, Incident] | None = None,
    ) -> None:
        self.meta = meta or NetworkMeta()
        self.nodes: dict[str, Node] = nodes or {}
        self.edges: dict[str, Edge] = edges or {}
        self.incidents: dict[str, Incident] = incidents or {}

        # Adjacency structures
        self.network_adj: dict[str, list[tuple[str, float]]] = {nid: [] for nid in self.nodes}
        self.dependency_adj: dict[str, list[str]] = {nid: [] for nid in self.nodes}

        self._build_adjacencies()

    def _build_adjacencies(self) -> None:
        for edge in self.edges.values():
            if edge.kind == EdgeKind.NETWORK.value or edge.kind == EdgeKind.NETWORK:
                if edge.source in self.network_adj:
                    prob = edge.probability if edge.probability is not None else 1.0
                    self.network_adj[edge.source].append((edge.target, prob))
            elif edge.kind == EdgeKind.DEPENDENCY.value or edge.kind == EdgeKind.DEPENDENCY:
                if edge.source in self.dependency_adj:
                    self.dependency_adj[edge.source].append(edge.target)

    def get_node(self, node_id: str) -> Node | None:
        """Retrieve node by ID or None if not found."""
        return self.nodes.get(node_id)

    def neighbors(self, node_id: str, kind: str = "network") -> list[Any]:
        """Return neighbor references for node_id under specified edge kind.

        For kind='network': returns list of tuples (target_node_id, probability).
        For kind='dependency': returns list of target_node_id strings.
        """
        if kind == EdgeKind.NETWORK.value or kind == EdgeKind.NETWORK:
            return list(self.network_adj.get(node_id, []))
        if kind == EdgeKind.DEPENDENCY.value or kind == EdgeKind.DEPENDENCY:
            return list(self.dependency_adj.get(node_id, []))
        raise ValueError(f"Unknown edge kind: '{kind}'. Expected 'network' or 'dependency'.")

    def without_node(self, node_id: str) -> Network:
        """Return a copy of the network with the node and all incident edges removed.

        Pure transformation: does not mutate self.
        """
        if node_id not in self.nodes:
            # If node not present, return shallow copy
            return Network(
                meta=self.meta,
                nodes=dict(self.nodes),
                edges=dict(self.edges),
                incidents=dict(self.incidents),
            )

        new_nodes = {nid: n for nid, n in self.nodes.items() if nid != node_id}
        new_edges = {
            eid: e
            for eid, e in self.edges.items()
            if e.source != node_id and e.target != node_id
        }
        new_incidents = {
            iid: inc for iid, inc in self.incidents.items() if inc.node_id != node_id
        }

        return Network(
            meta=self.meta,
            nodes=new_nodes,
            edges=new_edges,
            incidents=new_incidents,
        )

    def is_critical(self, node_id: str) -> bool:
        """Check if node criticality satisfies or exceeds critical_threshold."""
        node = self.get_node(node_id)
        if not node:
            return False
        return node.criticality >= self.meta.critical_threshold
