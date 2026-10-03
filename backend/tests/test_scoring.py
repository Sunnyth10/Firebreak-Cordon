"""Tests for priority scoring calculation and versioned IncidentQueue."""

from pathlib import Path
import pytest
from planner.core.loader import load_network_from_file
from planner.core.models import Incident
from planner.core.scoring import IncidentQueue, compute_score

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_worked_example_score_breakdowns():
    """Verify exact score breakdown and impact calculations for worked example."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")

    inc1 = net.incidents["INC-1"]
    sb1 = compute_score(net, inc1)
    assert sb1.severity == 3
    assert sb1.confidence == 0.8
    assert sb1.own_criticality == 2
    assert sb1.reachable_weighted_criticality == 18.8
    assert sb1.impact == 20.8
    assert sb1.score == 49.92

    inc2 = net.incidents["INC-2"]
    sb2 = compute_score(net, inc2)
    assert sb2.severity == 9
    assert sb2.confidence == 0.9
    assert sb2.own_criticality == 1
    assert sb2.reachable_weighted_criticality == 0.0
    assert sb2.impact == 1.0
    assert sb2.score == 8.10


def test_graph_aware_vs_severity_only_ranking():
    """Demonstrate how graph-aware ranking prioritizes connected laptop over isolated printer."""
    net = load_network_from_file(DATA_DIR / "worked_example.json")

    inc1 = net.incidents["INC-1"]
    inc2 = net.incidents["INC-2"]

    score1 = compute_score(net, inc1).score
    score2 = compute_score(net, inc2).score

    # Graph-aware queue
    queue = IncidentQueue()
    queue.push(inc1, score1)
    queue.push(inc2, score2)

    assert len(queue) == 2
    top_inc, top_score = queue.pop()
    assert top_inc.id == "INC-1"
    assert top_score == 49.92

    second_inc, second_score = queue.pop()
    assert second_inc.id == "INC-2"
    assert second_score == 8.10

    # Severity-only ranking (INC-2 severity 9 > INC-1 severity 3)
    severity_order = sorted([inc1, inc2], key=lambda x: x.severity, reverse=True)
    assert severity_order[0].id == "INC-2"
    assert severity_order[1].id == "INC-1"


def test_queue_lazy_update():
    """Verify lazy versioned score updates reprioritize without corrupting queue."""
    queue = IncidentQueue()
    inc_a = Incident(id="INC-A", node_id="LT", severity=2, confidence=0.5, timestamp="2026-10-03T10:00:00Z")
    inc_b = Incident(id="INC-B", node_id="P", severity=5, confidence=0.8, timestamp="2026-10-03T10:01:00Z")

    queue.push(inc_a, 10.0)
    queue.push(inc_b, 20.0)

    # Initial peak is INC-B
    assert queue.peek()[0].id == "INC-B"
    assert len(queue) == 2

    # Update INC-A score to 35.0 (exceeds INC-B)
    queue.update("INC-A", 35.0)
    assert queue.peek()[0].id == "INC-A"
    assert queue.peek()[1] == 35.0
    assert len(queue) == 2

    # Popping yields INC-A first with updated score
    popped_a, score_a = queue.pop()
    assert popped_a.id == "INC-A"
    assert score_a == 35.0
    assert len(queue) == 1

    popped_b, score_b = queue.pop()
    assert popped_b.id == "INC-B"
    assert score_b == 20.0
    assert len(queue) == 0

    # Pop on empty queue raises IndexError
    with pytest.raises(IndexError):
        queue.pop()


def test_queue_timestamp_tie_breaking():
    """Equal scores must break ties deterministically with earlier timestamp first."""
    queue = IncidentQueue()
    inc_early = Incident(id="INC-EARLY", node_id="LT", severity=5, confidence=0.8, timestamp="2026-10-03T09:00:00Z")
    inc_late = Incident(id="INC-LATE", node_id="P", severity=5, confidence=0.8, timestamp="2026-10-03T11:00:00Z")

    # Push late first, then early
    queue.push(inc_late, 50.0)
    queue.push(inc_early, 50.0)

    # Peek and pop must choose earlier timestamp
    assert queue.peek()[0].id == "INC-EARLY"
    popped, _ = queue.pop()
    assert popped.id == "INC-EARLY"
    popped2, _ = queue.pop()
    assert popped2.id == "INC-LATE"


def test_demo_network_scoring():
    """Verify scoring on 20-node enterprise network."""
    net = load_network_from_file(DATA_DIR / "demo_network.json")

    inc_eng = net.incidents["INC-DEMO-01"]
    sb_eng = compute_score(net, inc_eng)
    assert sb_eng.own_criticality == 2
    assert pytest.approx(sb_eng.reachable_weighted_criticality, abs=1e-3) == 35.0996
    assert pytest.approx(sb_eng.impact, abs=1e-3) == 37.0996
    assert pytest.approx(sb_eng.score, abs=1e-2) == 94.60

    inc_hr = net.incidents["INC-DEMO-02"]
    sb_hr = compute_score(net, inc_hr)
    assert sb_hr.own_criticality == 1
    assert sb_hr.reachable_weighted_criticality == 0.0
    assert sb_hr.impact == 1.0
    assert sb_hr.score == 9.50

    # Queue ordering
    queue = IncidentQueue()
    queue.push(inc_eng, sb_eng.score)
    queue.push(inc_hr, sb_hr.score)

    ranked = queue.ranked()
    assert len(ranked) == 2
    assert ranked[0][0].id == "INC-DEMO-01"
    assert ranked[1][0].id == "INC-DEMO-02"
