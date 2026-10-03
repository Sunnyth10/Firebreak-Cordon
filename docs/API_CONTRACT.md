# REST API Specification & Contract
Cyber Incident Response Planner (DAA Hackathon, Problem #92)

All API requests and responses are JSON encoded. All endpoints return appropriate HTTP status codes (200, 201, 400, 404, 500).

---

## Standard Error Response Format
When a request fails due to validation errors (400) or missing resources (404), the response body is formatted as:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Edge probability must be in (0, 1.0]; got 1.5",
    "details": [
      "Edge 'E-bad': probability 1.5 is greater than 1.0"
    ]
  }
}
```

---

## Endpoints

### 1. Health Check
- **`GET /health`**
- **Description**: Verifies service status.
- **Response `200 OK`**:
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

### 2. Network Management
- **`POST /network`**
- **Description**: Uploads and initializes a full network graph with nodes, edges, and incidents.
- **Request Body**:
```json
{
  "meta": {
    "name": "Worked Example Network",
    "critical_threshold": 8
  },
  "nodes": [
    {
      "id": "LT",
      "name": "Laptop",
      "type": "endpoint",
      "criticality": 2,
      "status": "compromised"
    }
  ],
  "edges": [
    {
      "id": "E1",
      "source": "LT",
      "target": "L",
      "kind": "network",
      "probability": 0.8
    }
  ],
  "incidents": [
    {
      "id": "INC-1",
      "node_id": "LT",
      "severity": 3,
      "confidence": 0.8,
      "timestamp": "2026-10-03T10:00:00Z"
    }
  ]
}
```
- **Response `200 OK`**:
```json
{
  "message": "Network loaded successfully",
  "node_count": 7,
  "edge_count": 8,
  "incident_count": 2
}
```

---

### 3. CRUD for Nodes, Edges, Incidents, Scenarios

#### Nodes
- **`GET /nodes`**: Returns list of all nodes.
- **`POST /nodes`**: Creates a new node.
- **`GET /nodes/<node_id>`**: Returns specific node.
- **`PUT /nodes/<node_id>`**: Updates node attributes (e.g. status, criticality).
- **`DELETE /nodes/<node_id>`**: Deletes node and connected edges.

#### Edges
- **`GET /edges`**: Returns list of all edges.
- **`POST /edges`**: Creates a new edge (`network` with probability, or `dependency`).
- **`DELETE /edges/<edge_id>`**: Deletes edge.

#### Incidents
- **`GET /incidents`**: Returns list of all active incidents.
- **`POST /incidents`**: Creates/registers a new incident on a node.
- **`DELETE /incidents/<incident_id>`**: Resolves/deletes incident.

#### Scenarios
- **`GET /scenarios`**: List saved scenario configurations.
- **`POST /scenarios`**: Save current network state as a named scenario.
- **`GET /scenarios/<scenario_id>`**: Load a specific scenario.

---

### 4. Incident Priority Queue
- **`GET /queue`**
- **Description**: Returns all incidents ordered by priority score descending (earliest timestamp breaking ties).
- **Response `200 OK`**:
```json
{
  "queue": [
    {
      "incident_id": "INC-1",
      "node_id": "LT",
      "score": 49.92,
      "breakdown": {
        "severity": 3,
        "confidence": 0.8,
        "own_criticality": 2,
        "reachable_weighted_criticality": 18.8,
        "impact": 20.8,
        "score": 49.92
      },
      "timestamp": "2026-10-03T10:00:00Z"
    },
    {
      "incident_id": "INC-2",
      "node_id": "P",
      "score": 8.10,
      "breakdown": {
        "severity": 9,
        "confidence": 0.9,
        "own_criticality": 1,
        "reachable_weighted_criticality": 0.0,
        "impact": 1.0,
        "score": 8.10
      },
      "timestamp": "2026-10-03T10:05:00Z"
    }
  ]
}
```

---

### 5. Blast Radius
- **`GET /blast-radius/<node_id>`**
- **Description**: Computes blast radius of node over `network` edges.
- **Response `200 OK`**:
```json
{
  "source_id": "LT",
  "blast_radius": {
    "L": { "hops": 1, "reach_probability": 0.80 },
    "A": { "hops": 1, "reach_probability": 0.40 },
    "D": { "hops": 2, "reach_probability": 0.56 },
    "B": { "hops": 2, "reach_probability": 0.40 }
  },
  "total_impact": 20.8
}
```

---

### 6. Most Probable Attack Path
- **`GET /attack-path?from=<source_id>&to=<target_id>`**
- **Description**: Dijkstra shortest path under weights $w = -\ln(p)$.
- **Response `200 OK`**:
```json
{
  "source": "LT",
  "target": "D",
  "path": ["LT", "L", "D"],
  "probability": 0.56,
  "total_weight": 0.57982,
  "alternatives": [
    {
      "path": ["LT", "A", "D"],
      "probability": 0.24,
      "total_weight": 1.42712
    }
  ]
}
```

---

### 7. Node Isolation Simulation
- **`POST /isolate/<node_id>`**
- **Description**: Simulates containment by isolating a node and recalculating risk and blast radius.
- **Response `200 OK`**:
```json
{
  "isolated_node": "L",
  "disruption_cost": 9,
  "incidents_affected": [
    {
      "incident_id": "INC-1",
      "node_id": "LT",
      "risk_before": 49.92,
      "risk_after": 17.28,
      "risk_reduction_pct": 65.38,
      "remaining_blast_radius": {
        "A": { "hops": 1, "reach_probability": 0.40 },
        "D": { "hops": 2, "reach_probability": 0.24 }
      }
    }
  ]
}
```

---

### 8. Dependency-Safe Restore Order
- **`GET /restore-order`**
- **Description**: Topological sort of dependency edges with cycle detection.
- **Response `200 OK` (when acyclic)**:
```json
{
  "ok": true,
  "order": ["D", "L", "B", "LT", "P", "A", "W"],
  "cycle": null,
  "explanation": "Valid topological restore order ensuring all required dependencies precede dependents."
}
```
- **Response `200 OK` (when cycle detected)**:
```json
{
  "ok": false,
  "order": null,
  "cycle": ["A", "D", "A"],
  "explanation": "Circular dependency detected involving nodes A, D. Restoration blocked."
}
```

---

### 9. Strategy Simulation Comparison
- **`POST /simulate`**
- **Description**: Simulates response under three strategies: `fcfs`, `severity_only`, and `graph_aware`.
- **Request Body**:
```json
{
  "seed": 42
}
```
- **Response `200 OK`**:
```json
{
  "seed": 42,
  "strategies": {
    "fcfs": {
      "total_damage": 312.4,
      "handled_order": ["INC-1", "INC-2"],
      "_mock": true
    },
    "severity_only": {
      "total_damage": 450.2,
      "handled_order": ["INC-2", "INC-1"],
      "_mock": true
    },
    "graph_aware": {
      "total_damage": 182.1,
      "handled_order": ["INC-1", "INC-2"],
      "_mock": true
    }
  }
}
```
*(Note: Non-hand-calculated simulation metrics explicitly flag `"_mock": true`).*
