# Phase 0 Handoff: Cyber Incident Response Planner

## 1. Status
- **Phase Completed**: Phase 0 (Foundation and Contracts)
- **Date**: October 3, 2026
- **What is done**:
  - Pure Python core data models (`Node`, `Edge`, `Incident`, `NetworkMeta`, `ScoreBreakdown`, `PathResult`, `ContainmentOption`, `RestoreResult`).
  - Validation engine with comprehensive multi-error reporting (`schema.py`).
  - Graph data container (`Network` in `graph.py`) with separate network vs. dependency adjacency lists and immutable `without_node()` isolation.
  - Loader (`loader.py`) with `ValidationError` and file/json loading.
  - Test fixtures: `worked_example.json` (exact 7-node spec) and `demo_network.json` (20-node enterprise layout).
  - Hand-calculated and script-verified expected values recorded in `docs/expected_values.md`.
  - Core algorithm module stubs raising `NotImplementedError` with precise contracts (`blast.py`, `scoring.py`, `paths.py`, `restore.py`, `simulate.py`).
  - API documentation (`docs/API_CONTRACT.md`) and mock JSON responses in `docs/mock/`.
  - Architecture (`docs/ARCHITECTURE.md`), Decisions (`docs/DECISIONS.md`), and Roadmap (`docs/ROADMAP.md`).
  - SQLite database schema (`schema.sql`) and database initialization script (`init_db.py`).
  - Flask application factory with working `GET /health` endpoint.
  - Vite + React + Cytoscape.js frontend displaying the worked-example network with nodes sized by criticality and distinct edge styles.
  - Test suite (`test_schema.py`, `test_loader.py`, `test_fixtures.py`) passing with 19/19 passing tests.
- **What is NOT done** (deferred by design to future phases):
  - BFS blast radius algorithm (Phase 1).
  - Priority scoring & versioned max-heap queue (Phase 2).
  - Dijkstra shortest path under $w = -\ln(p)$ & containment recommendation (Phase 3).
  - Iterative DFS cycle detection & topological sort (Phase 4).
  - Discrete event simulation & strategy comparison (Phase 5).
  - Flask algorithm endpoints (Phase 6).
  - Full interactive frontend panels & live API integration (Phase 7).

---

## 2. What Was Built
- **Pure Core Engine**: Implemented `models.py`, `schema.py`, `loader.py`, and `graph.py` inside `backend/planner/core/` without any Flask, DB, or network dependencies.
- **Algorithm Contracts**: Stubs with typed signatures, contract docstrings, and `raise NotImplementedError` in `blast.py`, `scoring.py`, `paths.py`, `restore.py`, and `simulate.py`.
- **Fixtures & Expected Calculations**: Created `worked_example.json` and `demo_network.json`, and derived all blast radius, impact, priority score, shortest path, and topological restore constraints.
- **Mock Service API**: Defined REST endpoints and produced 12 realistic mock response files in `docs/mock/` with `"_mock": true` flags for non-hand-calculated simulation metrics.
- **Persistence Foundation**: SQLite database schema with indexes and tables for nodes, edges, incidents, scenarios, and results.
- **Interactive UI Scaffold**: Built a Vite React app with Cytoscape.js rendering the worked-example graph, sizing nodes by criticality (1–10), styling network vs dependency edges, and offering node inspection.

---

