"""Tests for dependency-safe restoration ordering and iterative DFS cycle detection."""

from pathlib import Path
import networkx as nx
import pytest
from planner.core.graph import Network
from planner.core.loader import load_network_from_file
from planner.core.models import Edge, Node
from planner.core.restore import restore_order

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_worked_example_restore_order():
    """Verify that topological order satisfies all dependency requirements in worked_example."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")

    res = restore_order(net)
    assert res.ok is True
    assert res.cycle is None
    assert res.order is not None

    order = res.order
    assert len(order) == 7
    assert set(order) == {"LT", "P", "A", "B", "L", "D", "W"}

    # Assert dependency requirements:
    # A requires D -> D must precede A
    assert order.index("D") < order.index("A")
    # A requires L -> L must precede A
    assert order.index("L") < order.index("A")
    # W requires A -> A must precede W
    assert order.index("A") < order.index("W")


def test_cycle_detection():
    """Verify detection and diagnostic reporting of circular dependencies."""
    nodes = {
        "S1": Node(id="S1", name="Service 1", type="app", criticality=5),
        "S2": Node(id="S2", name="Service 2", type="app", criticality=5),
        "S3": Node(id="S3", name="Service 3", type="database", criticality=8),
    }
    # S1 -> S2 -> S3 -> S1
    edges = {
        "d1": Edge(id="d1", source="S1", target="S2", kind="dependency"),
        "d2": Edge(id="d2", source="S2", target="S3", kind="dependency"),
        "d3": Edge(id="d3", source="S3", target="S1", kind="dependency"),
    }
    net = Network(nodes=nodes, edges=edges)

    res = restore_order(net)
    assert res.ok is False
    assert res.order is None
    assert res.cycle is not None
    assert len(res.cycle) >= 3
    # Cycle must start and end at the same node
    assert res.cycle[0] == res.cycle[-1]
    assert "Circular dependency detected" in res.explanation


def test_demo_network_restore_order():
    """Verify restore order across all 20 nodes and 11 dependencies in demo_network.json."""
    net = load_network_from_file(DATA_DIR / "demo_network.json")

    res = restore_order(net)
    assert res.ok is True
    assert res.cycle is None
    assert res.order is not None
    assert len(res.order) == 20

    # Every dependency edge source -> target must have target preceding source
    order = res.order
    for edge in net.edges.values():
        if edge.kind == "dependency":
            source_idx = order.index(edge.source)
            target_idx = order.index(edge.target)
            assert target_idx < source_idx, (
                f"Dependency violated: {edge.source} requires {edge.target}, "
                f"but {edge.source} is at index {source_idx} while {edge.target} is at {target_idx}"
            )


def test_deep_chain_no_recursion_limit():
    """Verify iterative DFS handles 2,500 chained nodes without RecursionError."""
    chain_length = 2500
    nodes = {
        f"N_{i}": Node(id=f"N_{i}", name=f"Node {i}", type="app", criticality=5)
        for i in range(chain_length)
    }
    # Chain: N_0 -> N_1 -> N_2 -> ... -> N_{chain_length-1}
    # (N_0 requires N_1, which requires N_2, ...)
    edges = {
        f"dep_{i}": Edge(id=f"dep_{i}", source=f"N_{i}", target=f"N_{i+1}", kind="dependency")
        for i in range(chain_length - 1)
    }
    net = Network(nodes=nodes, edges=edges)

    res = restore_order(net)
    assert res.ok is True
    assert res.order is not None
    assert len(res.order) == chain_length

    # N_{chain_length-1} has no dependencies, so it must be first
    assert res.order[0] == f"N_{chain_length - 1}"
    # N_0 requires everything, so it must be last
    assert res.order[-1] == "N_0"


def test_cross_verify_restore_order_with_networkx():
    """Verify absence of cycles and precedence against NetworkX topological sort."""
    net = load_network_from_file(DATA_DIR / "demo_network.json")

    # In restore graph: if u requires v, then v must be restored BEFORE u (v -> u)
    G = nx.DiGraph()
    for nid in net.nodes:
        G.add_node(nid)
    for edge in net.edges.values():
        if edge.kind == "dependency":
            G.add_edge(edge.target, edge.source)

    assert nx.is_directed_acyclic_graph(G)

    res = restore_order(net)
    assert res.ok is True

    # Validate that our order is a valid topological sort in G
    pos = {node: i for i, node in enumerate(res.order)}
    for u, v in G.edges():
        assert pos[u] < pos[v]
