-- Cyber Incident Response Planner Database Schema

CREATE TABLE IF NOT EXISTS scenarios (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    critical_threshold INTEGER DEFAULT 8,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nodes (
    id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    criticality INTEGER NOT NULL CHECK (criticality >= 1 AND criticality <= 10),
    status TEXT NOT NULL DEFAULT 'healthy',
    PRIMARY KEY (id, scenario_id),
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS edges (
    id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('network', 'dependency')),
    probability REAL CHECK (probability IS NULL OR (probability > 0 AND probability <= 1.0)),
    PRIMARY KEY (id, scenario_id),
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS incidents (
    id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    severity INTEGER NOT NULL CHECK (severity >= 1 AND severity <= 10),
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    timestamp TEXT NOT NULL,
    PRIMARY KEY (id, scenario_id),
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS results (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    strategy TEXT NOT NULL,
    seed INTEGER NOT NULL,
    total_damage REAL NOT NULL,
    handled_order TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_nodes_scenario ON nodes(scenario_id);
CREATE INDEX IF NOT EXISTS idx_edges_scenario ON edges(scenario_id);
CREATE INDEX IF NOT EXISTS idx_incidents_scenario ON incidents(scenario_id);
CREATE INDEX IF NOT EXISTS idx_results_scenario ON results(scenario_id);
