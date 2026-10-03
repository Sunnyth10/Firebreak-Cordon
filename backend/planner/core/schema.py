"""Schema validation logic for cyber incident networks."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import EdgeKind, NodeStatus, NodeType


def validate_network_dict(data: Any) -> list[str]:
    """Validate a parsed network dictionary against specification.

    Returns a list of clear human-readable error messages. If empty, data is valid.
    """
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["Network payload must be a JSON object (dict)."]

    # Validate meta
    meta = data.get("meta")
    if meta is not None:
        if not isinstance(meta, dict):
            errors.append("'meta' must be an object if provided.")
        else:
            if "name" in meta and not isinstance(meta["name"], str):
                errors.append("meta.name must be a string.")
            if "critical_threshold" in meta:
                threshold = meta["critical_threshold"]
                if not isinstance(threshold, int) or isinstance(threshold, bool) or threshold < 1 or threshold > 10:
                    errors.append(f"meta.critical_threshold must be an integer between 1 and 10, got {threshold}.")

    # Validate nodes
    raw_nodes = data.get("nodes")
    if raw_nodes is None:
        errors.append("Missing required field 'nodes'.")
        raw_nodes = []
    elif not isinstance(raw_nodes, list):
        errors.append("'nodes' must be a list.")
        raw_nodes = []

    valid_node_types = {e.value for e in NodeType}
    valid_node_statuses = {e.value for e in NodeStatus}
    seen_node_ids: set[str] = set()

    for i, node in enumerate(raw_nodes):
        if not isinstance(node, dict):
            errors.append(f"Node at index {i} must be an object.")
            continue

        node_id = node.get("id")
        if not node_id or not isinstance(node_id, str):
            errors.append(f"Node at index {i} must have a non-empty string 'id'.")
        else:
            if node_id in seen_node_ids:
                errors.append(f"Duplicate node id: '{node_id}'.")
            seen_node_ids.add(node_id)

        node_name = node.get("name")
        if not node_name or not isinstance(node_name, str):
            errors.append(f"Node '{node_id or i}': 'name' must be a non-empty string.")

        node_type = node.get("type")
        if node_type not in valid_node_types:
            errors.append(
                f"Node '{node_id or i}': invalid type '{node_type}'. "
                f"Must be one of {sorted(list(valid_node_types))}."
            )

        criticality = node.get("criticality")
        if not isinstance(criticality, int) or isinstance(criticality, bool) or criticality < 1 or criticality > 10:
            errors.append(
                f"Node '{node_id or i}': criticality must be an integer between 1 and 10, got {criticality}."
            )

        status = node.get("status", "healthy")
        if status not in valid_node_statuses:
            errors.append(
                f"Node '{node_id or i}': invalid status '{status}'. "
                f"Must be one of {sorted(list(valid_node_statuses))}."
            )

    # Validate edges
    raw_edges = data.get("edges")
    if raw_edges is None:
        errors.append("Missing required field 'edges'.")
        raw_edges = []
    elif not isinstance(raw_edges, list):
        errors.append("'edges' must be a list.")
        raw_edges = []

    valid_edge_kinds = {e.value for e in EdgeKind}
    seen_edge_ids: set[str] = set()

    for i, edge in enumerate(raw_edges):
        if not isinstance(edge, dict):
            errors.append(f"Edge at index {i} must be an object.")
            continue

        edge_id = edge.get("id")
        if not edge_id or not isinstance(edge_id, str):
            errors.append(f"Edge at index {i} must have a non-empty string 'id'.")
        else:
            if edge_id in seen_edge_ids:
                errors.append(f"Duplicate edge id: '{edge_id}'.")
            seen_edge_ids.add(edge_id)

        source = edge.get("source")
        if not isinstance(source, str) or not source:
            errors.append(f"Edge '{edge_id or i}': 'source' must be a non-empty string.")
        elif source not in seen_node_ids:
            errors.append(f"Edge '{edge_id or i}': source node '{source}' does not exist.")

        target = edge.get("target")
        if not isinstance(target, str) or not target:
            errors.append(f"Edge '{edge_id or i}': 'target' must be a non-empty string.")
        elif target not in seen_node_ids:
            errors.append(f"Edge '{edge_id or i}': target node '{target}' does not exist.")

        kind = edge.get("kind")
        if kind not in valid_edge_kinds:
            errors.append(
                f"Edge '{edge_id or i}': invalid kind '{kind}'. "
                f"Must be one of {sorted(list(valid_edge_kinds))}."
            )
        elif kind == EdgeKind.NETWORK.value:
            prob = edge.get("probability")
            if prob is None or isinstance(prob, bool) or not isinstance(prob, (int, float)):
                errors.append(f"Edge '{edge_id or i}': network edge requires numeric probability in (0, 1.0].")
            elif prob == 0 or prob == 0.0:
                errors.append(f"Edge '{edge_id or i}': probability 0 is rejected (ln(0) undefined).")
            elif prob < 0 or prob > 1.0:
                errors.append(f"Edge '{edge_id or i}': probability must be in (0, 1.0], got {prob}.")

    # Validate incidents
    raw_incidents = data.get("incidents", [])
    if not isinstance(raw_incidents, list):
        errors.append("'incidents' must be a list.")
        raw_incidents = []

    seen_incident_ids: set[str] = set()
    for i, incident in enumerate(raw_incidents):
        if not isinstance(incident, dict):
            errors.append(f"Incident at index {i} must be an object.")
            continue

        incident_id = incident.get("id")
        if not incident_id or not isinstance(incident_id, str):
            errors.append(f"Incident at index {i} must have a non-empty string 'id'.")
        else:
            if incident_id in seen_incident_ids:
                errors.append(f"Duplicate incident id: '{incident_id}'.")
            seen_incident_ids.add(incident_id)

        node_id = incident.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"Incident '{incident_id or i}': 'node_id' must be a non-empty string.")
        elif node_id not in seen_node_ids:
            errors.append(f"Incident '{incident_id or i}': node_id '{node_id}' does not exist.")

        severity = incident.get("severity")
        if not isinstance(severity, int) or isinstance(severity, bool) or severity < 1 or severity > 10:
            errors.append(
                f"Incident '{incident_id or i}': severity must be an integer between 1 and 10, got {severity}."
            )

        confidence = incident.get("confidence")
        if (
            confidence is None
            or isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or confidence < 0.0
            or confidence > 1.0
        ):
            errors.append(
                f"Incident '{incident_id or i}': confidence must be a float between 0.0 and 1.0, got {confidence}."
            )

        timestamp = incident.get("timestamp")
        if not isinstance(timestamp, str) or not timestamp:
            errors.append(f"Incident '{incident_id or i}': 'timestamp' must be an ISO 8601 string.")
        else:
            # Validate ISO 8601 format
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                errors.append(
                    f"Incident '{incident_id or i}': invalid ISO 8601 timestamp '{timestamp}'."
                )

    return errors
