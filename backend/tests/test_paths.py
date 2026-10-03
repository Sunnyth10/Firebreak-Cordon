"""Tests for Dijkstra attack path discovery and containment recommendations."""

import math
from pathlib import Path
import networkx as nx
import pytest
from planner.core.loader import load_network_from_file
from planner.core.paths import (
    attack_paths_to_critical,
    most_probable_path,
    recommend_containment,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_worked_example_most_probable_path():
    """Verify LT -> D selects LT -> L -> D (p=0.56) over LT -> A -> D (p=0.24)."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")

    res = most_probable_path(net, "LT", "D")
    assert res is not None
    assert res.nodes == ["LT", "L", "D"]
    assert res.probability == 0.56
    expected_w = -math.log(0.8) + -math.log(0.7)
    assert pytest.approx(res.total_weight, abs=1e-4) == expected_w

    # Direct edge LT -> L
    res_l = most_probable_path(net, "LT", "L")
    assert res_l is not None
    assert res_l.nodes == ["LT", "L"]
    assert res_l.probability == 0.80

    # Unreachable target
    assert most_probable_path(net, "LT", "P") is None
    assert most_probable_path(net, "P", "D") is None


def test_attack_paths_to_critical():
    """Discover and order paths to critical nodes (criticality >= 8) from LT."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")

    paths = attack_paths_to_critical(net, "LT")
    assert len(paths) == 3

    # Sorted by probability descending
    assert paths[0].nodes == ["LT", "L"]
    assert paths[0].probability == 0.80

    assert paths[1].nodes == ["LT", "L", "D"]
    assert paths[1].probability == 0.56

    assert paths[2].nodes == ["LT", "L", "B"]
    assert paths[2].probability == 0.40


def test_worked_example_recommend_containment():
    """Verify containment recommendations for compromised LT node."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")

    options = recommend_containment(net, ["LT"])
    assert len(options) >= 1

    # Find option for isolating L
    opt_l = next((o for o in options if o.node_id == "L"), None)
    assert opt_l is not None
    assert opt_l.risk_before == 49.92
    assert opt_l.risk_after == 17.28
    assert opt_l.risk_removed_pct == 65.38
    assert opt_l.disruption_cost == 9
    assert opt_l.paths_covered == 3


def test_demo_network_attack_path():
    """Verify most probable path in 20-node enterprise network from LAPTOP-ENG to DB-PRIMARY."""
    net = load_network_from_file(DATA_DIR / "demo_network.json")

    res = most_probable_path(net, "LAPTOP-ENG", "DB-PRIMARY")
    assert res is not None
    assert res.nodes == ["LAPTOP-ENG", "VPN-GATEWAY", "AUTH-AD", "BASTION-HOST", "DB-PRIMARY"]
    expected_prob = 0.9 * 0.8 * 0.7 * 0.85
    assert pytest.approx(res.probability, abs=1e-4) == round(expected_prob, 4)


def test_self_path_and_missing_node():
    net = load_network_from_file(DATA_DIR / "worked_example.json")

    self_path = most_probable_path(net, "LT", "LT")
    assert self_path is not None
    assert self_path.nodes == ["LT"]
    assert self_path.probability == 1.0
    assert self_path.total_weight == 0.0

    assert most_probable_path(net, "UNKNOWN", "LT") is None
    assert most_probable_path(net, "LT", "UNKNOWN") is None


def test_cross_verify_path_with_networkx():
    """Cross-verify most probable attack path against NetworkX Dijkstra reference."""
    net = load_network_from_file(DATA_DIR / "demo_network.json")

    G = nx.DiGraph()
    for e in net.edges.values():
        if e.kind == "network":
            G.add_edge(e.source, e.target, weight=-math.log(e.probability))

    for target in ["AUTH-AD", "DB-PRIMARY", "BACKUP-VAULT", "MONITOR-SIEM"]:
        custom_res = most_probable_path(net, "LAPTOP-ENG", target)
        assert custom_res is not None

        nx_path = nx.dijkstra_path(G, "LAPTOP-ENG", target, weight="weight")
        nx_len = nx.dijkstra_path_length(G, "LAPTOP-ENG", target, weight="weight")

        assert custom_res.nodes == nx_path
        assert pytest.approx(custom_res.total_weight, abs=1e-4) == nx_len
        assert pytest.approx(custom_res.probability, abs=1e-4) == round(math.exp(-nx_len), 4)
