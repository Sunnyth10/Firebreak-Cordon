"""Loader to parse and instantiate validated Network instances."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .graph import Network
from .models import Edge, Incident, NetworkMeta, Node
from .schema import validate_network_dict


class ValidationError(ValueError):
    """Raised when network dictionary fails schema validation."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        message = f"Network validation failed with {len(errors)} error(s):\n" + "\n".join(
            f"  - {err}" for err in errors
        )
        super().__init__(message)


def load_network_dict(data: dict[str, Any]) -> Network:
    """Validate and convert dictionary payload into Network instance."""
    errors = validate_network_dict(data)
    if errors:
        raise ValidationError(errors)

    meta_raw = data.get("meta", {})
    meta = NetworkMeta(
        name=meta_raw.get("name", "Cyber Incident Network"),
        critical_threshold=meta_raw.get("critical_threshold", 8),
    )

    nodes: dict[str, Node] = {}
    for n in data.get("nodes", []):
        node = Node(
            id=n["id"],
            name=n["name"],
            type=n["type"],
            criticality=n["criticality"],
            status=n.get("status", "healthy"),
        )
        nodes[node.id] = node

    edges: dict[str, Edge] = {}
    for e in data.get("edges", []):
        edge = Edge(
            id=e["id"],
            source=e["source"],
            target=e["target"],
            kind=e["kind"],
            probability=e.get("probability") if e["kind"] == "network" else None,
        )
        edges[edge.id] = edge

    incidents: dict[str, Incident] = {}
    for inc in data.get("incidents", []):
        incident = Incident(
            id=inc["id"],
            node_id=inc["node_id"],
            severity=inc["severity"],
            confidence=float(inc["confidence"]),
            timestamp=inc["timestamp"],
        )
        incidents[incident.id] = incident

    return Network(
        meta=meta,
        nodes=nodes,
        edges=edges,
        incidents=incidents,
    )


def load_network_from_file(file_path: str | Path) -> Network:
    """Read a JSON file and parse into a validated Network instance."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Network file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return load_network_dict(data)


def load_network_from_json(json_str: str) -> Network:
    """Read a JSON string and parse into a validated Network instance."""
    data = json.loads(json_str)
    return load_network_dict(data)
