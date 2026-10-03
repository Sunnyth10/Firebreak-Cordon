"""Performance benchmark tests verifying algorithm scalability on 100 to 1,000 node graphs."""

import time
import pytest
from planner.core.blast import blast_radius
from planner.core.graph import Network
from planner.core.models import Edge, Node
from planner.core.paths import most_probable_path
from planner.core.restore import restore_order


def generate_synthetic_graph(node_count: int, edge_density: float = 2.0) -> Network:
    """Generate a deterministic synthetic network with layered topology."""
    nodes = {
        f"N_{i}": Node(
            id=f"N_{i}",
            name=f"Asset {i}",
            type="app" if i % 3 == 0 else "endpoint",
            criticality=(i % 10) + 1,
        )
        for i in range(node_count)
    }

    edges = {}
    edge_idx = 0

    # 1. Forward lateral network edges (layered)
    for i in range(node_count - 1):
        target = min(i + 1, node_count - 1)
        eid = f"net_{edge_idx}"
        edges[eid] = Edge(
            id=eid,
            source=f"N_{i}",
            target=f"N_{target}",
            kind="network",
            probability=0.85,
        )
        edge_idx += 1

        # Additional cross edges for density
        if i + 3 < node_count and i % 2 == 0:
            eid2 = f"net_{edge_idx}"
            edges[eid2] = Edge(
                id=eid2,
                source=f"N_{i}",
                target=f"N_{i+3}",
                kind="network",
                probability=0.75,
            )
            edge_idx += 1

    # 2. Dependency edges (acyclic DAG: higher index requires lower index)
    for i in range(1, node_count):
        if i % 3 == 0:
            target = i // 2
            eid_dep = f"dep_{edge_idx}"
            edges[eid_dep] = Edge(
                id=eid_dep,
                source=f"N_{i}",
                target=f"N_{target}",
                kind="dependency",
            )
            edge_idx += 1

    return Network(nodes=nodes, edges=edges)


def test_benchmark_blast_radius_100_nodes():
    net = generate_synthetic_graph(100)
    t0 = time.perf_counter()
    blast = blast_radius(net, "N_0")
    elapsed = time.perf_counter() - t0

    assert len(blast) > 0
    # Must complete in under 50ms
    assert elapsed < 0.05, f"Blast radius on 100 nodes took {elapsed:.4f}s"


def test_benchmark_blast_radius_1000_nodes():
    net = generate_synthetic_graph(1000)
    t0 = time.perf_counter()
    blast = blast_radius(net, "N_0")
    elapsed = time.perf_counter() - t0

    assert len(blast) > 0
    # Must complete in under 150ms
    assert elapsed < 0.15, f"Blast radius on 1000 nodes took {elapsed:.4f}s"


def test_benchmark_dijkstra_shortest_path_1000_nodes():
    net = generate_synthetic_graph(1000)
    t0 = time.perf_counter()
    path_res = most_probable_path(net, "N_0", "N_999")
    elapsed = time.perf_counter() - t0

    assert path_res is not None
    assert path_res.nodes[0] == "N_0"
    assert path_res.nodes[-1] == "N_999"
    # Dijkstra on 1,000 nodes must complete in under 50ms
    assert elapsed < 0.05, f"Dijkstra on 1000 nodes took {elapsed:.4f}s"


def test_benchmark_iterative_dfs_topological_sort_1000_nodes():
    net = generate_synthetic_graph(1000)
    t0 = time.perf_counter()
    res = restore_order(net)
    elapsed = time.perf_counter() - t0

    assert res.ok is True
    assert len(res.order) == 1000
    # Iterative DFS topological sort on 1,000 nodes must complete in under 50ms
    assert elapsed < 0.05, f"Topological sort on 1000 nodes took {elapsed:.4f}s"
