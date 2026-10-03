"""Tests for network fixture files and data container integrity."""

from pathlib import Path
import pytest
from planner.core.loader import load_network_from_file

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data"


def test_worked_example_fixture_shape():
    """worked_example.json must strictly match the 7-node specification."""
    fixture_path = FIXTURES_DIR / "worked_example.json"
    net = load_network_from_file(fixture_path)

    # Exactly 7 nodes
    assert len(net.nodes) == 7
    expected_nodes = {"LT", "P", "A", "B", "L", "D", "W"}
    assert set(net.nodes.keys()) == expected_nodes

    # Check node attributes
    assert net.nodes["LT"].criticality == 2
    assert net.nodes["LT"].type == "endpoint"
    assert net.nodes["P"].criticality == 1
    assert net.nodes["P"].type == "peripheral"
    assert net.nodes["A"].criticality == 7
    assert net.nodes["A"].type == "app"
    assert net.nodes["B"].criticality == 8
    assert net.nodes["B"].type == "backup"
    assert net.nodes["L"].criticality == 9
    assert net.nodes["L"].type == "auth"
    assert net.nodes["D"].criticality == 10
    assert net.nodes["D"].type == "database"
    assert net.nodes["W"].criticality == 6
    assert net.nodes["W"].type == "web"

    # Critical threshold
    assert net.meta.critical_threshold == 8
    assert net.is_critical("D") is True
    assert net.is_critical("L") is True
    assert net.is_critical("B") is True
    assert net.is_critical("A") is False
    assert net.is_critical("LT") is False

    # Edges: 5 network, 3 dependency
    network_edges = [e for e in net.edges.values() if e.kind == "network"]
    dependency_edges = [e for e in net.edges.values() if e.kind == "dependency"]
    assert len(network_edges) == 5
    assert len(dependency_edges) == 3
    assert len(net.edges) == 8

    # Network adjacency
    lt_net_neighbors = net.neighbors("LT", "network")
    assert sorted(lt_net_neighbors) == sorted([("L", 0.8), ("A", 0.4)])
    p_net_neighbors = net.neighbors("P", "network")
    assert p_net_neighbors == []

    # Dependency adjacency
    a_dep = net.neighbors("A", "dependency")
    assert sorted(a_dep) == sorted(["D", "L"])
    w_dep = net.neighbors("W", "dependency")
    assert w_dep == ["A"]

    # Incidents: exactly 2
    assert len(net.incidents) == 2
    assert "INC-1" in net.incidents
    assert "INC-2" in net.incidents
    inc1 = net.incidents["INC-1"]
    assert inc1.node_id == "LT"
    assert inc1.severity == 3
    assert inc1.confidence == 0.8
    inc2 = net.incidents["INC-2"]
    assert inc2.node_id == "P"
    assert inc2.severity == 9
    assert inc2.confidence == 0.9


def test_worked_example_without_node_isolation():
    """Test pure without_node transformation removing node L and its edges."""
    fixture_path = FIXTURES_DIR / "worked_example.json"
    net = load_network_from_file(fixture_path)

    isolated_net = net.without_node("L")

    # Original network must not be mutated
    assert "L" in net.nodes
    assert len(net.nodes) == 7

    # Isolated copy must not have L
    assert "L" not in isolated_net.nodes
    assert len(isolated_net.nodes) == 6

    # Edges touching L removed
    remaining_edge_endpoints = {(e.source, e.target) for e in isolated_net.edges.values()}
    assert ("LT", "L") not in remaining_edge_endpoints
    assert ("L", "D") not in remaining_edge_endpoints
    assert ("L", "B") not in remaining_edge_endpoints
    assert ("A", "L") not in remaining_edge_endpoints

    # Remaining network edges from LT should only be LT -> A
    assert isolated_net.neighbors("LT", "network") == [("A", 0.4)]


def test_demo_network_fixture():
    """demo_network.json must load and satisfy enterprise scale constraints."""
    fixture_path = FIXTURES_DIR / "demo_network.json"
    net = load_network_from_file(fixture_path)

    assert 18 <= len(net.nodes) <= 25
    assert len(net.nodes) == 20
    assert len(net.incidents) == 2

    # Incidents
    assert "INC-DEMO-01" in net.incidents
    assert "INC-DEMO-02" in net.incidents
    assert net.incidents["INC-DEMO-01"].node_id == "LAPTOP-ENG"
    assert net.incidents["INC-DEMO-02"].node_id == "PRINTER-HR"

    # Printer is isolated
    assert net.neighbors("PRINTER-HR", "network") == []