## 3. File Map
- `.gitignore`: Global git ignore rules for Python bytecode, virtual environments, SQLite databases, and Node modules.
- `README.md`: Project summary, architecture overview, and instructions for running backend, tests, and frontend.
- `HANDOFF.md`: This Phase 0 completion document with verification outputs and Phase 1 instructions.
- `docs/ROADMAP.md`: Master roadmap outlining all 9 phases from foundation to final demo preparation.
- `docs/ARCHITECTURE.md`: Technical architecture describing 3-tier layering, graph data models, and algorithm mechanics.
- `docs/DECISIONS.md`: Architectural Decision Records (ADRs) documenting design rationale and trade-offs.
- `docs/expected_values.md`: Hand-calculated and script-verified numerical values for tests in later phases.
- `docs/API_CONTRACT.md`: Full REST API contract specifying request/response payloads and error handling.
- `docs/mock/health.json`: Mock response for `GET /health`.
- `docs/mock/network.json`: Mock response for full network load (`POST /network`).
- `docs/mock/nodes.json`: Mock response for listing nodes (`GET /nodes`).
- `docs/mock/edges.json`: Mock response for listing edges (`GET /edges`).
- `docs/mock/incidents.json`: Mock response for listing incidents (`GET /incidents`).
- `docs/mock/scenarios.json`: Mock response for listing scenarios (`GET /scenarios`).
- `docs/mock/queue.json`: Mock response for prioritized incident queue (`GET /queue`).
- `docs/mock/blast_radius_LT.json`: Mock response for blast radius calculation (`GET /blast-radius/LT`).
- `docs/mock/attack_path_LT_D.json`: Mock response for most probable attack path (`GET /attack-path`).
- `docs/mock/isolate_L.json`: Mock response for containment simulation (`POST /isolate/L`).
- `docs/mock/restore_order.json`: Mock response for dependency-safe restore ordering (`GET /restore-order`).
- `docs/mock/simulate.json`: Mock response for response strategy simulation (`POST /simulate`).
- `backend/requirements.txt`: Python package requirements (`Flask`, `pytest`, `networkx`).
- `backend/pytest.ini`: Pytest configuration setting pythonpath and test discovery.
- `backend/planner/__init__.py`: Planner package initialization.
- `backend/planner/core/__init__.py`: Pure core module package initialization.
- `backend/planner/core/models.py`: Dataclasses and enums for nodes, edges, incidents, and algorithm outputs.
- `backend/planner/core/schema.py`: Validation logic enforcing data integrity and returning all error messages.
- `backend/planner/core/loader.py`: JSON and dictionary parser constructing validated `Network` instances.
- `backend/planner/core/graph.py`: Plain `Network` data container with adjacency indices and `without_node()`.
- `backend/planner/core/blast.py`: Contract stub for BFS blast radius and maximum reach probability.
- `backend/planner/core/scoring.py`: Contract stub for score calculation and versioned `IncidentQueue`.
- `backend/planner/core/paths.py`: Contract stub for Dijkstra shortest path and containment recommendation.
- `backend/planner/core/restore.py`: Contract stub for iterative DFS cycle detection and topological restore order.
- `backend/planner/core/simulate.py`: Contract stub for strategy simulation (FCFS, severity-only, graph-aware).
- `backend/planner/api/__init__.py`: Flask API package initialization.
- `backend/planner/api/app.py`: Flask application factory with `GET /health`.
- `backend/planner/db/__init__.py`: Database package initialization.
- `backend/planner/db/schema.sql`: DDL schema for SQLite tables (scenarios, nodes, edges, incidents, results).
- `backend/planner/db/init_db.py`: Database initializer creating `backend/data/planner.db`.
- `backend/data/worked_example.json`: Exact 7-node canonical fixture from the hackathon challenge.
- `backend/data/demo_network.json`: 20-node realistic enterprise network fixture.
- `backend/tests/__init__.py`: Test package initialization.
- `backend/tests/test_schema.py`: Unit tests asserting rejection of invalid schema conditions.
- `backend/tests/test_loader.py`: Unit tests verifying loader behavior, `ValidationError`, and `GET /health`.
- `backend/tests/test_fixtures.py`: Unit tests verifying shapes and properties of fixture files.
- `frontend/package.json`: Vite and React project configuration including Cytoscape.js.
- `frontend/vite.config.js`: Vite build and server settings.
- `frontend/index.html`: Web application HTML entry point.
- `frontend/src/main.jsx`: React root mount script.
- `frontend/src/App.jsx`: Main interface rendering Cytoscape graph with nodes sized by criticality.
- `frontend/src/index.css`: Design system tokens, dark theme, and typography styles.
- `frontend/src/worked_example_mock.json`: Local mock fixture used by the frontend interface.

