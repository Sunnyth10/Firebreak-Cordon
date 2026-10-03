"""Live server end-to-end HTTP smoke test for Firebreak-Cordon.

Verifies that both the Flask API server (http://127.0.0.1:5000) and the
Vite React frontend dev server (http://127.0.0.1:5173) are running,
serving valid payloads, and correctly executing all graph algorithms.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request


def http_request(
    url: str,
    method: str = "GET",
    data: dict | None = None,
) -> tuple[int, dict | str]:
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    body = json.dumps(data).encode("utf-8") if data is not None else None

    try:
        with urllib.request.urlopen(req, data=body, timeout=5) as resp:
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read().decode("utf-8")
            if "application/json" in content_type:
                return status, json.loads(raw)
            return status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def run_smoke_tests() -> bool:
    print("=" * 60)
    print("FIREBREAK-CORDON LIVE END-TO-END SMOKE TESTS")
    print("=" * 60)
    all_passed = True

    # Ensure backend network state is reset to worked_example
    fixture_path = Path(__file__).resolve().parent.parent / "data" / "worked_example.json"
    if fixture_path.is_file():
        try:
            with open(fixture_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            http_request("http://127.0.0.1:5000/network", method="POST", data=data)
        except Exception:
            pass

    # 1. Frontend Server Check
    print("\n[1/8] Checking Vite React Frontend (http://127.0.0.1:5173)...")
    try:
        status, html = http_request("http://127.0.0.1:5173/")
        assert status == 200, f"Expected 200, got {status}"
        assert '<div id="root">' in str(html), "Missing root div in HTML"
        assert "/src/main.jsx" in str(html), "Missing main.jsx module script"
        print("  -> PASS: Vite server responding with valid React HTML.")
    except Exception as exc:
        print(f"  -> FAIL: {exc}")
        all_passed = False

    # 2. Flask Health Check
    print("\n[2/8] Checking Flask API Health (GET /health)...")
    try:
        status, res = http_request("http://127.0.0.1:5000/health")
        assert status == 200, f"Expected 200, got {status}"
        assert res.get("status") == "ok", f"Unexpected status: {res}"
        print(f"  -> PASS: Backend reports status: ok (v{res.get('version')})")
    except Exception as exc:
        print(f"  -> FAIL: {exc}")
        all_passed = False

    # 3. Incident Priority Queue & Explainability
    print("\n[3/8] Checking Priority Queue Ranking (GET /queue)...")
    try:
        status, res = http_request("http://127.0.0.1:5000/queue")
        assert status == 200, f"Expected 200, got {status}"
        q = res.get("queue", [])
        assert len(q) >= 2, f"Expected at least 2 incidents, got {len(q)}"
        inc1, inc2 = q[0], q[1]
        print(f"  Rank #1: {inc1['incident_id']} (Node {inc1['node_id']}) - Score: {inc1['score']:.2f}")
        print(f"  Rank #2: {inc2['incident_id']} (Node {inc2['node_id']}) - Score: {inc2['score']:.2f}")

        # Pedagogical story verification
        assert inc1["incident_id"] == "INC-1" and inc1["node_id"] == "LT"
        assert inc2["incident_id"] == "INC-2" and inc2["node_id"] == "P"
        assert inc1["score"] > inc2["score"]
        assert round(inc1["score"], 2) == 49.92
        assert round(inc2["score"], 2) == 8.10
        print("  -> PASS: Graph-aware ranking proved! Low-severity connected laptop ranks #1 over isolated printer.")
    except Exception as exc:
        print(f"  -> FAIL: {exc}")
        all_passed = False

    # 4. Blast Radius (BFS & Reach Probability)
    print("\n[4/8] Checking Blast Radius for Laptop 'LT' (GET /blast-radius/LT)...")
    try:
        status, res = http_request("http://127.0.0.1:5000/blast-radius/LT")
        assert status == 200, f"Expected 200, got {status}"
        blast = res.get("blast_radius", {})
        d_blast = blast.get("D", {})
        d_hops = d_blast.get("hops")
        d_prob = d_blast.get("reach_probability", 0)

        assert d_hops == 2, f"Expected 2 hops to D, got {d_hops}"
        assert abs(d_prob - 0.56) < 1e-3, f"Expected p=0.56 to D, got {d_prob}"
        print(f"  Reachability: {len(blast)} nodes reachable. Database 'D' at {d_hops} hops with probability {d_prob:.2f}.")
        print("  -> PASS: Blast radius calculated via BFS + Dijkstra on -ln(p).")
    except Exception as exc:
        print(f"  -> FAIL: {exc}")
        all_passed = False

    # 5. Attack Path & Containment Recommendation
    print("\n[5/8] Checking Attack Path LT -> D (GET /attack-path?from=LT&to=D)...")
    try:
        status, res = http_request(
            "http://127.0.0.1:5000/attack-path?from=LT&to=D",
            method="GET",
        )
        assert status == 200, f"Expected 200, got {status}"
        path = res.get("path", [])
        prob = res.get("probability", 0)
        assert path == ["LT", "L", "D"], f"Expected ['LT', 'L', 'D'], got {path}"
        assert abs(prob - 0.56) < 1e-3, f"Expected p=0.56, got {prob}"

        print(f"  Most Probable Path: {' -> '.join(path)} (p = {prob:.4f})")
        print("  -> PASS: Dijkstra attack path algorithm verified.")
    except Exception as exc:
        print(f"  -> FAIL: {exc}")
        all_passed = False

    # 6. Topological Dependency Restore Order
    print("\n[6/8] Checking Dependency Restore Plan (GET /restore-order)...")
    try:
        status, res = http_request("http://127.0.0.1:5000/restore-order")
        assert status == 200, f"Expected 200, got {status}"
        order = res.get("order", [])
        cycles = res.get("cycles", [])
        assert cycles == [], f"Expected 0 cycles, found: {cycles}"
        assert len(order) == 7, f"Expected 7 nodes in restore order, got {len(order)}"

        idx_d = order.index("D")
        idx_a = order.index("A")
        idx_w = order.index("W")
        assert idx_d < idx_a < idx_w, f"Invalid restore dependency ordering: {order}"
        print(f"  Safe Restore Sequence: {' -> '.join(order)}")
        print("  Dependency constraints verified: Database (D) restored before Auth (A), Auth before Web (W).")
        print("  -> PASS: Iterative DFS three-color topological ordering verified.")
    except Exception as exc:
        print(f"  -> FAIL: {exc}")
        all_passed = False

    # 7. Discrete Event Strategy Simulation
    print("\n[7/8] Running Strategy Comparison Simulation (POST /simulate)...")
    try:
        status, res = http_request(
            "http://127.0.0.1:5000/simulate",
            method="POST",
            data={
                "strategies": ["fcfs", "severity_only", "graph_aware"],
                "seed": 42,
            },
        )
        assert status == 200, f"Expected 200, got {status}"
        strategies = res.get("strategies", {})
        print("  Simulation Results (Seed 42):")
        for sname, sdata in strategies.items():
            print(
                f"    - {sname:14s}: Total Damage = {sdata.get('total_damage', 0):6.2f}, "
                f"Compromised = {sdata.get('compromised_count', 0)}, "
                f"Steps = {sdata.get('steps_taken', 0)}"
            )
        dam_graph = strategies.get("graph_aware", {}).get("total_damage", 999)
        dam_sev = strategies.get("severity_only", {}).get("total_damage", 0)
        assert dam_graph <= dam_sev, f"Graph aware damage ({dam_graph}) should be <= severity only ({dam_sev})"
        print("  -> PASS: Graph-aware response strategy minimizes lateral breach damage.")
    except Exception as exc:
        print(f"  -> FAIL: {exc}")
        all_passed = False

    # 8. Node Isolation & Network Recomputation
    print("\n[8/8] Testing Live Node Isolation (POST /isolate/L)...")
    try:
        status, res = http_request("http://127.0.0.1:5000/isolate/L", method="POST")
        assert status == 200, f"Expected 200, got {status}"
        assert res.get("isolated_node") == "L"
        assert res.get("disruption_cost") == 9

        affected = res.get("incidents_affected", [])
        assert len(affected) > 0, "Expected affected incidents list"
        inc0 = affected[0]
        assert inc0.get("incident_id") == "INC-1"
        assert abs(inc0.get("risk_reduction_pct", 0) - 65.38) < 0.1
        print(f"  Isolation Impact: Node 'L' isolated (Disruption cost: {res.get('disruption_cost')})")
        print(f"  INC-1 Risk Before: {inc0.get('risk_before')}, After: {inc0.get('risk_after')}, Reduction: {inc0.get('risk_reduction_pct')}%")
        print("  -> PASS: Live node isolation severing attack path successfully demonstrated.")
    except Exception as exc:
        print(f"  -> FAIL: {exc}")
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL 8 END-TO-END SMOKE TESTS PASSED SUCCESSFULLY! (100% HEALTHY)")
        print("=" * 60)
        return True
    else:
        print("SOME SMOKE TESTS FAILED. PLEASE REVIEW LOGS ABOVE.")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
