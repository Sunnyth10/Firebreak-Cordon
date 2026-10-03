# Phase 1 Handoff: Cyber Incident Response Planner

## 1. Status
- **Phase Completed**: Phase 1 (Graph Model & BFS Blast Radius)
- **Date**: October 3, 2026
- **What is done**:
  - `backend/planner/core/blast.py` implemented with:
    - Unweighted Breadth-First Search (BFS) computing minimum hop distance.
    - Dijkstra shortest path under additive edge weights $w = -\ln(p) \ge 0$ computing maximum path probability product $P = \exp(-D)$.
    - Handling for isolated nodes, non-existent sources, and cyclic graphs.
  - Comprehensive unit test suite in `backend/tests/test_blast.py`:
    - Worked example verification for `LT` (exact hops and reach probabilities for `L`, `A`, `D`, `B`).
    - Isolated nodes (`P`, `W`) returning empty blast radius `{}`.
    - Recomputed blast radius after node isolation (`without_node("L")`).
    - Demo enterprise network verification for `LAPTOP-ENG` and `PRINTER-HR`.
    - Cyclic graph tolerance.
    - Independent cross-verification of all hops and probabilities against `networkx` (`descendants`, `shortest_path_length`).
  - All 26 unit tests passing.
- **What is NOT done** (scheduled for future phases):
  - Priority scoring & versioned max-heap queue (Phase 2).
  - Dijkstra attack path discovery & containment recommendation (Phase 3).
  - Iterative DFS cycle detection & topological restore ordering (Phase 4).
  - Strategy simulation comparison (Phase 5).
  - Flask algorithm endpoints (Phase 6).
  - Interactive UI panels for queue and containment (Phase 7).

---

## 2. What Was Built
- **`blast_radius(network, source_id)` Engine**:
  - Implemented in `backend/planner/core/blast.py` using standard library `collections.deque`, `heapq`, and `math`.
  - Zero external algorithm dependencies; completely pure.
  - Computes both topological proximity (`hops`) and stochastic likelihood (`reach_probability`).
- **Phase 1 Test Suite**:
  - `backend/tests/test_blast.py` containing 7 test cases covering edge cases, hand-calculated fixture values, and NetworkX equivalence tests.
- **Decision Documentation**:
  - Documented ADR-008 in `docs/DECISIONS.md` establishing logarithmic transformation $w = -\ln(p)$ and 4-decimal precision rounding.

---

## 3. File Map
- `.gitignore`: Global ignore rules for Python bytecode, virtual environments, SQLite databases, and Node modules.
- `README.md`: Project summary, architecture overview, and instructions for running backend, tests, and frontend.
- `HANDOFF.md`: This handoff document with verification logs and Phase 2 instructions.
- `docs/ROADMAP.md`: Master roadmap outlining all 9 phases.
- `docs/ARCHITECTURE.md`: Technical architecture describing 3-tier layering, graph data models, and algorithm mechanics.
- `docs/DECISIONS.md`: Architectural Decision Records (ADRs) documenting design rationale (ADR-001 to ADR-008).
- `docs/expected_values.md`: Hand-calculated and script-verified numerical values for tests.
- `docs/API_CONTRACT.md`: Full REST API contract specifying request/response payloads and error handling.
- `docs/mock/`: 12 realistic mock response files for frontend testing.
- `backend/requirements.txt`: Python package requirements (`Flask`, `pytest`, `networkx`).
- `backend/pytest.ini`: Pytest configuration setting pythonpath and test discovery.
- `backend/planner/__init__.py`: Planner package initialization.
- `backend/planner/core/__init__.py`: Pure core module package initialization.
- `backend/planner/core/models.py`: Dataclasses and enums for nodes, edges, incidents, and algorithm outputs.
- `backend/planner/core/schema.py`: Validation logic enforcing data integrity and returning all error messages.
- `backend/planner/core/loader.py`: JSON and dictionary parser constructing validated `Network` instances.
- `backend/planner/core/graph.py`: Plain `Network` data container with adjacency indices and `without_node()`.
- `backend/planner/core/blast.py`: Implemented BFS blast radius and maximum reach probability engine.
- `backend/planner/core/scoring.py`: Contract stub for score calculation and versioned `IncidentQueue`.
- `backend/planner/core/paths.py`: Contract stub for Dijkstra shortest path and containment recommendation.
- `backend/planner/core/restore.py`: Contract stub for iterative DFS cycle detection and topological restore order.
- `backend/planner/core/simulate.py`: Contract stub for strategy simulation (FCFS, severity-only, graph-aware).
- `backend/planner/api/__init__.py`: Flask API package initialization.
- `backend/planner/api/app.py`: Flask application factory with `GET /health`.
- `backend/planner/db/__init__.py`: Database package initialization.
- `backend/planner/db/schema.sql`: DDL schema for SQLite tables (scenarios, nodes, edges, incidents, results).
- `backend/planner/db/init_db.py`: Database initializer creating `backend/data/planner.db`.
- `backend/data/worked_example.json`: Exact 7-node canonical fixture from challenge.
- `backend/data/demo_network.json`: 20-node realistic enterprise network fixture.
- `backend/tests/__init__.py`: Test package initialization.
- `backend/tests/test_schema.py`: Unit tests asserting rejection of invalid schema conditions.
- `backend/tests/test_loader.py`: Unit tests verifying loader behavior, `ValidationError`, and `GET /health`.
- `backend/tests/test_fixtures.py`: Unit tests verifying shapes and properties of fixture files.
- `backend/tests/test_blast.py`: Unit tests verifying blast radius against hand-calculated values and NetworkX.
- `frontend/`: Vite + React + Cytoscape UI displaying worked-example graph.

