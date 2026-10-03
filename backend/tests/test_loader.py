"""Tests for loader functions and health check API endpoint."""

import json
from pathlib import Path
import pytest
from planner.api.app import create_app
from planner.core.loader import (
    ValidationError,
    load_network_dict,
    load_network_from_file,
    load_network_from_json,
)

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "data" / "worked_example.json"


def test_load_network_dict_success():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    net = load_network_dict(data)
    assert len(net.nodes) == 7
    assert len(net.edges) == 8


def test_load_network_dict_raises_validation_error():
    invalid_data = {
        "nodes": [{"id": "n1", "name": "N1", "type": "endpoint", "criticality": 12}],
        "edges": [],
    }
    with pytest.raises(ValidationError) as exc_info:
        load_network_dict(invalid_data)
    assert "Network validation failed" in str(exc_info.value)
    assert len(exc_info.value.errors) >= 1


def test_load_network_from_file_success():
    net = load_network_from_file(FIXTURE_PATH)
    assert net.get_node("LT") is not None
    assert net.get_node("LT").criticality == 2


def test_load_network_from_file_missing():
    with pytest.raises(FileNotFoundError):
        load_network_from_file(Path("non_existent_network_file.json"))


def test_load_network_from_json():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        raw_json = f.read()
    net = load_network_from_json(raw_json)
    assert len(net.nodes) == 7
    assert net.meta.critical_threshold == 8


def test_health_check_endpoint():
    """Verify Flask app factory GET /health endpoint."""
    app = create_app({"TESTING": True})
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"status": "ok", "version": "0.1.0"}
