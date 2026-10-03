# Phase 4 Handoff: Cyber Incident Response Planner

## 1. Status
- **Phase Completed**: Phase 4 (DFS Cycle Detection & Topological Restore Order)
- **Date**: October 3, 2026
- **What is done**:
  - `restore_order(network)` implemented in `backend/planner/core/restore.py`:
    - Traverses `dependency` edges where $u \to v$ means $u$ requires $v$ to run.
    - True iterative DFS using a three-color state machine (`WHITE=0`, `GRAY=1`, `BLACK=2`) completely eliminating recursion depth limits.
    - Accurately detects circular dependencies via back-edges to `GRAY` nodes, extracting the exact circular path `[v, ..., u, v]`.
    - Produces valid topological recovery sequences ensuring all required dependencies are operational before dependent services start.
  - Comprehensive unit test suite in `backend/tests/test_restore.py`:
    - Verified `worked_example.json` topological sequence: $D$ and $L$ restored before $A$, and $A$ restored before $W$.
    - Verified circular dependency detection and error reporting.
    - Verified 20-node `demo_network.json` acyclic restoration satisfying all 11 dependency constraints.
    - Verified deep dependency chain (2,500 nodes) executing cleanly without `RecursionError`.
    - Cross-verified valid topological ordering against `networkx.is_directed_acyclic_graph` and edge topological precedence.
  - All 42 unit tests passing.
- **What is NOT done** (scheduled for future phases):
  - Strategy simulation comparison (Phase 5).
  - Flask algorithm endpoints (Phase 6).
  - Interactive UI panels for restore ordering and simulation comparison (Phase 7).

---

## 2. What Was Built
- **Iterative Restoration Engine (`restore.py`)**:
  - Robust three-color state machine.
  - Cycle detection with exact back-trace path extraction.
  - Dependency precedence guarantee: $u \to v \implies \text{index}(v) < \text{index}(u)$.
- **Unit Test Suite (`test_restore.py`)**:
  - 5 tests covering correctness, cycle detection, large scale chains (2,500 nodes), and NetworkX comparison.

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
- `backend/planner/core/simulate.py`: Contract stub for strategy simulation.
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
- `frontend/`: Vite + React + Cytoscape UI.

---

## 4. How to Run
```powershell
# Run backend pytest suite
py -m pytest -q backend/tests -o pythonpath=backend
```

---

## 5. Contracts
- `restore.restore_order(network: Network) -> RestoreResult`
  - Returns `RestoreResult(ok=True, order=[...], cycle=None, explanation="...")` when acyclic.
  - Returns `RestoreResult(ok=False, order=None, cycle=[...], explanation="...")` when cyclic.

---

## 6. Verification
```
> py -m pytest -q backend/tests -o pythonpath=backend
..........................................                               [100%]
42 passed in 0.29s
```
All 42 unit tests passed, confirming:
- `worked_example`: topological sequence guarantees $D$ and $L$ precede $A$, and $A$ precedes $W$.
- Cycle detection successfully isolates loops ($S_1 \to S_2 \to S_3 \to S_1$).
- `demo_network`: all 11 dependency pairs satisfy order precedence across 20 nodes.
- 2,500-node linear chain traverses and orders without hitting recursion limits.
- Independent verification against `networkx` DAG topological constraints passed.

---

## 7. Decisions and Assumptions
- The dependency relation $u \to v$ denotes that system $u$ requires system $v$ to function. In recovery order, $v$ must be restored before $u$.
- Graph cycles strictly prevent valid recovery and return `ok=False` with the detected cycle path.

---

## 8. Open Questions & Risks
- None. Iterative three-color DFS has $O(V + E)$ time complexity and avoids call-stack overflow.

---

## 9. Next Phase (Phase 5) Instructions
### Goals
Implement discrete event strategy simulation in `backend/planner/core/simulate.py`.

### Specifications
1. **Simulation Model**:
   - Compare three distinct operational strategies:
     1. `"fcfs"`: First-Come-First-Served (order of arrival timestamp).
     2. `"severity_only"`: Highest severity first (descending raw severity).
     3. `"graph_aware"`: Priority queue order using dynamic score $S = \text{sev} \times \text{conf} \times \text{impact}$.
   - Deterministic execution: accept an explicit integer `seed` to seed `random.Random(seed)`.
   - Discrete time ticks / handling rounds:
     - While active incidents remain:
       - Selected incident is contained/mitigated.
       - Unhandled incidents accrue damage at each time step proportional to their current impact.
       - Total damage accumulated is recorded.
   - Return dictionary structure matching API contract:
     ```python
     {
         "fcfs": {"total_damage": float, "handled_order": list[str]},
         "severity_only": {"total_damage": float, "handled_order": list[str]},
         "graph_aware": {"total_damage": float, "handled_order": list[str]}
     }
     ```
2. **Tests to Add in `backend/tests/test_simulate.py`**:
   - Determinism test: identical seeds produce identical total damage and handled order.
   - Strategy differentiation test:
     - On `worked_example.json`, assert that `graph_aware` handles `INC-1` first, `severity_only` handles `INC-2` first, and `fcfs` handles `INC-1` first.
     - Graph-aware accumulates lower total lateral damage than severity-only due to containing high-impact asset `LT` earlier.

---

## 10. Rules for Future Phases
1. Update `HANDOFF.md` at the conclusion of every phase.
2. Keep `backend/planner/core/` pure.
3. Validate against `docs/expected_values.md`.
