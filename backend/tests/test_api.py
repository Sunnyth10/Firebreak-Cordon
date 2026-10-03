"""Integration tests for Flask REST API endpoints."""

import json
from pathlib import Path
import pytest
from planner.api.app import create_app

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "data" / "worked_example.json"


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c


def test_api_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok", "version": "0.1.0"}


def test_api_get_network(client):
    res = client.get("/network")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["nodes"]) == 7
    assert len(data["edges"]) == 8
    assert len(data["incidents"]) == 2


def test_api_load_network_valid_and_invalid(client):
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        valid_payload = json.load(f)

    res = client.post("/network", json=valid_payload)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Network loaded successfully"

    # Invalid payload (e.g. probability 1.5)
    invalid_payload = dict(valid_payload)
    invalid_payload["edges"] = [
        {"id": "e_bad", "source": "LT", "target": "L", "kind": "network", "probability": 1.5}
    ]
    res_bad = client.post("/network", json=invalid_payload)
    assert res_bad.status_code == 400
    data = res_bad.get_json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) >= 1


def test_api_nodes_crud(client):
    # List nodes
    res = client.get("/nodes")
    assert res.status_code == 200
    assert len(res.get_json()) == 7

    # Get single node
    res_lt = client.get("/nodes/LT")
    assert res_lt.status_code == 200
    assert res_lt.get_json()["criticality"] == 2

    # Get non-existent node
    assert client.get("/nodes/UNKNOWN").status_code == 404

    # Create node
    res_create = client.post("/nodes", json={"id": "NEW-NODE", "name": "New Asset", "type": "endpoint", "criticality": 4})
    assert res_create.status_code == 201

    # Update node
    res_update = client.put("/nodes/NEW-NODE", json={"status": "suspected", "criticality": 6})
    assert res_update.status_code == 200
    assert res_update.get_json()["criticality"] == 6

    # Delete node
    res_del = client.delete("/nodes/NEW-NODE")
    assert res_del.status_code == 200


def test_api_priority_queue(client):
    res = client.get("/queue")
    assert res.status_code == 200
    data = res.get_json()
    assert "queue" in data
    queue = data["queue"]
    assert len(queue) == 2

    # INC-1 (score 49.92) ranked before INC-2 (score 8.10)
    assert queue[0]["incident_id"] == "INC-1"
    assert queue[0]["score"] == 49.92
    assert queue[0]["breakdown"]["impact"] == 20.8
    assert queue[1]["incident_id"] == "INC-2"
    assert queue[1]["score"] == 8.10


def test_api_blast_radius(client):
    res = client.get("/blast-radius/LT")
    assert res.status_code == 200
    data = res.get_json()
    assert data["source_id"] == "LT"
    assert data["total_impact"] == 20.8
    assert data["blast_radius"]["L"]["reach_probability"] == 0.8
    assert data["blast_radius"]["D"]["reach_probability"] == 0.56

    # 404 for unknown node
    assert client.get("/blast-radius/NONEXISTENT").status_code == 404


def test_api_attack_path(client):
    # Valid reachable path
    res = client.get("/attack-path?from=LT&to=D")
    assert res.status_code == 200
    data = res.get_json()
    assert data["path"] == ["LT", "L", "D"]
    assert data["probability"] == 0.56

    # Unreachable path
    res_p = client.get("/attack-path?from=LT&to=P")
    assert res_p.status_code == 200
    assert res_p.get_json()["path"] is None

    # Missing parameters
    assert client.get("/attack-path?from=LT").status_code == 400


def test_api_isolate_simulation(client):
    res = client.post("/isolate/L")
    assert res.status_code == 200
    data = res.get_json()
    assert data["isolated_node"] == "L"
    assert data["disruption_cost"] == 9
    assert len(data["incidents_affected"]) >= 1

    inc1_effect = next(i for i in data["incidents_affected"] if i["incident_id"] == "INC-1")
    assert inc1_effect["risk_before"] == 49.92
    assert inc1_effect["risk_after"] == 17.28
    assert inc1_effect["risk_reduction_pct"] == 65.38


def test_api_restore_order(client):
    res = client.get("/restore-order")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    order = data["order"]
    assert order.index("D") < order.index("A")
    assert order.index("L") < order.index("A")
    assert order.index("A") < order.index("W")


def test_api_simulate(client):
    res = client.post("/simulate", json={"seed": 42})
    assert res.status_code == 200
    data = res.get_json()
    assert data["seed"] == 42
    assert "strategies" in data
    strats = data["strategies"]
    assert strats["graph_aware"]["handled_order"] == ["INC-1", "INC-2"]
    assert strats["severity_only"]["handled_order"] == ["INC-2", "INC-1"]
    assert strats["graph_aware"]["total_damage"] < strats["severity_only"]["total_damage"]
