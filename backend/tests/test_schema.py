"""Tests for network schema validation error rejection and messaging."""

import copy
import pytest
from planner.core.schema import validate_network_dict

VALID_BASE = {
    "meta": {"name": "Test Net", "critical_threshold": 8},
    "nodes": [
        {"id": "n1", "name": "Node 1", "type": "endpoint", "criticality": 5, "status": "healthy"},
        {"id": "n2", "name": "Node 2", "type": "database", "criticality": 10, "status": "healthy"},
    ],
    "edges": [
        {"id": "e1", "source": "n1", "target": "n2", "kind": "network", "probability": 0.5},
    ],
    "incidents": [
        {"id": "inc1", "node_id": "n1", "severity": 5, "confidence": 0.8, "timestamp": "2026-10-03T12:00:00Z"}
    ],
}


def test_valid_schema_passes():
    errors = validate_network_dict(VALID_BASE)
    assert errors == []


def test_reject_probability_zero():
    """probability 0 rejected (ln(0) undefined)."""
    payload = copy.deepcopy(VALID_BASE)
    payload["edges"][0]["probability"] = 0
    errors = validate_network_dict(payload)
    assert len(errors) >= 1
    assert any("probability 0 is rejected" in err or "ln(0) undefined" in err for err in errors)


def test_reject_probability_greater_than_one():
    """probability 1.5 rejected."""
    payload = copy.deepcopy(VALID_BASE)
    payload["edges"][0]["probability"] = 1.5
    errors = validate_network_dict(payload)
    assert len(errors) >= 1
    assert any("probability must be in (0, 1.0]" in err and "1.5" in err for err in errors)


def test_reject_unknown_node_reference_edge():
    """Edge referencing unknown source and target nodes rejected."""
    payload = copy.deepcopy(VALID_BASE)
    payload["edges"].append({
        "id": "e_bad",
        "source": "ghost_source",
        "target": "n2",
        "kind": "network",
        "probability": 0.5,
    })
    errors = validate_network_dict(payload)
    assert len(errors) >= 1
    assert any("source node 'ghost_source' does not exist" in err for err in errors)


def test_reject_unknown_node_reference_incident():
    """Incident referencing unknown node_id rejected."""
    payload = copy.deepcopy(VALID_BASE)
    payload["incidents"].append({
        "id": "inc_bad",
        "node_id": "unknown_server",
        "severity": 4,
        "confidence": 0.7,
        "timestamp": "2026-10-03T12:00:00Z",
    })
    errors = validate_network_dict(payload)
    assert len(errors) >= 1
    assert any("node_id 'unknown_server' does not exist" in err for err in errors)


def test_reject_duplicate_ids():
    """Duplicate node, edge, and incident ids must be detected."""
    payload = copy.deepcopy(VALID_BASE)
    # Duplicate node id
    payload["nodes"].append(
        {"id": "n1", "name": "Node Duplicate", "type": "app", "criticality": 4}
    )
    # Duplicate edge id
    payload["edges"].append(
        {"id": "e1", "source": "n1", "target": "n2", "kind": "dependency"}
    )
    # Duplicate incident id
    payload["incidents"].append(
        {"id": "inc1", "node_id": "n2", "severity": 2, "confidence": 0.5, "timestamp": "2026-10-03T12:00:00Z"}
    )
    errors = validate_network_dict(payload)
    assert any("Duplicate node id: 'n1'" in err for err in errors)
    assert any("Duplicate edge id: 'e1'" in err for err in errors)
    assert any("Duplicate incident id: 'inc1'" in err for err in errors)


def test_reject_bad_edge_kind():
    """Edge kind other than network or dependency must be rejected."""
    payload = copy.deepcopy(VALID_BASE)
    payload["edges"][0]["kind"] = "unsupported_link"
    errors = validate_network_dict(payload)
    assert len(errors) >= 1
    assert any("invalid kind 'unsupported_link'" in err for err in errors)


def test_reject_criticality_eleven():
    """Criticality > 10 rejected."""
    payload = copy.deepcopy(VALID_BASE)
    payload["nodes"][0]["criticality"] = 11
    errors = validate_network_dict(payload)
    assert len(errors) >= 1
    assert any("criticality must be an integer between 1 and 10" in err and "11" in err for err in errors)


def test_reject_confidence_negative():
    """Confidence -0.1 rejected."""
    payload = copy.deepcopy(VALID_BASE)
    payload["incidents"][0]["confidence"] = -0.1
    errors = validate_network_dict(payload)
    assert len(errors) >= 1
    assert any("confidence must be a float between 0.0 and 1.0" in err and "-0.1" in err for err in errors)


def test_multiple_errors_collected_together():
    """Validation must return all errors rather than failing on the first one."""
    payload = {
        "nodes": [
            {"id": "n1", "name": "Node 1", "type": "invalid_type", "criticality": 15},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "missing_node", "kind": "network", "probability": 2.5},
        ],
        "incidents": [
            {"id": "inc1", "node_id": "missing_node2", "severity": 20, "confidence": -0.5, "timestamp": "invalid_ts"},
        ],
    }
    errors = validate_network_dict(payload)
    # Should accumulate errors across node type, node criticality, target node, probability, incident node, severity, confidence, timestamp
    assert len(errors) >= 6
