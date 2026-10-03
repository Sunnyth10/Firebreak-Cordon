# System Architecture: Cyber Incident Response Planner

## 1. Architectural Philosophy & Layering

The system follows a strict 3-tier decoupling to ensure algorithm correctness, deterministic testability, and UI responsiveness:

```
[ Frontend: React + Cytoscape.js ]
              │ HTTP / JSON
              ▼
[ API Layer: Flask (backend/planner/api/) ]
  - Input validation, route binding, JSON serialization
  - Persistence via SQLite (backend/planner/db/)
              │ In-memory objects
              ▼
[ Core Algorithm Engine: Pure Python (backend/planner/core/) ]
  - Zero I/O, zero Flask, zero global state
  - Python standard library only (heapq, collections, math)
  - Pure mathematical and graph transformations
```

### Constraints & Invariants
1. **Core Purity**: Code in `backend/planner/core/` must never import Flask, access filesystem/network, or rely on mutable module-level state.
2. **Algorithm Implementation**: Core algorithms must be implemented using standard Python structures (`heapq`, `collections.deque`, `math`). External graph libraries (`networkx`) are permitted **only** inside tests as an independent verification reference.
3. **Frontend Role**: The React frontend is strictly a presentation and interaction layer. It contains no algorithmic scoring, pathfinding, or ordering logic.
4. **Determinism**: Any probabilistic or simulation component must accept an explicit random `seed`.

---

## 2. Graph & Data Modeling

The graph separates physical/network connectivity from functional dependency:

### Edge Kinds
1. **`network` Edges**:
   - Represents lateral movement capability: attacker at `source` can pivot to `target`.
   - Directed edge with transmission probability $p \in (0, 1.0]$.
   - Edge weight for shortest-path routing: $w = -\ln(p) \ge 0$.
2. **`dependency` Edges**:
   - Represents functional system requirement: `source` requires `target` to function.
   - Directed edge without probability (unweighted).
   - Inversion semantics: When restoring systems, `target` must be online before `source` can start.

### Graph Representation in Memory
`Network` (`backend/planner/core/graph.py`) stores:
- `nodes`: mapping of node id to `Node` object.
- `edges`: mapping of edge id to `Edge` object.
- `network_adj`: adjacency list `dict[str, list[tuple[str, float]]]` mapping `u -> [(v, p)]`.
- `dependency_adj`: adjacency list `dict[str, list[str]]` mapping `u -> [v]`.
- Mutation via functional copies: `network.without_node(node_id)` creates a fresh copy without the specified node and its incident edges.

---

## 3. Mathematical & Algorithmic Foundations

### A. Critical Assets
A node $v$ is classified as a critical asset if:
$$\text{criticality}(v) \ge \text{critical\_threshold} \quad (\text{default: } 8)$$

### B. Blast Radius (BFS + Probability Propagation)
For an incident on node $s$:
- Traverses directed `network` edges.
- For each reachable node $v$:
  - $\text{hops}(s, v)$: Minimum edge distance from $s$ to $v$ via Breadth-First Search (BFS).
  - $\text{reach\_probability}(s, v)$: The maximum product of edge probabilities along any directed network path from $s$ to $v$:
    $$\text{reach\_probability}(s, v) = \max_{\text{path } P} \prod_{e \in P} p_e$$

### C. Impact & Incident Prioritization
1. **Impact**:
   $$\text{impact}(s) = \text{criticality}(s) + \sum_{v \in \text{blast\_radius}(s)} \big(\text{criticality}(v) \times \text{reach\_probability}(s, v)\big)$$
2. **Priority Score**:
   $$\text{score} = \text{severity} \times \text{confidence} \times \text{impact}$$
3. **Queue**: Max-heap ordering by `score` descending. Tie-breaking is resolved by earliest incident `timestamp`.

### D. Most Probable Attack Path (Dijkstra)
- Maximizing path probability $\prod p_i$ is equivalent to minimizing additive cost $\sum -\ln(p_i)$.
- Weights $w_e = -\ln(p_e) \ge 0$ guarantee non-negative edge costs, permitting standard Dijkstra.
- Path probability from distance $D$: $P = \exp(-D)$.

### E. Containment & Node Isolation
- Isolating a node $x$ removes $x$ and all connected network edges.
- Post-isolation blast radius and incident impact are recalculated.
- Risk reduction:
  $$\Delta \text{Risk} = \frac{\text{Risk}_{\text{before}} - \text{Risk}_{\text{after}}}{\text{Risk}_{\text{before}}} \times 100\%$$
- Disruption cost is modeled as $\text{criticality}(x)$.

### F. Dependency-Safe Restore Order (Topological Sort)
- Traverses `dependency` edges.
- Safe startup condition: If $u$ requires $v$ ($u \to v$), $v$ must be operational before $u$.
- Graph must be an acyclic DAG; cycles are detected using iterative DFS (three-color state).

---

## 4. Storage Architecture (SQLite)
The database persists networks, nodes, edges, incidents, scenarios, and execution runs:
- `nodes`: `(id, network_id, name, type, criticality, status)`
- `edges`: `(id, network_id, source, target, kind, probability)`
- `incidents`: `(id, network_id, node_id, severity, confidence, timestamp)`
- `scenarios`: `(id, name, description, created_at)`
- `simulation_results`: `(id, scenario_id, strategy, seed, total_damage, handled_order, created_at)`
