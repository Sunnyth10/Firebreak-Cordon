"""Tests for blast radius calculation engine against hand-calculated and networkx baselines."""

import math
from pathlib import Path
import networkx as nx
import pytest
from planner.core.blast import blast_radius
from planner.core.graph import Network
from planner.core.loader import load_network_from_file
from planner.core.models import Edge, Node

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_worked_example_blast_radius_lt():
    """Verify exact blast radius values for node LT in worked_example.json."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")
    blast = blast_radius(net, "LT")

    assert set(blast.keys()) == {"L", "A", "D", "B"}

    # Hops
    assert blast["L"]["hops"] == 1
    assert blast["A"]["hops"] == 1
    assert blast["D"]["hops"] == 2
    assert blast["B"]["hops"] == 2

    # Reach probabilities
    assert blast["L"]["reach_probability"] == 0.80
    assert blast["A"]["reach_probability"] == 0.40
    # D via L is 0.8 * 0.7 = 0.56 (better than via A: 0.4 * 0.6 = 0.24)
    assert blast["D"]["reach_probability"] == 0.56
    # B via L is 0.8 * 0.5 = 0.40
    assert blast["B"]["reach_probability"] == 0.40


def test_worked_example_isolated_printer():
    """Printer P has no network edges and thus empty blast radius."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")
    blast_p = blast_radius(net, "P")
    assert blast_p == {}

    # Node W also has no outgoing network edges
    blast_w = blast_radius(net, "W")
    assert blast_w == {}


def test_worked_example_blast_radius_after_isolation():
    """Verify recomputed blast radius when node L is isolated."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")
    net_isolated = net.without_node("L")

    blast = blast_radius(net_isolated, "LT")

    # With L isolated, LT can only reach A and D (via A)
    assert set(blast.keys()) == {"A", "D"}
    assert blast["A"]["hops"] == 1
    assert blast["A"]["reach_probability"] == 0.40
    assert blast["D"]["hops"] == 2
    # D via A is 0.4 * 0.6 = 0.24
    assert blast["D"]["reach_probability"] == 0.24


def test_demo_network_blast_radius():
    """Verify blast radius for LAPTOP-ENG and PRINTER-HR in demo_network.json."""
    net = load_network_from_file(DATA_DIR / "demo_network.json")

    # PRINTER-HR is isolated
    assert blast_radius(net, "PRINTER-HR") == {}

    # LAPTOP-ENG
    blast = blast_radius(net, "LAPTOP-ENG")
    expected_hops = {
        "VPN-GATEWAY": 1,
        "AUTH-AD": 2,
        "INTERNAL-DNS": 2,
        "BASTION-HOST": 3,
        "APP-01": 3,
        "MONITOR-SIEM": 3,
        "DB-PRIMARY": 4,
        "DB-REPLICA": 5,
        "BACKUP-VAULT": 5,
    }
    expected_probs = {
        "VPN-GATEWAY": 0.9000,
        "AUTH-AD": 0.7200,
        "INTERNAL-DNS": 0.7200,
        "BASTION-HOST": 0.5040,
        "APP-01": 0.4320,
        "MONITOR-SIEM": 0.4320,
        "DB-PRIMARY": 0.4284,
        "DB-REPLICA": 0.3856,
        "BACKUP-VAULT": 0.2142,
    }

    assert set(blast.keys()) == set(expected_hops.keys())
    for target in expected_hops:
        assert blast[target]["hops"] == expected_hops[target]
        assert pytest.approx(blast[target]["reach_probability"], abs=1e-4) == expected_probs[target]


def test_blast_radius_cycle_tolerance():
    """Ensure graphs with cycles terminate correctly and find maximum probability."""
    # Graph: X <-> Y (0.8 both ways), Y -> Z (0.5), Z -> Y (0.5)
    nodes = {
        "X": Node(id="X", name="Node X", type="endpoint", criticality=2),
        "Y": Node(id="Y", name="Node Y", type="app", criticality=5),
        "Z": Node(id="Z", name="Node Z", type="database", criticality=8),
    }
    edges = {
        "e1": Edge(id="e1", source="X", target="Y", kind="network", probability=0.8),
        "e2": Edge(id="e2", source="Y", target="X", kind="network", probability=0.8),
        "e3": Edge(id="e3", source="Y", target="Z", kind="network", probability=0.5),
        "e4": Edge(id="e4", source="Z", target="Y", kind="network", probability=0.5),
    }
    net = Network(nodes=nodes, edges=edges)

    blast = blast_radius(net, "X")
    assert "Y" in blast
    assert "Z" in blast
    assert blast["Y"]["hops"] == 1
    assert blast["Y"]["reach_probability"] == 0.8
    assert blast["Z"]["hops"] == 2
    assert blast["Z"]["reach_probability"] == 0.40  # 0.8 * 0.5


def test_blast_radius_nonexistent_node():
    net = load_network_from_file(DATA_DIR / "worked_example.json")
    assert blast_radius(net, "NON_EXISTENT_NODE") == {}


def test_cross_verify_with_networkx():
    """Cross-verify blast radius calculation against NetworkX reference implementation."""
    net = load_network_from_file(DATA_DIR / "demo_network.json")

    # Build reference NetworkX directed graph
    nx_graph = nx.DiGraph()
    for node in net.nodes.values():
        nx_graph.add_node(node.id)

    for edge in net.edges.values():
        if edge.kind == "network":
            # Additive cost: -ln(p)
            w = -math.log(edge.probability)
            nx_graph.add_edge(edge.source, edge.target, weight=w)

    for source in ["LAPTOP-ENG", "LAPTOP-SALES", "DMZ-FIREWALL", "PRINTER-HR"]:
        custom_blast = blast_radius(net, source)

        # NetworkX reference
        nx_reachable = nx.descendants(nx_graph, source)
        assert set(custom_blast.keys()) == nx_reachable

        for target in nx_reachable:
            # Unweighted shortest path for hops
            nx_hops = nx.shortest_path_length(nx_graph, source, target)
            assert custom_blast[target]["hops"] == nx_hops

            # Weighted shortest path for probability
            nx_dist = nx.shortest_path_length(nx_graph, source, target, weight="weight")
            nx_prob = round(math.exp(-nx_dist), 4)
            assert pytest.approx(custom_blast[target]["reach_probability"], abs=1e-4) == nx_prob
