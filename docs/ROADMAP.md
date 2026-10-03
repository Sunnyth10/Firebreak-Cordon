# Project Roadmap: Cyber Incident Response Planner
DAA Hackathon - Problem #92

## Overview
An algorithm-centric prototype for prioritizing cyber incidents and modeling dependencies between affected systems to determine response order and containment routes.

---

## Phase Breakdown

### Phase 0: Foundation and Contracts (Current Phase)
- **Goal**: Establish project architecture, schemas, stubs, fixtures, documentation, and baseline tests.
- **Deliverables**:
  - Pure Python core model definitions and validation logic.
  - Test fixtures (`worked_example.json` and `demo_network.json`).
  - Hand-calculated and script-verified values in `docs/expected_values.md`.
  - Architecture, API contract, and roadmap documentation.
  - Flask app factory with `GET /health`.
  - React + Cytoscape frontend rendering static mock graph.
  - Test suite validating schemas, loaders, and fixture shapes.

### Phase 1: Graph Model & BFS Blast Radius
- **Goal**: Implement graph operations and BFS blast radius calculation.
- **Deliverables**:
  - `Network` queries and mutation (`without_node`).
  - BFS algorithm computing minimum hop distance.
  - Reach probability computation (maximum probability product over all paths).
  - Unit tests asserting exact blast radius results against `worked_example.json`.

### Phase 2: Priority Score & Max-Heap Queue
- **Goal**: Implement incident prioritization with lazy updates.
- **Deliverables**:
  - Score breakdown computation: $\text{impact} = \text{own\_criticality} + \sum (\text{criticality}(v) \times \text{reach\_prob}(v))$, $\text{score} = \text{severity} \times \text{confidence} \times \text{impact}$.
  - `IncidentQueue` based on max-heap with lazy updates and version tracking.
  - Deterministic tie-breaking on earlier incident timestamps.
  - Tests comparing graph-aware ranking vs. severity-only ranking.

### Phase 3: Dijkstra Attack Paths & Containment Recommendation
- **Goal**: Identify most probable attack routes and optimal isolation points.
- **Deliverables**:
  - Dijkstra shortest path with additive edge weights $w = -\ln(p)$, yielding highest probability path $P = \exp(-\text{distance})$.
  - Multi-target attack path discovery to all critical assets ($\ge \text{critical\_threshold}$).
  - Containment recommendation evaluating risk before vs. risk after isolation, risk reduction percentage, and disruption cost.

### Phase 4: DFS Cycle Detection & Topological Restore Order
- **Goal**: Safe service restoration ordering based on dependency graphs.
- **Deliverables**:
  - Iterative DFS cycle detection on dependency edges (avoiding Python recursion limits).
  - Topological sort producing valid recovery sequence (dependencies restored before dependents).
  - Diagnostic reporting for detected cycles.

### Phase 5: Simulation & Strategy Comparison
- **Goal**: Discrete simulation comparing incident response strategies.
- **Deliverables**:
  - Simulation engine with explicit random seed.
  - Comparison of 3 strategies: First-Come-First-Served (FCFS), Severity-Only, and Graph-Aware.
  - Tracking metrics: total accumulated damage, time to containment, handled order.

### Phase 6: Flask REST API
- **Goal**: Expose core algorithms through clean REST endpoints.
- **Deliverables**:
  - Endpoints: `POST /network`, CRUD for nodes/edges/incidents/scenarios.
  - Algorithm endpoints: `GET /queue`, `GET /blast-radius/<node>`, `GET /attack-path`, `POST /isolate/<node>`, `GET /restore-order`, `POST /simulate`.
  - Structured error handling with HTTP 400/404 responses.

### Phase 7: React Frontend & Interactive Visualizations
- **Goal**: Rich, intuitive user interface for exploring graph and algorithmic decisions.
- **Deliverables**:
  - Interactive Cytoscape.js canvas styling network vs. dependency edges and node types.
  - Priority queue inspection panel with transparent score breakdowns.
  - Attack path highlighting and one-click containment simulation.
  - Restore order step-by-step viewer and strategy comparison bar/line charts.

### Phase 8: Testing, Benchmarks, Polish & Demo Prep
- **Goal**: Production readiness, cross-verification, and presentation prep.
- **Deliverables**:
  - Comparison tests against independent NetworkX reference algorithms.
  - Performance benchmarks on large graphs (100+ to 1,000+ nodes).
  - Polished user flows, sample scenario loader, and demo walkthrough.

---

## Priority Guidance
- **Must-Have**: Phases 1–3 and a functional UI graph explorer.
- **Should-Have**: Phases 4–5 (Restore ordering and Strategy simulation).
- **Nice-to-Have**: Phase 8 benchmarks and advanced UI animations.