---

## 4. How to Run

### Setup Environment & Dependencies
```powershell
# In repository root:
py -m pip install -r backend/requirements.txt
```

### Run Tests
```powershell
# Run backend pytest suite from root:
py -m pytest -q backend/tests -o pythonpath=backend

# Or from backend directory:
cd backend
py -m pytest -q
cd ..
```

### Initialize Database
```powershell
py backend/planner/db/init_db.py
```

### Run Flask API
```powershell
$env:PYTHONPATH = "backend"
py -m flask --app planner.api.app:create_app run --port 5000
```
Test health endpoint:
```powershell
curl http://127.0.0.1:5000/health
```

### Run Frontend
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173/` in your browser.

---

## 5. Contracts
- **REST API Contracts**: Fully specified in [API_CONTRACT.md](file:///c:/Users/tejas/Firebreak-Cordon/docs/API_CONTRACT.md).
- **Data Models**: Defined in [models.py](file:///c:/Users/tejas/Firebreak-Cordon/backend/planner/core/models.py).
- **Core Function Signatures**:
  - `blast.blast_radius(network: Network, source_id: str) -> dict[str, dict[str, int | float]]`
  - `scoring.compute_score(network: Network, incident: Incident) -> ScoreBreakdown`
  - `scoring.IncidentQueue`: methods `push`, `update`, `pop`, `peek`, `ranked`, `__len__`
  - `paths.most_probable_path(network: Network, source_id: str, target_id: str) -> PathResult | None`
  - `paths.attack_paths_to_critical(network: Network, source_id: str) -> list[PathResult]`
  - `paths.recommend_containment(network: Network, compromised_ids: list[str]) -> list[ContainmentOption]`
  - `restore.restore_order(network: Network) -> RestoreResult`
  - `simulate.run_strategies(network: Network, incidents: list[Incident], seed: int) -> dict[str, dict[str, Any]]`

---

## 6. Verification
The test suite was run and verified on the local environment:

```
> py -m pytest -q backend/tests -o pythonpath=backend
...................                                                      [100%]
19 passed in 0.17s
```

All 19 test cases passed, verifying:
- Valid fixtures (`worked_example.json` and `demo_network.json`) load without error.
- Rejection of `probability = 0` with explicit error message (`ln(0) undefined`).
- Rejection of `probability > 1.0` (e.g. `1.5`).
- Rejection of unknown node references in edges and incidents.
- Rejection of duplicate IDs across nodes, edges, and incidents.
- Rejection of invalid edge kinds.
- Rejection of node criticality out of bounds (e.g. `11`).
- Rejection of incident confidence out of bounds (e.g. `-0.1`).
- Aggregation of multiple schema errors simultaneously.
- Loader file handling, missing file exceptions, and JSON string parsing.
- Flask app factory `GET /health` returning 200 with `{"status": "ok", "version": "0.1.0"}`.
- Worked example structure asserting exactly 7 nodes, 5 network edges, 3 dependency edges, and 2 incidents.
- Pure immutable node isolation via `network.without_node()`.

### Expected Value Verification
Hand calculations were verified using an independent verification script (`verify_script.py` / `compute_demo.py`) yielding:
- `worked_example` LT Blast:
  - `L`: hops 1, reach_probability 0.80
  - `A`: hops 1, reach_probability 0.40
  - `D`: hops 2, reach_probability 0.56
  - `B`: hops 2, reach_probability 0.40
  - Impact(LT) = $2 + 18.8 = 20.80$, Score INC-1 = $3 \times 0.8 \times 20.80 = 49.92$
  - Impact(P) = $1.00$, Score INC-2 = $9 \times 0.9 \times 1.00 = 8.10$
  - Isolate L: Impact(LT) becomes $7.20$, Score becomes $17.28$ ($\approx 65.38\%$ reduction).
- All numbers recorded in [expected_values.md](file:///c:/Users/tejas/Firebreak-Cordon/docs/expected_values.md).

---

## 7. Decisions and Assumptions
All decisions are recorded in [DECISIONS.md](file:///c:/Users/tejas/Firebreak-Cordon/docs/DECISIONS.md):
- **ADR-001**: Workspace root `Firebreak-Cordon` serves as the project root containing `docs/`, `backend/`, and `frontend/`.
- **ADR-002**: Two distinct edge kinds: `network` (directed, probability in $(0, 1.0]$) and `dependency` (unweighted functional requirement).
- **ADR-003**: In `paths.recommend_containment`, `disruption_cost` is defined as the target node's `criticality` (1–10).
- **ADR-004**: Blast radius computes two orthogonal metrics for reachable nodes: `hops` (unweighted BFS) and `reach_probability` (maximum product of path probabilities).
- **ADR-005**: Dependency recovery order enforces that for dependency edge $u \to v$ ($u$ requires $v$), $v$ precedes $u$ in recovery order.
- **ADR-006**: Priority queue is a max-heap with negative score tuples and version tracking for lazy updates.
- **ADR-007**: Isolation creates an immutable copy via `without_node()` without mutating the base network.

---

## 8. Open Questions & Risks
- **Reach Probability Algorithm**: Finding the maximum probability product over arbitrary graphs is equivalent to shortest path with weights $w = -\ln(p)$. Since all $p \in (0, 1.0]$, $w \ge 0$, so Dijkstra or DP reliably avoids negative cycles. In Phase 1, the implementation will integrate this cleanly into `blast.blast_radius`.
- **PowerShell ExecutionPolicy**: On Windows systems, PowerShell blocks `.ps1` execution by default. For frontend commands, use `cmd.exe /c "npx ..."` or `npx.cmd` to bypass policy blocks.

---

## 9. Next Phase (Phase 1) Instructions
### Goals
Implement `backend/planner/core/blast.py` and unit tests in `backend/tests/test_blast.py`.

### Specifications
1. **BFS for Hops**:
   - Traverse `network` edges from `source_id` using `collections.deque`.
   - Record minimum edge count `hops` for every reachable node.
2. **Best-Probability Reach**:
   - Compute maximum path probability product $P = \max \prod p_e$.
   - Transform edge probabilities using $w = -\ln(p)$ and apply Dijkstra or relaxation over reachable nodes.
   - For every reachable node $v$, set `reach_probability = exp(-dist[v])`.
3. **Assert Expected Values**:
   - Test against `worked_example.json`:
     - `blast_radius(net, "LT")` must return:
       - `"L"`: `hops: 1`, `reach_probability: 0.80`
       - `"A"`: `hops: 1`, `reach_probability: 0.40`
       - `"D"`: `hops: 2`, `reach_probability: 0.56`
       - `"B"`: `hops: 2`, `reach_probability: 0.40`
     - `blast_radius(net, "P")` must return `{}` (empty dict).
   - Test against `demo_network.json` for `LAPTOP-ENG` and `PRINTER-HR`.
4. **Tests to Add**:
   - `test_blast_radius_worked_example_lt()`: exact values for LT.
   - `test_blast_radius_isolated_node()`: empty blast radius for P.
   - `test_blast_radius_disconnected_graph()`: verifies nodes with no incoming/outgoing paths.
   - `test_blast_radius_cycle_tolerance()`: network with cycles does not infinite loop and computes optimal probability.

---

## 10. Rules for Future Phases
1. **Update HANDOFF.md**: At the conclusion of every phase, update this document with current status, test verification output, and instructions for the next phase.
2. **Preserve Core Purity**: Never import Flask, SQLite, or perform disk/network I/O inside `backend/planner/core/`.
3. **Contract Stability**: Do not modify function signatures in `core/` or API routes without simultaneously updating `docs/API_CONTRACT.md` and mock files in `docs/mock/`.
4. **Deterministic Execution**: Always pass explicit seeds for stochastic behavior.
