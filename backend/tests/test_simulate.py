"""Tests for incident response strategy discrete simulation engine."""

from pathlib import Path
import pytest
from planner.core.loader import load_network_from_file
from planner.core.simulate import run_strategies

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_worked_example_strategy_orders():
    """Verify handling orders of FCFS, Severity-Only, and Graph-Aware strategies."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")
    incidents = list(net.incidents.values())

    results = run_strategies(net, incidents, seed=42)

    # Strategy handled orders
    assert results["fcfs"]["handled_order"] == ["INC-1", "INC-2"]
    assert results["severity_only"]["handled_order"] == ["INC-2", "INC-1"]
    assert results["graph_aware"]["handled_order"] == ["INC-1", "INC-2"]


def test_graph_aware_reduces_damage():
    """Graph-aware policy must accumulate significantly lower damage than severity-only."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")
    incidents = list(net.incidents.values())

    results = run_strategies(net, incidents, seed=42)

    damage_ga = results["graph_aware"]["total_damage"]
    damage_sev = results["severity_only"]["total_damage"]

    # Containing pivotable laptop early prevents lateral damage accumulation
    assert damage_ga < damage_sev
    assert damage_ga > 0


def test_simulation_determinism():
    """Explicit random seed must produce 100% reproducible results."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")
    incidents = list(net.incidents.values())

    run1 = run_strategies(net, incidents, seed=123)
    run2 = run_strategies(net, incidents, seed=123)

    assert run1 == run2


def test_empty_incidents_simulation():
    """Simulation with zero incidents returns zero damage cleanly."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")
    results = run_strategies(net, [], seed=42)

    for strat in ["fcfs", "severity_only", "graph_aware"]:
        assert results[strat]["total_damage"] == 0.0
        assert results[strat]["handled_order"] == []


def test_demo_network_simulation():
    """Verify strategy comparison on 20-node enterprise network."""
    net = load_network_from_file(DATA_DIR / "demo_network.json")
    incidents = list(net.incidents.values())

    results = run_strategies(net, incidents, seed=999)

    # In demo network, INC-DEMO-01 is on LAPTOP-ENG (threatens core DB), INC-DEMO-02 is on isolated printer
    assert results["graph_aware"]["handled_order"][0] == "INC-DEMO-01"
    assert results["severity_only"]["handled_order"][0] == "INC-DEMO-02"

    # Graph-aware damage is much lower
    assert results["graph_aware"]["total_damage"] < results["severity_only"]["total_damage"]
