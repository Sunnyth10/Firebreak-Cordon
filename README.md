# Cyber Incident Response Planner
*DAA Hackathon - Problem #92 Prototype*

An algorithm-centric decision support prototype that prioritizes cyber incidents and models lateral attack dependencies and functional service requirements to determine response ordering and containment routes.

---

## Key Features & Foundations
- **Explainable Incident Prioritization**: Explicit scoring based on severity, detection confidence, own asset criticality, and probabilistic blast radius ($S = \text{sev} \times \text{conf} \times \text{impact}$).
- **Dual Graph Topology**:
  - `network` edges: Lateral attacker propagation with transmission probability $p \in (0, 1.0]$.
  - `dependency` edges: Functional service requirements ($u \to v$ requires $v$ restored before $u$).
- **Pure Core Engine**: `backend/planner/core/` is completely decoupled from Flask, SQLite, and network I/O.
- **Visual Graph Explorer**: React + Cytoscape.js interface rendering assets sized by criticality with edge kind styling.

---

## Directory Layout
```
Firebreak-Cordon/
  ├── README.md               # Overview and setup instructions
  ├── HANDOFF.md              # Phase handoff documentation and verification logs
  ├── .gitignore              # Ignored build, env, and DB artifacts
  ├── docs/
  │   ├── ROADMAP.md          # 9-phase hackathon progression plan
  │   ├── ARCHITECTURE.md     # Architectural constraints and algorithms
  │   ├── DECISIONS.md        # Architectural Decision Records (ADRs)
  │   ├── API_CONTRACT.md     # REST endpoint contracts and payloads
  │   ├── expected_values.md  # Hand-calculated reference values
  │   └── mock/               # Mock JSON API responses
  ├── backend/
  │   ├── requirements.txt    # Python dependencies
  │   ├── pytest.ini          # Pytest configuration
  │   ├── planner/
  │   │   ├── core/           # Pure algorithm stubs and data models
  │   │   ├── api/            # Flask application factory (GET /health)
  │   │   └── db/             # SQLite schema and initializer
  │   ├── data/               # Network fixtures (worked_example, demo_network)
  │   └── tests/              # Pytest test suite
  └── frontend/               # Vite + React + Cytoscape UI
```

---

## Getting Started

### 1. Backend Setup & Tests
Requirements: Python 3.10+ (tested on Python 3.13)

```powershell
# Install backend requirements
py -m pip install -r backend/requirements.txt

# Run pytest suite
py -m pytest -q backend/tests -o pythonpath=backend
```

### 2. Database Initialization
```powershell
py backend/planner/db/init_db.py
```
This initializes `backend/data/planner.db` with tables for scenarios, nodes, edges, incidents, and results.

### 3. Run Flask Backend API
```powershell
$env:PYTHONPATH = "backend"
py -m flask --app planner.api.app:create_app run --port 5000
```
Verify health check:
```powershell
curl http://127.0.0.1:5000/health
```

### 4. Frontend Setup & Run
Requirements: Node.js 18+

```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173/` in your browser to view the interactive worked-example graph.
To build for production:
```powershell
npm run build
```
