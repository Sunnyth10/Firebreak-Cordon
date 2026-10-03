# Phase 2 Handoff: Cyber Incident Response Planner

## 1. Status
- **Phase Completed**: Phase 2 (Priority Score & Max-Heap Queue)
- **Date**: October 3, 2026
- **What is done**:
  - `compute_score(network, incident)` implemented in `backend/planner/core/scoring.py`:
    - Computes own asset criticality, reachable blast radius, and reachable weighted criticality.
    - $\text{impact} = \text{own\_criticality} + \sum (\text{criticality}(v) \times \text{reach\_probability}(v))$.
    - $\text{score} = \text{severity} \times \text{confidence} \times \text{impact}$.
    - Returns explainable `ScoreBreakdown` dataclass.
  - `IncidentQueue` max-heap implemented in `backend/planner/core/scoring.py`:
    - Versioned entries with lazy update mechanism.
    - Python `heapq` max-heap using `-score` and deterministic timestamp tie-breaking.
    - Full API: `push`, `update`, `pop`, `peek`, `ranked`, `__len__`, `__contains__`.
  - Comprehensive unit test suite in `backend/tests/test_scoring.py`:
    - Verified exact scores on `worked_example.json`: `INC-1` = 49.92, `INC-2` = 8.10.
    - Verified strategy comparison: graph-aware queue orders `INC-1` first, whereas severity-only orders `INC-2` first.
    - Verified dynamic lazy updates and heap invariant preservation.
    - Verified timestamp tie-breaking for equal scores.
    - Verified 20-node `demo_network.json` scoring (`INC-DEMO-01` = 94.60, `INC-DEMO-02` = 9.50).
  - All 31 unit tests passing.
- **What is NOT done** (scheduled for future phases):
  - Dijkstra attack path discovery & containment recommendation (Phase 3).
  - Iterative DFS cycle detection & topological restore ordering (Phase 4).
  - Strategy simulation comparison (Phase 5).
  - Flask algorithm endpoints (Phase 6).
  - Interactive UI panels for queue and containment (Phase 7).

---

## 2. What Was Built
- **Scoring Engine**: Transparent priority score breakdown calculation based on threat metrics and network blast radius.
- **Max-Heap Incident Queue**: Efficient $O(\log n)$ priority queue with lazy updates discarding stale entries on access.
- **Unit Tests**: 5 dedicated tests in `backend/tests/test_scoring.py` validating scores, rankings, updates, and tie-breakers.

---

## 3. File Map
- `.gitignore`: Global ignore rules.
- `README.md`: Project documentation and setup instructions.
- `HANDOFF.md`: This handoff document with verification logs.
- `docs/ROADMAP.md`: Master roadmap outlining all 9 phases.
- `docs/ARCHITECTURE.md`: Technical architecture and algorithmic foundations.
- `docs/DECISIONS.md`: Architectural Decision Records (ADR-001 to ADR-008).
- `docs/expected_values.md`: Hand-calculated and script-verified numerical values.
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
- `backend/planner/core/paths.py`: Contract stub for Dijkstra shortest path and containment recommendation.
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
- `frontend/`: Vite + React + Cytoscape UI.

---

## 4. How to Run
```powershell
# Run backend pytest suite
py -m pytest -q backend/tests -o pythonpath=backend
```

---

## 5. Contracts
- `scoring.compute_score(network: Network, incident: Incident) -> ScoreBreakdown`
  - Returns `ScoreBreakdown(severity, confidence, own_criticality, reachable_weighted_criticality, impact, score)`.
- `scoring.IncidentQueue`
  - `push(incident: Incident, score: float) -> None`
  - `update(incident_id: str, new_score: float) -> None`
  - `pop() -> tuple[Incident, float]`
  - `peek() -> tuple[Incident, float] | None`
  - `ranked() -> list[tuple[Incident, float]]`
  - `__len__() -> int`

---

## 6. Verification
```
> py -m pytest -q backend/tests -o pythonpath=backend
...............................                                          [100%]
31 passed in 0.34s
```
All 31 unit tests passed, confirming:
- `worked_example`: `INC-1` score 49.92, `INC-2` score 8.10.
- Graph-aware queue pops `INC-1` first, severity-only orders `INC-2` first.
- Queue lazy updates dynamically reorder heap elements.
- Timestamp tie-breaking prioritizes earlier alerts.
- `demo_network`: `INC-DEMO-01` score 94.60, `INC-DEMO-02` score 9.50.

---

## 7. Decisions and Assumptions
- Max-heap is implemented over min-heap with negative scores: `(-score, timestamp, incident_id, version)`.
- Stale versions are purged lazily during heap top access (`pop`, `peek`, `ranked`).
- Ties are broken deterministically by ISO 8601 timestamp string comparison (earlier timestamp has lower alphabetical string value and pops first).

---

## 8. Open Questions & Risks
- None. Heap invariants and lazy version updates operate with $O(\log n)$ push/pop and $O(1)$ len/peek.

---

## 9. Next Phase (Phase 3) Instructions
### Goals
Implement most probable attack paths and containment recommendation in `backend/planner/core/paths.py`.

### Specifications
1. **`most_probable_path(network: Network, source_id: str, target_id: str) -> PathResult | None`**:
   - Dijkstra shortest path under edge weights $w = -\ln(p) \ge 0$.
   - Tracks node predecessor pointers to reconstruct the exact path list `[source_id, ..., target_id]`.
   - Path probability = $\exp(-\text{total\_weight})$.
   - Returns `PathResult(nodes, probability, total_weight)` or `None` if unreachable.
2. **`attack_paths_to_critical(network: Network, source_id: str) -> list[PathResult]`**:
   - Identifies all nodes with `criticality >= network.meta.critical_threshold`.
   - Computes `most_probable_path` from `source_id` to each critical asset.
   - Returns list of `PathResult` sorted by highest probability descending.
3. **`recommend_containment(network: Network, compromised_ids: list[str]) -> list[ContainmentOption]`**:
   - Finds candidate containment nodes whose isolation interrupts attack paths to critical assets.
   - For each candidate node:
     - `paths_covered`: count of critical paths passing through this node.
     - `risk_before`: initial score of active incidents.
     - `risk_after`: recomputed score after `network.without_node(candidate)`.
     - `risk_removed_pct`: $(( \text{risk\_before} - \text{risk\_after} ) / \text{risk\_before}) \times 100$.
     - `disruption_cost`: candidate node criticality (ADR-003).
   - Returns list of `ContainmentOption` sorted by highest risk reduction percentage descending.
4. **Tests to Add in `backend/tests/test_paths.py`**:
   - `worked_example` LT -> D path: `['LT', 'L', 'D']`, probability 0.56, weight $\approx 0.5798$.
   - Critical paths from LT: targets `D`, `L`, `B` (all criticality $\ge 8$).
   - Containment recommendation on node `L`: risk before 49.92, risk after 17.28, risk reduction 65.38%, disruption cost 9.
   - Demo network path `LAPTOP-ENG` -> `DB-PRIMARY`: `['LAPTOP-ENG', 'VPN-GATEWAY', 'AUTH-AD', 'BASTION-HOST', 'DB-PRIMARY']`, probability 0.4284.

---

## 10. Rules for Future Phases
1. Update `HANDOFF.md` at the conclusion of every phase.
2. Keep `backend/planner/core/` pure.
3. Validate against `docs/expected_values.md`.
