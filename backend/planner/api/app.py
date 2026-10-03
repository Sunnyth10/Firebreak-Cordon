"""Flask REST API application for Cyber Incident Response Planner (Phase 6).

Thin wrapper over pure core algorithms: validates HTTP payloads and calls core functions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from flask import Flask, jsonify, request

from ..core.blast import blast_radius
from ..core.graph import Network
from ..core.loader import load_network_dict, load_network_from_file
from ..core.models import Edge, Incident, Node
from ..core.paths import attack_paths_to_critical, most_probable_path, recommend_containment
from ..core.restore import restore_order
from ..core.schema import validate_network_dict
from ..core.scoring import IncidentQueue, compute_score
from ..core.simulate import run_strategies

DEFAULT_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "worked_example.json"
)


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Application factory for the Cyber Incident Planner REST API."""
    app = Flask(__name__)

    if test_config is not None:
        app.config.update(test_config)

    # In-memory network state and saved scenarios
    initial_network: Network | None = None
    if DEFAULT_FIXTURE_PATH.is_file():
        try:
            initial_network = load_network_from_file(DEFAULT_FIXTURE_PATH)
        except Exception:
            initial_network = Network()
    else:
        initial_network = Network()

    state: dict[str, Any] = {
        "network": initial_network,
        "scenarios": {},
    }

    @app.after_request
    def enable_cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response

    @app.route("/", methods=["OPTIONS"])
    @app.route("/<path:path>", methods=["OPTIONS"])
    def options_handler(*args, **kwargs):
        return "", 204

    # 1. Health Endpoint
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "version": "0.1.0"}), 200

    # 2. Full Network Load
    @app.route("/network", methods=["POST"])
    def load_network():
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "Request body must be a valid JSON object."
                }
            }), 400

        errors = validate_network_dict(payload)
        if errors:
            return jsonify({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Network payload validation failed with {len(errors)} error(s).",
                    "details": errors,
                }
            }), 400

        try:
            net = load_network_dict(payload)
            state["network"] = net
            return jsonify({
                "message": "Network loaded successfully",
                "node_count": len(net.nodes),
                "edge_count": len(net.edges),
                "incident_count": len(net.incidents),
            }), 200
        except Exception as e:
            return jsonify({
                "error": {
                    "code": "LOAD_ERROR",
                    "message": str(e)
                }
            }), 400

    @app.route("/network", methods=["GET"])
    def get_network():
        net: Network = state["network"]
        nodes_list = [
            {"id": n.id, "name": n.name, "type": n.type, "criticality": n.criticality, "status": n.status}
            for n in net.nodes.values()
        ]
        edges_list = [
            {"id": e.id, "source": e.source, "target": e.target, "kind": e.kind, "probability": e.probability}
            for e in net.edges.values()
        ]
        incidents_list = [
            {"id": i.id, "node_id": i.node_id, "severity": i.severity, "confidence": i.confidence, "timestamp": i.timestamp}
            for i in net.incidents.values()
        ]
        return jsonify({
            "meta": {
                "name": net.meta.name,
                "critical_threshold": net.meta.critical_threshold,
            },
            "nodes": nodes_list,
            "edges": edges_list,
            "incidents": incidents_list,
        }), 200

    # 3. Nodes CRUD
    @app.route("/nodes", methods=["GET"])
    def list_nodes():
        net: Network = state["network"]
        return jsonify([
            {"id": n.id, "name": n.name, "type": n.type, "criticality": n.criticality, "status": n.status}
            for n in net.nodes.values()
        ]), 200

    @app.route("/nodes/<node_id>", methods=["GET"])
    def get_node(node_id: str):
        net: Network = state["network"]
        node = net.get_node(node_id)
        if not node:
            return jsonify({"error": {"code": "NOT_FOUND", "message": f"Node '{node_id}' not found."}}), 404
        return jsonify({
            "id": node.id,
            "name": node.name,
            "type": node.type,
            "criticality": node.criticality,
            "status": node.status,
        }), 200

    @app.route("/nodes", methods=["POST"])
    def create_node():
        net: Network = state["network"]
        data = request.get_json(silent=True) or {}
        node_id = data.get("id")
        if not node_id or not isinstance(node_id, str):
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing non-empty 'id'."}}), 400
        if node_id in net.nodes:
            return jsonify({"error": {"code": "CONFLICT", "message": f"Node '{node_id}' already exists."}}), 400

        try:
            crit = int(data.get("criticality", 5))
            if crit < 1 or crit > 10:
                raise ValueError()
        except Exception:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Criticality must be between 1 and 10."}}), 400

        new_node = Node(
            id=node_id,
            name=data.get("name", node_id),
            type=data.get("type", "endpoint"),
            criticality=crit,
            status=data.get("status", "healthy"),
        )
        new_nodes = dict(net.nodes)
        new_nodes[node_id] = new_node
        state["network"] = Network(meta=net.meta, nodes=new_nodes, edges=dict(net.edges), incidents=dict(net.incidents))
        return jsonify({
            "id": new_node.id, "name": new_node.name, "type": new_node.type,
            "criticality": new_node.criticality, "status": new_node.status
        }), 201

    @app.route("/nodes/<node_id>", methods=["PUT"])
    def update_node(node_id: str):
        net: Network = state["network"]
        existing = net.get_node(node_id)
        if not existing:
            return jsonify({"error": {"code": "NOT_FOUND", "message": f"Node '{node_id}' not found."}}), 404

        data = request.get_json(silent=True) or {}
        crit = data.get("criticality", existing.criticality)
        status = data.get("status", existing.status)
        name = data.get("name", existing.name)
        node_type = data.get("type", existing.type)

        updated_node = Node(
            id=node_id,
            name=name,
            type=node_type,
            criticality=int(crit),
            status=status,
        )
        new_nodes = dict(net.nodes)
        new_nodes[node_id] = updated_node
        state["network"] = Network(meta=net.meta, nodes=new_nodes, edges=dict(net.edges), incidents=dict(net.incidents))
        return jsonify({
            "id": updated_node.id, "name": updated_node.name, "type": updated_node.type,
            "criticality": updated_node.criticality, "status": updated_node.status
        }), 200

    @app.route("/nodes/<node_id>", methods=["DELETE"])
    def delete_node(node_id: str):
        net: Network = state["network"]
        if node_id not in net.nodes:
            return jsonify({"error": {"code": "NOT_FOUND", "message": f"Node '{node_id}' not found."}}), 404
        state["network"] = net.without_node(node_id)
        return jsonify({"message": f"Node '{node_id}' deleted."}), 200

    # 4. Edges CRUD
    @app.route("/edges", methods=["GET"])
    def list_edges():
        net: Network = state["network"]
        return jsonify([
            {"id": e.id, "source": e.source, "target": e.target, "kind": e.kind, "probability": e.probability}
            for e in net.edges.values()
        ]), 200

    @app.route("/edges", methods=["POST"])
    def create_edge():
        net: Network = state["network"]
        data = request.get_json(silent=True) or {}
        edge_id = data.get("id")
        source = data.get("source")
        target = data.get("target")
        kind = data.get("kind", "network")
        prob = data.get("probability")

        if not edge_id or not source or not target:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing edge id, source, or target."}}), 400
        if source not in net.nodes or target not in net.nodes:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Source or target node does not exist."}}), 400

        new_edge = Edge(id=edge_id, source=source, target=target, kind=kind, probability=float(prob) if prob else None)
        new_edges = dict(net.edges)
        new_edges[edge_id] = new_edge
        state["network"] = Network(meta=net.meta, nodes=dict(net.nodes), edges=new_edges, incidents=dict(net.incidents))
        return jsonify({
            "id": new_edge.id, "source": new_edge.source, "target": new_edge.target, "kind": new_edge.kind, "probability": new_edge.probability
        }), 201

    @app.route("/edges/<edge_id>", methods=["DELETE"])
    def delete_edge(edge_id: str):
        net: Network = state["network"]
        if edge_id not in net.edges:
            return jsonify({"error": {"code": "NOT_FOUND", "message": f"Edge '{edge_id}' not found."}}), 404
        new_edges = {eid: e for eid, e in net.edges.items() if eid != edge_id}
        state["network"] = Network(meta=net.meta, nodes=dict(net.nodes), edges=new_edges, incidents=dict(net.incidents))
        return jsonify({"message": f"Edge '{edge_id}' deleted."}), 200

    # 5. Incidents CRUD
    @app.route("/incidents", methods=["GET"])
    def list_incidents():
        net: Network = state["network"]
        return jsonify([
            {"id": inc.id, "node_id": inc.node_id, "severity": inc.severity, "confidence": inc.confidence, "timestamp": inc.timestamp}
            for inc in net.incidents.values()
        ]), 200

    @app.route("/incidents", methods=["POST"])
    def create_incident():
        net: Network = state["network"]
        data = request.get_json(silent=True) or {}
        inc_id = data.get("id")
        node_id = data.get("node_id")
        sev = data.get("severity")
        conf = data.get("confidence")
        ts = data.get("timestamp")

        if not inc_id or not node_id:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing incident id or node_id."}}), 400
        if node_id not in net.nodes:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": f"Node '{node_id}' does not exist."}}), 400

        new_inc = Incident(
            id=inc_id,
            node_id=node_id,
            severity=int(sev or 5),
            confidence=float(conf if conf is not None else 0.8),
            timestamp=ts or "2026-10-03T12:00:00Z",
        )
        new_incidents = dict(net.incidents)
        new_incidents[inc_id] = new_inc
        state["network"] = Network(meta=net.meta, nodes=dict(net.nodes), edges=dict(net.edges), incidents=new_incidents)
        return jsonify({
            "id": new_inc.id, "node_id": new_inc.node_id, "severity": new_inc.severity,
            "confidence": new_inc.confidence, "timestamp": new_inc.timestamp
        }), 201

    @app.route("/incidents/<incident_id>", methods=["DELETE"])
    def delete_incident(incident_id: str):
        net: Network = state["network"]
        if incident_id not in net.incidents:
            return jsonify({"error": {"code": "NOT_FOUND", "message": f"Incident '{incident_id}' not found."}}), 404
        new_incidents = {iid: inc for iid, inc in net.incidents.items() if iid != incident_id}
        state["network"] = Network(meta=net.meta, nodes=dict(net.nodes), edges=dict(net.edges), incidents=new_incidents)
        return jsonify({"message": f"Incident '{incident_id}' resolved."}), 200

    # 6. Scenarios
    @app.route("/scenarios", methods=["GET"])
    def list_scenarios():
        scenarios = list(state["scenarios"].values())
        return jsonify(scenarios), 200

    @app.route("/scenarios", methods=["POST"])
    def save_scenario():
        net: Network = state["network"]
        data = request.get_json(silent=True) or {}
        sc_id = data.get("id") or f"scenario-{len(state['scenarios']) + 1}"
        scenario_obj = {
            "id": sc_id,
            "name": data.get("name", f"Scenario {sc_id}"),
            "description": data.get("description", "Saved network state"),
            "created_at": "2026-10-03T12:00:00Z",
            "node_count": len(net.nodes),
            "edge_count": len(net.edges),
            "incident_count": len(net.incidents),
        }
        state["scenarios"][sc_id] = scenario_obj
        return jsonify(scenario_obj), 201

    # 7. Priority Queue
    @app.route("/queue", methods=["GET"])
    def get_priority_queue():
        net: Network = state["network"]
        queue = IncidentQueue()
        breakdowns: dict[str, Any] = {}

        for inc in net.incidents.values():
            sb = compute_score(net, inc)
            queue.push(inc, sb.score)
            breakdowns[inc.id] = sb

        ranked_incidents = queue.ranked()
        queue_response = [
            {
                "incident_id": inc.id,
                "node_id": inc.node_id,
                "score": score,
                "breakdown": {
                    "severity": breakdowns[inc.id].severity,
                    "confidence": breakdowns[inc.id].confidence,
                    "own_criticality": breakdowns[inc.id].own_criticality,
                    "reachable_weighted_criticality": breakdowns[inc.id].reachable_weighted_criticality,
                    "impact": breakdowns[inc.id].impact,
                    "score": breakdowns[inc.id].score,
                },
                "timestamp": inc.timestamp,
            }
            for inc, score in ranked_incidents
        ]

        return jsonify({"queue": queue_response}), 200

    # 8. Blast Radius
    @app.route("/blast-radius/<node_id>", methods=["GET"])
    def get_blast_radius(node_id: str):
        net: Network = state["network"]
        node = net.get_node(node_id)
        if not node:
            return jsonify({"error": {"code": "NOT_FOUND", "message": f"Node '{node_id}' not found."}}), 404

        blast = blast_radius(net, node_id)
        reachable_wt = sum(
            net.nodes[target].criticality * float(d["reach_probability"])
            for target, d in blast.items()
            if target in net.nodes
        )
        total_impact = round(node.criticality + reachable_wt, 4)

        return jsonify({
            "source_id": node_id,
            "blast_radius": blast,
            "total_impact": total_impact,
        }), 200

    # 9. Attack Path
    @app.route("/attack-path", methods=["GET"])
    def get_attack_path():
        net: Network = state["network"]
        source = request.args.get("from")
        target = request.args.get("to")

        if not source or not target:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing 'from' or 'to' query parameters."}}), 400

        if source not in net.nodes:
            return jsonify({"error": {"code": "NOT_FOUND", "message": f"Source node '{source}' not found."}}), 404
        if target not in net.nodes:
            return jsonify({"error": {"code": "NOT_FOUND", "message": f"Target node '{target}' not found."}}), 404

        path_res = most_probable_path(net, source, target)
        if not path_res:
            return jsonify({
                "source": source,
                "target": target,
                "path": None,
                "probability": 0.0,
                "total_weight": None,
                "explanation": f"No directed network path exists from '{source}' to '{target}'."
            }), 200

        return jsonify({
            "source": source,
            "target": target,
            "path": path_res.nodes,
            "probability": path_res.probability,
            "total_weight": path_res.total_weight,
        }), 200

    # 10. Containment / Isolation Simulation
    @app.route("/isolate/<node_id>", methods=["POST"])
    def isolate_node(node_id: str):
        net: Network = state["network"]
        target_node = net.get_node(node_id)
        if not target_node:
            return jsonify({"error": {"code": "NOT_FOUND", "message": f"Node '{node_id}' not found."}}), 404

        isolated_net = net.without_node(node_id)
        affected_incidents = []

        for inc in net.incidents.values():
            if inc.node_id == node_id:
                # Incident node itself is isolated
                affected_incidents.append({
                    "incident_id": inc.id,
                    "node_id": inc.node_id,
                    "risk_before": compute_score(net, inc).score,
                    "risk_after": 0.0,
                    "risk_reduction_pct": 100.0,
                    "remaining_blast_radius": {},
                })
            else:
                score_before = compute_score(net, inc).score
                score_after = compute_score(isolated_net, inc).score
                pct = round(((score_before - score_after) / score_before) * 100, 2) if score_before > 0 else 0.0
                rem_blast = blast_radius(isolated_net, inc.node_id)
                affected_incidents.append({
                    "incident_id": inc.id,
                    "node_id": inc.node_id,
                    "risk_before": score_before,
                    "risk_after": score_after,
                    "risk_reduction_pct": pct,
                    "remaining_blast_radius": rem_blast,
                })

        return jsonify({
            "isolated_node": node_id,
            "disruption_cost": target_node.criticality,
            "incidents_affected": affected_incidents,
        }), 200

    # 11. Restore Order
    @app.route("/restore-order", methods=["GET"])
    def get_restore_order():
        net: Network = state["network"]
        res = restore_order(net)
        return jsonify({
            "ok": res.ok,
            "order": res.order,
            "cycle": res.cycle,
            "explanation": res.explanation,
        }), 200

    # 12. Simulation Comparison
    @app.route("/simulate", methods=["POST"])
    def simulate_strategies():
        net: Network = state["network"]
        payload = request.get_json(silent=True) or {}
        seed = int(payload.get("seed", 42))

        incidents_list = list(net.incidents.values())
        results = run_strategies(net, incidents_list, seed=seed)

        return jsonify({
            "seed": seed,
            "strategies": results,
        }), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
