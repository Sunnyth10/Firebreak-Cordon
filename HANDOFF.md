# Phase 3 Handoff: Cyber Incident Response Planner

## 1. Status
- **Phase Completed**: Phase 3 (Dijkstra Attack Path & Containment Recommendation)
- **Date**: October 3, 2026
- **What is done**:
  - `most_probable_path(network, source_id, target_id)` implemented in `backend/planner/core/paths.py`:
    - Solves shortest path on additive edge costs $w = -\ln(p) \ge 0$ using Dijkstra.
    - Reconstructs exact sequence of nodes along the path via predecessor tracking.
    - Computes total path probability $P = \exp(-D)$ and total additive weight.
    - Returns `PathResult` or `None` if unreachable.
  - `attack_paths_to_critical(network, source_id)` implemented in `backend/planner/core/paths.py`:
    - Discovers all paths from `source_id` to assets with `criticality >= network.meta.critical_threshold`.
    - Returns ordered list of `PathResult` sorted by probability descending.
  - `recommend_containment(network, compromised_ids)` implemented in `backend/planner/core/paths.py`:
    - Evaluates candidate isolation nodes lying on attack paths to critical assets.
    - Calculates `paths_covered`, `risk_before`, `risk_after`, `risk_removed_pct`, and `disruption_cost` (node criticality per ADR-003).
    - Sorts candidate options by highest risk reduction percentage.
  - Comprehensive unit test suite in `backend/tests/test_paths.py`:
    - Verified `worked_example.json` path `LT -> D` selects `LT -> L -> D` ($P=0.56$) over `LT -> A -> D` ($P=0.24$).
    - Verified 3 critical paths from `LT` to `L`, `D`, `B`.
    - Verified containment option for `L` achieves 65.38% risk reduction with disruption cost 9 and 3 paths covered.
    - Verified 20-node `demo_network.json` path `LAPTOP-ENG` to `DB-PRIMARY` via `BASTION-HOST` ($P=0.4284$).
    - Cross-verified path choices and path lengths against `networkx.dijkstra_path` and `networkx.dijkstra_path_length`.
  - All 37 unit tests passing.
- **What is NOT done** (scheduled for future phases):
  - Iterative DFS cycle detection & topological restore ordering (Phase 4).
  - Strategy simulation comparison (Phase 5).
  - Flask algorithm endpoints (Phase 6).
  - Interactive UI panels for path highlight and containment simulation (Phase 7).

---

## 2. What Was Built
- **Shortest Path & Containment Engine (`paths.py`)**:
  - Implemented Dijkstra pathfinding with backtracking reconstruction and logarithmic transformation.
  - Multi-target critical asset discovery.
  - Differential containment simulator evaluating risk reduction vs. disruption cost.
- **Unit Test Suite (`test_paths.py`)**:
  - 6 dedicated unit test cases covering path optimality, critical asset routing, isolation metrics, and NetworkX cross-verification.

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
- `backend/planner/core/restore.py`: Contract stub for iterative DFS cycle detection and topological restore order.
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
- `frontend/`: Vite + React + Cytoscape UI.

---

## 4. How to Run
```powershell
# Run backend pytest suite
py -m pytest -q backend/tests -o pythonpath=backend
```

---

## 5. Contracts
- `paths.most_probable_path(network: Network, source_id: str, target_id: str) -> PathResult | None`
- `paths.attack_paths_to_critical(network: Network, source_id: str) -> list[PathResult]`
- `paths.recommend_containment(network: Network, compromised_ids: list[str]) -> list[ContainmentOption]`

---

## 6. Verification
```
> py -m pytest -q backend/tests -o pythonpath=backend
.....................................                                    [100%]
37 passed in 0.48s
```
All 37 unit tests passed, confirming:
- `worked_example`: `most_probable_path(net, "LT", "D")` returns `["LT", "L", "D"]`, probability 0.56, weight $\approx 0.5798$.
- Paths to critical nodes from `LT` identify `L` (0.80), `D` (0.56), and `B` (0.40).
- Isolating `L` results in:
  - `risk_before`: 49.92
  - `risk_after`: 17.28
  - `risk_removed_pct`: 65.38%
  - `disruption_cost`: 9
  - `paths_covered`: 3
- `demo_network`: `LAPTOP-ENG` to `DB-PRIMARY` optimal path is `['LAPTOP-ENG', 'VPN-GATEWAY', 'AUTH-AD', 'BASTION-HOST', 'DB-PRIMARY']` ($P=0.4284$).
- NetworkX cross-verification passed across all test paths and weights.

---

## 7. Decisions and Assumptions
- Candidate containment nodes are gathered from intermediate and target nodes along attack paths to critical assets (excluding compromised sources).
- Disruption cost is set to the candidate node's `criticality` rating ($1 \dots 10$) per ADR-003.

---

## 8. Open Questions & Risks
- None. Dijkstra with predecessor backtracking scales efficiently ($O((V + E) \log V)$), and differential containment analysis isolates candidate nodes purely via `network.without_node()`.

---

## 9. Next Phase (Phase 4) Instructions
### Goals
Implement iterative DFS cycle detection and dependency-safe restore ordering in `backend/planner/core/restore.py`.

### Specifications
1. **Dependency Direction & Semantics**:
   - `dependency` edges: $u \to v$ means system $u$ requires system $v$ to function.
   - Therefore, system $v$ must be restored and operational **before** system $u$.
   - In topological sort order, $v$ must appear before $u$ ($\text{index}(v) < \text{index}(u)$).
2. **Iterative DFS (Three-Color State)**:
   - Use iterative DFS (avoid recursion depth limits on large or deeply nested graphs).
   - Node states: `WHITE` (unvisited), `GRAY` (in current DFS recursion stack / active path), `BLACK` (fully explored and ordered).
   - If an edge encounters a `GRAY` node, a circular dependency cycle is detected!
   - Backtrack and reconstruct the exact cycle list `[..., node_x, ..., node_x]`.
   - If cyclic, return `RestoreResult(ok=False, order=None, cycle=[...], explanation="...")`.
3. **Topological Order Generation**:
   - When a node turns `BLACK`, append it to the reverse-postorder sequence.
   - Verify that all dependencies precede dependents.
   - If acyclic, return `RestoreResult(ok=True, order=final_order, cycle=None, explanation="...")`.
4. **Tests to Add in `backend/tests/test_restore.py`**:
   - Valid topological order for `worked_example.json`:
     - Assert that `index(D) < index(A)`, `index(L) < index(A)`, and `index(A) < index(W)`.
     - Validates order validity rather than brittle single-permutation comparison.
   - Cycle detection test:
     - Inject dependency cycle $A \to B \to C \to A$.
     - Assert `ok == False` and `cycle` contains the loop.
   - Disconnected DAG restore order:
     - Independent components properly included in restoration sequence.
   - Large deep graph test (e.g. 500+ chain):
     - Iterative DFS handles deep dependency chains without `RecursionError`.

---

## 10. Rules for Future Phases
1. Update `HANDOFF.md` at the conclusion of every phase.
2. Keep `backend/planner/core/` pure.
3. Validate against `docs/expected_values.md`.
