# Architectural & Design Decisions

This document records architectural, algorithmic, and data modeling decisions made across all phases.

---

## Decision Log

### ADR-001: Repository Root Directory Structure
- **Context**: The user workspace is rooted at `c:\Users\tejas\Firebreak-Cordon` under git tracking.
- **Decision**: All project folders (`docs/`, `backend/`, `frontend/`) and root deliverables (`README.md`, `HANDOFF.md`, `.gitignore`) reside directly at the repository root.
- **Consequence**: Clean standard layout; tools (`pytest`, `npm`) execute from expected project locations without extra wrapping directories.

### ADR-002: Separation of Network Connectivity and Functional Dependency
- **Context**: Cyber incidents propagate across lateral attack surfaces, while system recovery requires functional service availability.
- **Decision**:
  - `network` edges model attack pivots, have directed orientation $u \to v$ with probability $p \in (0, 1.0]$.
  - `dependency` edges model functional requirements: $u \to v$ means $u$ requires $v$. Probability is not allowed/ignored on dependency edges.
- **Consequence**: Graph queries explicitly specify edge kind (`kind="network"` vs `kind="dependency"`).

### ADR-003: Disruption Cost Modeling for Containment Recommendation
- **Context**: Recommending an isolation point requires balancing risk reduction against operational impact.
- **Decision**: In `paths.recommend_containment`, `disruption_cost` is defined as the target node's `criticality` ($1 \dots 10$).
- **Consequence**: Higher-criticality nodes (e.g., Database criticality 10) carry higher disruption cost if isolated, whereas isolating perimeter or low-criticality nodes incurs minimal disruption penalty.

### ADR-004: Blast Radius Metric Definitions
- **Context**: Incident blast radius requires both topological proximity and probabilistic likelihood.
- **Decision**:
  - `hops`: Fewest edge steps from incident source $s$ to reachable node $v$ via unweighted BFS.
  - `reach_probability`: Maximum product of edge probabilities along any directed network path from $s$ to $v$.
- **Consequence**: Blast radius reports both metrics for every reachable node.

### ADR-005: Dependency Recovery Topological Orientation
- **Context**: A service $A$ cannot operate without its dependency $D$ ($A \to D$).
- **Decision**: In `restore.restore_order`, valid recovery sequences must place all dependencies before their dependents. For edge $u \to v$, $v$ precedes $u$ in restore order.
- **Consequence**: In `worked_example.json` where $A \to D, A \to L, W \to A$, valid orders must have $D$ and $L$ restored before $A$, and $A$ restored before $W$.

### ADR-006: Max-Heap Incident Queue with Versioning
- **Context**: Incidents may update in real time (e.g., criticality changes, new alerts, containment updates) requiring dynamic re-scoring.
- **Decision**: Max-heap implemented over Python's min-heap `heapq` using negative score tuples: `(-score, timestamp, incident_id, version)`. Stale entries are discarded lazily during pop/peek operations. Earlier timestamp breaks score ties deterministically.

### ADR-007: Isolation Semantics
- **Context**: When a node is contained/isolated, how is the graph altered?
- **Decision**: Isolating node $x$ via `network.without_node(x)` returns a new immutable copy of `Network` with node $x$ removed along with all incident network edges. Incident scores and blast radiuses are then recalculated on this sub-network.

### ADR-008: Reach Probability Logarithmic Transformation & Rounding
- **Context**: Multiplying probabilities along paths can suffer from numeric instability and floating-point drift.
- **Decision**: In `blast.blast_radius`, maximum reach probability along any directed network path is solved as a shortest path problem using non-negative additive weights $w = -\ln(p) \ge 0$ via Dijkstra's algorithm. The reach probability is recovered as $\exp(-\text{dist})$ and rounded to 4 decimal places.
- **Consequence**: Guaranteed convergence without negative cycle hazards, exact equivalence with maximum product over paths, and numerical match with hand-calculated reference values.
