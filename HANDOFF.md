# Phase 5 Handoff: Cyber Incident Response Planner

## 1. Status
- **Phase Completed**: Phase 5 (Simulation & Strategy Comparison)
- **Date**: October 3, 2026
- **What is done**:
  - `run_strategies(network, incidents, seed)` implemented in `backend/planner/core/simulate.py`:
    - Compares 3 distinct operational strategies: `"fcfs"` (First-Come-First-Served), `"severity_only"`, and `"graph_aware"`.
    - Fully deterministic execution via explicit random `seed`.
    - Simulates discrete time steps where uncontained incidents inflict lateral damage proportional to their impact and severity.
    - Demonstrates that `graph_aware` strategy cuts overall system damage by isolating high-impact lateral pivots (such as `LT` and `LAPTOP-ENG`) early.
  - Comprehensive unit test suite in `backend/tests/test_simulate.py`:
    - Verified handling orders for `worked_example.json` (`fcfs`: `INC-1, INC-2`; `severity_only`: `INC-2, INC-1`; `graph_aware`: `INC-1, INC-2`).
    - Verified that `graph_aware` accumulates significantly less damage than `severity_only`.
    - Verified 100% determinism with identical seeds.
    - Verified edge cases (zero incidents).
    - Verified enterprise `demo_network.json` behavior.
  - All 47 unit tests passing.
- **What is NOT done** (scheduled for future phases):
  - Flask API implementation of all endpoints (Phase 6).
  - Interactive React frontend panels and API integration (Phase 7).
  - Performance benchmarks and final polish (Phase 8).

---

## 2. What Was Built
- **Discrete Event Simulator (`simulate.py`)**:
  - Multi-round simulation tracking ongoing lateral exposure damage.
  - Strategy comparative analysis (`fcfs`, `severity_only`, `graph_aware`).
  - Strict determinism via seed parameter.
- **Unit Test Suite (`test_simulate.py`)**:
  - 5 tests covering orders, damage reduction, reproducibility, and fixture evaluations.

---

## 3. File Map
- `.gitignore`: Global ignore rules.
- `README.md`: Project summary and setup instructions.
- `HANDOFF.md`: This handoff document with verification logs.
- `docs/ROADMAP.md`: Master roadmap.
- `docs/ARCHITECTURE.md`: Architecture and algorithm details.
- `docs/DECISIONS.md`: Architectural Decision Records (ADR-001 to ADR-008).
- `docs/expected_values.md`: Hand-calculated reference values.
- `docs/API_CONTRACT.md`: Full REST API contract.
- `docs/mock/`: 12 realistic mock response files.
- `backend/requirements.txt`: Python package requirements (`Flask`, `pytest`, `networkx`).
- `backend/pytest.ini`: Pytest configuration.
- `backend/planner/__init__.py`: Package init.
- `backend/planner/core/__init__.py`: Pure core module package init.
- `backend/planner/core/models.py`: Dataclasses and enums.
- `backend/planner/core/schema.py`: Validation logic.
- `backend/planner/core/loader.py`: JSON/dict parser.
- `backend/planner/core/graph.py`: Plain `Network` data container.
- `backend/planner/core/blast.py`: BFS blast radius and maximum reach probability engine.
- `backend/planner/core/scoring.py`: Priority score calculation and versioned `IncidentQueue`.
- `backend/planner/core/paths.py`: Dijkstra attack paths and containment recommendation engine.
- `backend/planner/core/restore.py`: Iterative DFS cycle detection and topological restore order engine.
- `backend/planner/core/simulate.py`: Strategy simulation engine comparing FCFS, Severity-Only, and Graph-Aware.
- `backend/planner/api/app.py`: Flask application factory with `GET /health`.
- `backend/planner/db/schema.sql` & `init_db.py`: SQLite persistence layer.
- `backend/data/worked_example.json`: 7-node canonical fixture.
- `backend/data/demo_network.json`: 20-node enterprise network fixture.
- `backend/tests/test_schema.py`: Schema validation unit tests.
- `backend/tests/test_loader.py`: Loader unit tests.
- `backend/tests/test_fixtures.py`: Fixture integrity tests.
- `backend/tests/test_blast.py`: Blast radius unit tests.
- `backend/tests/test_scoring.py`: Priority scoring and queue unit tests.
- `backend/tests/test_paths.py`: Dijkstra attack path and containment unit tests.
- `backend/tests/test_restore.py`: Restore order and cycle detection unit tests.
- `backend/tests/test_simulate.py`: Simulation and strategy comparison unit tests.
- `frontend/`: Vite + React + Cytoscape UI.

---

## 4. How to Run
```powershell
# Run backend pytest suite
py -m pytest -q backend/tests -o pythonpath=backend
```

---

## 5. Contracts
- `simulate.run_strategies(network: Network, incidents: list[Incident], seed: int = 42) -> dict[str, dict[str, Any]]`
  - Returns dictionary with `"fcfs"`, `"severity_only"`, and `"graph_aware"` results containing `"total_damage"` and `"handled_order"`.

---

## 6. Verification
```
> py -m pytest -q backend/tests -o pythonpath=backend
...............................................                          [100%]
47 passed in 0.34s
```
All 47 unit tests passed across all core algorithm engines.

---

## 7. Decisions and Assumptions
- Simulations accrue damage at each time step based on active incidents' current severity and impact.
- Graph-aware strategy dynamically isolates contained assets, reducing downstream lateral exposure for remaining uncontained alerts.

---

## 8. Open Questions & Risks
- None. Simulation operates purely in memory with deterministic outputs.

---

## 9. Next Phase (Phase 6) Instructions
### Goals
Implement all REST API endpoints in `backend/planner/api/app.py` conforming to [docs/API_CONTRACT.md](file:///c:/Users/tejas/Firebreak-Cordon/docs/API_CONTRACT.md).

### Specifications
1. **API Endpoints**:
   - `GET /health`: Health status.
   - `POST /network`: Load full network JSON into active state.
   - CRUD for `/nodes`, `/edges`, `/incidents`, `/scenarios`.
   - `GET /queue`: Returns prioritized incident queue with explainable score breakdowns.
   - `GET /blast-radius/<node_id>`: Returns BFS hops and reach probabilities.
   - `GET /attack-path?from=<source>&to=<target>`: Returns Dijkstra shortest path and probability.
   - `POST /isolate/<node_id>`: Simulates node containment, returns before/after risk scores.
   - `GET /restore-order`: Returns topological order or detected cycle.
   - `POST /simulate`: Simulates response strategies with explicit seed.
2. **Error Handling**:
   - Consistent JSON format: `{"error": {"code": "...", "message": "...", "details": [...]}}` with 400 and 404 HTTP codes.
3. **Tests to Add in `backend/tests/test_api.py`**:
   - Comprehensive test client suite asserting endpoint status codes and response bodies against `worked_example` expectations.

---

## 10. Rules for Future Phases
1. Update `HANDOFF.md` at the conclusion of every phase.
2. Keep `backend/planner/core/` pure.
3. Keep API responses aligned with `docs/API_CONTRACT.md`.