---

## 4. How to Run

### Run Tests
```powershell
py -m pytest -q backend/tests -o pythonpath=backend
```

### Run Backend Health Check
```powershell
$env:PYTHONPATH = "backend"
py -m flask --app planner.api.app:create_app run --port 5000
```

### Run Frontend
```powershell
cd frontend
npm run dev
```

---

## 5. Contracts
- `blast.blast_radius(network: Network, source_id: str) -> dict[str, dict[str, int | float]]`
  - Input: `Network` instance, string `source_id`.
  - Output: Dictionary mapping reachable node IDs to `{"hops": int, "reach_probability": float}`.
  - Guarantees: Does not include `source_id`. Returns `{}` if node not found or has no reachable neighbors.

---

## 6. Verification
The test suite was run and verified on the local environment:

```
> py -m pytest -q backend/tests -o pythonpath=backend
..........................                                               [100%]
26 passed in 0.33s
```

All 26 test cases passed:
- `worked_example` LT Blast verified:
  - `L`: hops 1, reach_probability 0.80
  - `A`: hops 1, reach_probability 0.40
  - `D`: hops 2, reach_probability 0.56
  - `B`: hops 2, reach_probability 0.40
- `P` (isolated): returns `{}`.
- `LT` without `L`: returns `{"A": {"hops": 1, "reach_probability": 0.40}, "D": {"hops": 2, "reach_probability": 0.24}}`.
- `demo_network` LAPTOP-ENG: all 9 reachable nodes matched expected values.
- Cycle tolerance: graphs with bidirectional edges terminate without infinite loop and compute maximal probability path.
- Independent verification against `networkx` passed across all reachable sets, hops, and shortest-path probabilities.

---

## 7. Decisions and Assumptions
- **ADR-008**: Maximum reach probability is computed by mapping edge probabilities to $w = -\ln(p)$ and solving single-source shortest path using Dijkstra, then recovering probability via $\exp(-D)$ rounded to 4 decimal places.
- **Node Exemption**: The incident source node itself is excluded from its own blast radius mapping.

---

## 8. Open Questions & Risks
- When incidents occur on isolated nodes (e.g. Printer `P`), their blast radius is empty, yielding `reachable_weighted_criticality = 0`. Impact is therefore strictly equal to `own_criticality`. This is verified and handled smoothly.

---

## 9. Next Phase (Phase 2) Instructions
### Goals
Implement incident prioritization scoring and the dynamic max-heap incident queue in `backend/planner/core/scoring.py`.

### Specifications
1. **`compute_score(network: Network, incident: Incident) -> ScoreBreakdown`**:
   - `own_criticality = network.nodes[incident.node_id].criticality`.
   - `blast = blast_radius(network, incident.node_id)`.
   - `reachable_weighted_criticality = sum(network.nodes[v].criticality * data["reach_probability"] for v, data in blast.items())`.
   - `impact = own_criticality + reachable_weighted_criticality`.
   - `score = incident.severity * incident.confidence * impact`.
   - Return `ScoreBreakdown(severity, confidence, own_criticality, reachable_weighted_criticality, impact, score)`.
2. **`IncidentQueue` Max-Heap**:
   - Store entries in Python `heapq` using negative score tuples: `(-score, incident.timestamp, incident.id, version)`.
   - Implement `push(incident, score)`: inserts entry and tracks incident version.
   - Implement `update(incident_id, new_score)`: increments version and inserts new tuple (lazy update).
   - Implement `pop()`: discards stale versions, returns `(Incident, float)` with highest score.
   - Implement `peek()`: returns top `(Incident, float)` without popping.
   - Implement `ranked()`: returns list of all current `(Incident, float)` tuples sorted by score descending.
   - Implement `__len__()`: returns number of active incidents.
   - Tie-breaking: earlier ISO timestamp ranks ahead when scores are equal.
3. **Tests to Add in `backend/tests/test_scoring.py`**:
   - Exact score assertion for `worked_example.json`:
     - `INC-1`: impact 20.80, score 49.92.
     - `INC-2`: impact 1.00, score 8.10.
   - Strategy comparison assertion:
     - Graph-aware queue pop order: `INC-1` first, `INC-2` second.
     - Severity-only sort order: `INC-2` first (severity 9), `INC-1` second (severity 3).
   - Lazy update verification: updating an incident's score dynamically reprioritizes the queue without corrupting heap invariant.
   - Timestamp tie-breaking verification: two incidents with identical score break ties with earlier timestamp first.

---

## 10. Rules for Future Phases
1. Update `HANDOFF.md` at the conclusion of every phase.
2. Keep `backend/planner/core/` pure: no Flask, no database, no global state.
3. Validate against `docs/expected_values.md`.
