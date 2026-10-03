# Cyber Incident Response Planner
*DAA Hackathon - Problem #92 Prototype*

An algorithm-centric decision support prototype that prioritizes cyber incidents and models lateral attack dependencies and functional service requirements to determine response ordering and containment routes.

---

## Core Algorithms & Architectural Highlights
1. **Explainable Priority Queue (Max-Heap)**: Ranks incidents using dynamic score:
   $$\text{Score} = \text{Severity} \times \text{Confidence} \times \text{Impact}$$
   where $\text{Impact} = \text{Own Criticality} + \sum_{v \in \text{blast}} (\text{Criticality}(v) \times \text{Reach Probability}(v))$.
   - Implemented via a versioned max-heap (`IncidentQueue`) with $O(\log n)$ lazy updates and deterministic timestamp tie-breaking.
2. **Blast Radius (BFS + Dijkstra Reach Probability)**:
   - Traverses directed lateral network edges to compute unweighted hop distances (BFS).
   - Solves maximum path probability products by minimizing additive edge weights $w = -\ln(p) \ge 0$ using Dijkstra's algorithm.
3. **Most Probable Attack Paths (Dijkstra)**:
   - Identifies high-risk attack routes targeting critical assets ($\text{criticality} \ge 8$).
   - Returns path sequences, additive weights, and overall path probabilities $P = \exp(-\text{distance})$.
4. **Differential Containment Recommendation**:
   - Evaluates candidate isolation points. Recomputes network risk before vs. after isolating nodes via pure immutable transformations (`without_node`).
   - Weighs risk reduction percentage against operational disruption cost (node criticality).
5. **Dependency-Safe Restoration Order (Iterative DFS)**:
   - Traverses service dependency requirements ($u \to v$ means $u$ requires $v$).
   - Generates valid topological recovery sequences ensuring prerequisites are operational before dependent services start.
   - Detects circular dependencies via a three-color state machine without hitting recursion limits (tested up to 2,500+ nodes).
6. **Strategy Simulation Engine**:
   - Deterministic discrete event simulator comparing First-Come-First-Served (FCFS), Severity-Only, and Graph-Aware response policies.
   - Proves that Graph-Aware prioritization substantially reduces aggregate lateral exposure damage compared to traditional Severity-Only sorting.

---

## Directory Layout
```
Firebreak-Cordon/
  ├── README.md               # Project overview and run guide
  ├── HANDOFF.md              # Full handoff documentation & test logs
  ├── .gitignore              # Ignored build, env, and DB artifacts
  ├── docs/
  │   ├── ROADMAP.md          # 9-phase hackathon roadmap
  │   ├── ARCHITECTURE.md     # System architecture & mathematical foundations
  │   ├── DECISIONS.md        # Architectural Decision Records (ADR-001 to ADR-008)
  │   ├── expected_values.md  # Hand-calculated reference values
  │   ├── API_CONTRACT.md     # REST API specification
  │   └── mock/               # Mock API JSON payloads
  ├── backend/
  │   ├── requirements.txt    # Python dependencies
  │   ├── pytest.ini          # Pytest configuration
  │   ├── planner/
  │   │   ├── core/           # Pure algorithms (blast, scoring, paths, restore, simulate)
  │   │   ├── api/            # Flask REST API application factory
  │   │   └── db/             # SQLite schema and initializer
  │   ├── data/               # Fixtures: worked_example.json, demo_network.json
  │   └── tests/              # Test suite (61 tests covering all engines & benchmarks)
  └── frontend/               # Vite + React + Cytoscape UI
```

---

## How to Run

### 1. Run Backend Tests & Benchmarks
Requirements: Python 3.10+ (tested on Python 3.13)

```powershell
# Run the complete test suite (61 tests in < 0.5s)
py -m pytest -q backend/tests -o pythonpath=backend
```

### 2. Run Flask API Backend
```powershell
$env:PYTHONPATH = "backend"
py -m flask --app planner.api.app:create_app run --port 5000
```
Health endpoint verification:
```powershell
curl http://127.0.0.1:5000/health
```

### 3. Run React Frontend Interface
Requirements: Node.js 18+

```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173/` in your browser.

---

## Interactive Demo Story Walkthrough
1. **The Core Dilemma**:
   - In the **Worked Example**, `INC-1` is an alert on a Laptop (`LT`) with low raw severity (3/10) but connected to the enterprise authentication server (`L`) and database (`D`).
   - `INC-2` is an alert on a Printer (`P`) with high raw severity (9/10), but completely isolated from core network assets.
2. **Priority Queue View (⚡)**:
   - Observe how Graph-Aware prioritization scores `INC-1` at **49.92** and `INC-2` at **8.10**, correctly promoting the low-severity laptop to Rank #1.
3. **Attack Paths & Containment View (🎯)**:
   - Inspect the most probable attack path `LT -> L -> D` ($P = 56\%$).
   - Click "Apply Isolation" on node `L` to see how cutting `L` reduces `LT`'s risk score by **65.38%** (from 49.92 down to 17.28).
4. **Restore Plan View (🔄)**:
   - Review the topological recovery pipeline ensuring database `D` and login `L` are online before app `A`, and `A` before web `W`.
5. **Simulation Comparison View (📊)**:
   - Observe how Graph-Aware containment neutralizes the laptop immediately, slashing accumulated damage compared to the Severity-Only approach.

---

## UI Theme & Credits
The dashboard features an animated night-mountain backdrop with translucent glassmorphic panels preserving full WCAG AA contrast.
- *Background effect: ThreeUI Cloud Field (MIT, © Meng To).*
- Accessibility & Performance: Uses code-splitting via `React.lazy`, supports a static gradient fallback for `prefers-reduced-motion: reduce`, and an optional half-resolution `?lite=1` mode.

