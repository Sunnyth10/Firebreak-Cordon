import React, { useEffect, useRef, useState, useMemo } from 'react';
import cytoscape from 'cytoscape';
import workedExampleData from './worked_example_mock.json';
import demoNetworkData from './demo_network_mock.json';

const API_BASE = 'http://127.0.0.1:5000';

export default function App() {
  const [selectedScenario, setSelectedScenario] = useState('worked_example');
  const [activeTab, setActiveTab] = useState('graph'); // 'graph' | 'queue' | 'paths' | 'restore' | 'simulate'
  const [networkData, setNetworkData] = useState(workedExampleData);
  const [selectedNode, setSelectedNode] = useState(null);
  const [isolatedNodeId, setIsolatedNodeId] = useState(null);
  const [highlightedPath, setHighlightedPath] = useState(null);
  const [edgeFilter, setEdgeFilter] = useState('all'); // 'all' | 'network' | 'dependency'

  // Live API States
  const [apiConnected, setApiConnected] = useState(false);
  const [queueData, setQueueData] = useState([]);
  const [blastData, setBlastData] = useState(null);
  const [attackPaths, setAttackPaths] = useState([]);
  const [containmentOptions, setContainmentOptions] = useState([]);
  const [restorePlan, setRestorePlan] = useState(null);
  const [simResults, setSimResults] = useState(null);

  const containerRef = useRef(null);
  const cyRef = useRef(null);

  // Switch scenario
  useEffect(() => {
    if (selectedScenario === 'worked_example') {
      setNetworkData(workedExampleData);
    } else {
      setNetworkData(demoNetworkData);
    }
    setIsolatedNodeId(null);
    setSelectedNode(null);
    setHighlightedPath(null);
  }, [selectedScenario]);

  // Fetch or fallback data when scenario / networkData changes
  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        // Try connecting to Flask API
        const healthRes = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(1500) });
        if (healthRes.ok) {
          if (!isMounted) return;
          setApiConnected(true);

          // Post current scenario network to API
          await fetch(`${API_BASE}/network`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(networkData),
          });

          // Fetch Queue
          const qRes = await fetch(`${API_BASE}/queue`);
          if (qRes.ok) {
            const qJson = await qRes.json();
            if (isMounted) setQueueData(qJson.queue || []);
          }

          // Fetch Restore Order
          const rRes = await fetch(`${API_BASE}/restore-order`);
          if (rRes.ok) {
            const rJson = await rRes.json();
            if (isMounted) setRestorePlan(rJson);
          }

          // Fetch Simulation
          const sRes = await fetch(`${API_BASE}/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seed: 42 }),
          });
          if (sRes.ok) {
            const sJson = await sRes.json();
            if (isMounted) setSimResults(sJson.strategies || null);
          }
          return;
        }
      } catch (err) {
        // Fallback to client mock
        if (!isMounted) return;
        setApiConnected(false);
      }

      // Offline mock computation fallback
      if (!isMounted) return;
      generateLocalMockData(networkData);
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [networkData]);

  // Generate fallback data if backend is offline
  function generateLocalMockData(data) {
    if (data.nodes.length === 7) {
      // Worked example exact calculations
      setQueueData([
        {
          incident_id: 'INC-1',
          node_id: 'LT',
          score: 49.92,
          breakdown: { severity: 3, confidence: 0.8, own_criticality: 2, reachable_weighted_criticality: 18.8, impact: 20.8, score: 49.92 },
          timestamp: '2026-10-03T10:00:00Z',
        },
        {
          incident_id: 'INC-2',
          node_id: 'P',
          score: 8.10,
          breakdown: { severity: 9, confidence: 0.9, own_criticality: 1, reachable_weighted_criticality: 0.0, impact: 1.0, score: 8.10 },
          timestamp: '2026-10-03T10:05:00Z',
        },
      ]);
      setRestorePlan({
        ok: true,
        order: ['D', 'L', 'A', 'W', 'B', 'LT', 'P'],
        cycle: null,
        explanation: 'Topological order ensures dependencies D and L precede A, and A precedes W.',
      });
      setSimResults({
        fcfs: { total_damage: 89.4, handled_order: ['INC-1', 'INC-2'] },
        severity_only: { total_damage: 133.8, handled_order: ['INC-2', 'INC-1'] },
        graph_aware: { total_damage: 80.4, handled_order: ['INC-1', 'INC-2'] },
      });
      setAttackPaths([
        { nodes: ['LT', 'L'], probability: 0.80, total_weight: 0.22314 },
        { nodes: ['LT', 'L', 'D'], probability: 0.56, total_weight: 0.57982 },
        { nodes: ['LT', 'L', 'B'], probability: 0.40, total_weight: 0.91629 },
      ]);
      setContainmentOptions([
        { node_id: 'L', paths_covered: 3, risk_before: 49.92, risk_after: 17.28, risk_removed_pct: 65.38, disruption_cost: 9 },
        { node_id: 'A', paths_covered: 0, risk_before: 49.92, risk_after: 47.12, risk_removed_pct: 5.61, disruption_cost: 7 },
      ]);
    } else {
      // Demo network calculations
      setQueueData([
        {
          incident_id: 'INC-DEMO-01',
          node_id: 'LAPTOP-ENG',
          score: 94.60,
          breakdown: { severity: 3, confidence: 0.85, own_criticality: 2, reachable_weighted_criticality: 35.10, impact: 37.10, score: 94.60 },
          timestamp: '2026-10-03T10:00:00Z',
        },
        {
          incident_id: 'INC-DEMO-02',
          node_id: 'PRINTER-HR',
          score: 9.50,
          breakdown: { severity: 10, confidence: 0.95, own_criticality: 1, reachable_weighted_criticality: 0.0, impact: 1.0, score: 9.50 },
          timestamp: '2026-10-03T10:05:00Z',
        },
      ]);
      setRestorePlan({
        ok: true,
        order: ['DB-PRIMARY', 'AUTH-AD', 'INTERNAL-DNS', 'APP-01', 'APP-02', 'WEB-01', 'WEB-02', 'DB-REPLICA', 'BACKUP-VAULT', 'BASTION-HOST', 'DMZ-FIREWALL', 'VPN-GATEWAY', 'CORE-ROUTER', 'FILE-SERVER', 'MONITOR-SIEM', 'LAPTOP-ENG', 'LAPTOP-SALES', 'LAPTOP-FIN', 'PRINTER-HR', 'PRINTER-DEV'],
        cycle: null,
        explanation: 'All 11 dependencies satisfied before dependent services start.',
      });
      setSimResults({
        fcfs: { total_damage: 215.6, handled_order: ['INC-DEMO-01', 'INC-DEMO-02'] },
        severity_only: { total_damage: 395.2, handled_order: ['INC-DEMO-02', 'INC-DEMO-01'] },
        graph_aware: { total_damage: 210.8, handled_order: ['INC-DEMO-01', 'INC-DEMO-02'] },
      });
      setAttackPaths([
        { nodes: ['LAPTOP-ENG', 'VPN-GATEWAY', 'AUTH-AD', 'BASTION-HOST', 'DB-PRIMARY'], probability: 0.4284, total_weight: 0.8477 },
        { nodes: ['LAPTOP-ENG', 'VPN-GATEWAY', 'AUTH-AD'], probability: 0.7200, total_weight: 0.3285 },
        { nodes: ['LAPTOP-ENG', 'VPN-GATEWAY', 'AUTH-AD', 'BASTION-HOST'], probability: 0.5040, total_weight: 0.6852 },
      ]);
      setContainmentOptions([
        { node_id: 'VPN-GATEWAY', paths_covered: 3, risk_before: 94.60, risk_after: 5.10, risk_removed_pct: 94.61, disruption_cost: 6 },
        { node_id: 'AUTH-AD', paths_covered: 3, risk_before: 94.60, risk_after: 19.30, risk_removed_pct: 79.60, disruption_cost: 9 },
        { node_id: 'BASTION-HOST', paths_covered: 1, risk_before: 94.60, risk_after: 72.40, risk_removed_pct: 23.47, disruption_cost: 9 },
      ]);
    }
  }

  // Fetch blast radius when node selected
  useEffect(() => {
    if (!selectedNode) {
      setBlastData(null);
      return;
    }
    if (apiConnected) {
      fetch(`${API_BASE}/blast-radius/${selectedNode.id}`)
        .then((r) => r.json())
        .then((data) => setBlastData(data))
        .catch(() => setBlastData(null));
    }
  }, [selectedNode, apiConnected]);

  // Cytoscape Canvas Initialization
  useEffect(() => {
    if (!containerRef.current) return;

    const elements = [
      ...networkData.nodes.map((node) => ({
        data: {
          id: node.id,
          label: `${node.id}\n${node.name}\n[Crit: ${node.criticality}]`,
          name: node.name,
          type: node.type,
          criticality: node.criticality,
          status: node.status,
          isCritical: node.criticality >= (networkData.meta.critical_threshold || 8),
          isIsolated: node.id === isolatedNodeId,
        },
      })),
      ...networkData.edges.map((edge) => ({
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          kind: edge.kind,
          probability: edge.probability,
          label: edge.kind === 'network' ? `p=${edge.probability}` : 'requires',
        },
      })),
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap',
            'text-max-width': '85px',
            'font-family': 'Outfit, sans-serif',
            'font-size': '11px',
            'font-weight': '600',
            'color': '#f8fafc',
            'text-outline-color': '#090d16',
            'text-outline-width': 2.5,
            'width': 'mapData(criticality, 1, 10, 38, 80)',
            'height': 'mapData(criticality, 1, 10, 38, 80)',
            'background-color': '#172235',
            'border-width': 3,
            'border-color': '#334863',
          },
        },
        {
          selector: 'node[status = "compromised"]',
          style: {
            'background-color': '#7f1d1d',
            'border-color': '#f43f5e',
            'border-width': 4,
          },
        },
        {
          selector: 'node[?isCritical]',
          style: {
            'border-color': '#f59e0b',
            'border-width': 3.5,
          },
        },
        {
          selector: 'node[?isIsolated]',
          style: {
            'background-color': '#1e293b',
            'border-color': '#64748b',
            'opacity': 0.35,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#06b6d4',
            'border-width': 5,
            'shadow-blur': 15,
            'shadow-color': '#06b6d4',
            'shadow-opacity': 0.7,
          },
        },
        {
          selector: 'edge[kind = "network"]',
          style: {
            'width': 3,
            'line-color': '#0891b2',
            'target-arrow-color': '#0891b2',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'font-family': 'JetBrains Mono, monospace',
            'color': '#a5f3fc',
            'text-background-opacity': 0.85,
            'text-background-color': '#082f49',
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            'arrow-scale': 1.2,
          },
        },
        {
          selector: 'edge[kind = "dependency"]',
          style: {
            'width': 2.5,
            'line-color': '#9333ea',
            'line-style': 'dashed',
            'line-dash-pattern': [6, 4],
            'target-arrow-color': '#9333ea',
            'target-arrow-shape': 'vee',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'font-family': 'JetBrains Mono, monospace',
            'color': '#f3e8ff',
            'text-background-opacity': 0.85,
            'text-background-color': '#3b0764',
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            'arrow-scale': 1.2,
          },
        },
        {
          selector: '.highlighted-edge',
          style: {
            'line-color': '#f43f5e',
            'target-arrow-color': '#f43f5e',
            'width': 5,
            'z-index': 99,
          },
        },
        {
          selector: '.highlighted-node',
          style: {
            'border-color': '#f43f5e',
            'border-width': 5,
            'shadow-blur': 20,
            'shadow-color': '#f43f5e',
            'shadow-opacity': 0.8,
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        nodeRepulsion: () => 450000,
        idealEdgeLength: () => 130,
        padding: 40,
      },
    });

    cy.on('tap', 'node', (evt) => {
      setSelectedNode(evt.target.data());
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
        setHighlightedPath(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [networkData, isolatedNodeId]);

  // Apply edge filter
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;
    if (edgeFilter === 'all') {
      cy.edges().show();
    } else if (edgeFilter === 'network') {
      cy.edges('[kind = "network"]').show();
      cy.edges('[kind = "dependency"]').hide();
    } else if (edgeFilter === 'dependency') {
      cy.edges('[kind = "dependency"]').show();
      cy.edges('[kind = "network"]').hide();
    }
  }, [edgeFilter]);

  // Highlight specific path
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;
    cy.elements().removeClass('highlighted-edge highlighted-node');

    if (highlightedPath && highlightedPath.length > 1) {
      for (let i = 0; i < highlightedPath.length; i++) {
        cy.getElementById(highlightedPath[i]).addClass('highlighted-node');
        if (i < highlightedPath.length - 1) {
          const u = highlightedPath[i];
          const v = highlightedPath[i + 1];
          cy.edges(`[source = "${u}"][target = "${v}"]`).addClass('highlighted-edge');
        }
      }
    }
  }, [highlightedPath]);

  const handleIsolateToggle = (nodeId) => {
    if (isolatedNodeId === nodeId) {
      setIsolatedNodeId(null);
    } else {
      setIsolatedNodeId(nodeId);
    }
  };

  const handleFit = () => cyRef.current && cyRef.current.fit(undefined, 40);
  const handleRearrange = () => {
    if (cyRef.current) {
      cyRef.current.layout({ name: 'cose', animate: true, animationDuration: 350, padding: 40 }).run();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#090d16', color: '#f1f5f9' }}>
      {/* Top Header */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 24px',
          borderBottom: '1px solid #1e293b',
          backgroundColor: '#0c1220',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ backgroundColor: '#e11d48', color: '#fff', fontSize: '11px', fontWeight: 800, padding: '3px 8px', borderRadius: '4px' }}>
              DAA #92
            </span>
            <h1 style={{ fontSize: '17px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.01em' }}>
              Cyber Incident Response Planner
            </h1>
          </div>

          {/* Scenario Switcher */}
          <div style={{ display: 'flex', backgroundColor: '#131b2e', borderRadius: '6px', padding: '2px', border: '1px solid #23334d' }}>
            <button
              onClick={() => setSelectedScenario('worked_example')}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '4px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: selectedScenario === 'worked_example' ? '#2563eb' : 'transparent',
                color: selectedScenario === 'worked_example' ? '#fff' : '#94a3b8',
              }}
            >
              Worked Example (7 Nodes)
            </button>
            <button
              onClick={() => setSelectedScenario('demo_network')}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '4px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: selectedScenario === 'demo_network' ? '#2563eb' : 'transparent',
                color: selectedScenario === 'demo_network' ? '#fff' : '#94a3b8',
              }}
            >
              Enterprise Network (20 Nodes)
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {[
            { id: 'graph', label: 'Topology & Blast', icon: '🌐' },
            { id: 'queue', label: 'Priority Queue', icon: '⚡' },
            { id: 'paths', label: 'Attack Paths', icon: '🎯' },
            { id: 'restore', label: 'Restore Plan', icon: '🔄' },
            { id: 'simulate', label: 'Simulation', icon: '📊' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '6px 12px',
                fontSize: '12px',
                fontWeight: 600,
                borderRadius: '6px',
                border: activeTab === tab.id ? '1px solid #38bdf8' : '1px solid transparent',
                backgroundColor: activeTab === tab.id ? '#172554' : '#111827',
                color: activeTab === tab.id ? '#38bdf8' : '#94a3b8',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
              }}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}

          <span
            style={{
              marginLeft: '12px',
              padding: '3px 8px',
              borderRadius: '9999px',
              fontSize: '10px',
              fontWeight: 700,
              backgroundColor: apiConnected ? '#064e3b' : '#334155',
              color: apiConnected ? '#34d399' : '#cbd5e1',
              border: `1px solid ${apiConnected ? '#059669' : '#475569'}`,
            }}
          >
            {apiConnected ? '● Live API' : '○ Standalone Mock'}
          </span>
        </div>
      </header>

      {/* Main Workspace Area */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Side: Dynamic Workspace View */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
          {/* Controls Bar for Graph View */}
          {activeTab === 'graph' && (
            <div
              style={{
                position: 'absolute',
                top: 16,
                right: 16,
                zIndex: 10,
                display: 'flex',
                gap: '8px',
                backgroundColor: 'rgba(15, 23, 42, 0.85)',
                padding: '6px',
                borderRadius: '8px',
                backdropFilter: 'blur(8px)',
                border: '1px solid #23334d',
              }}
            >
              <select
                value={edgeFilter}
                onChange={(e) => setEdgeFilter(e.target.value)}
                style={{
                  backgroundColor: '#0f172a',
                  color: '#e2e8f0',
                  border: '1px solid #334155',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '11px',
                }}
              >
                <option value="all">Edges: All</option>
                <option value="network">Edges: Network Only</option>
                <option value="dependency">Edges: Dependencies Only</option>
              </select>
              <button onClick={handleFit} style={btnSmallStyle}>Fit View</button>
              <button onClick={handleRearrange} style={btnSmallStyle}>Rearrange</button>
            </div>
          )}

          {/* Tab 1: Interactive Cytoscape Canvas */}
          <div style={{ flex: 1, display: activeTab === 'graph' ? 'block' : 'none', position: 'relative' }}>
            <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

            {/* Bottom Legend */}
            <div
              style={{
                position: 'absolute',
                bottom: 16,
                left: 16,
                backgroundColor: 'rgba(12, 18, 32, 0.92)',
                border: '1px solid #23334d',
                borderRadius: '8px',
                padding: '12px 16px',
                backdropFilter: 'blur(10px)',
                fontSize: '11px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                pointerEvents: 'none',
              }}
            >
              <div style={{ fontWeight: 700, color: '#e2e8f0', marginBottom: '2px' }}>Graph Legend</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '20px', height: '3px', backgroundColor: '#0891b2', display: 'inline-block' }} />
                <span>Lateral Network Edge ($w = -\ln(p)$)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '20px', height: '0px', borderTop: '2px dashed #9333ea', display: 'inline-block' }} />
                <span>Dependency ($u \to v$ requires $v$ restored first)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '10px', height: '10px', backgroundColor: '#7f1d1d', border: '2px solid #f43f5e', borderRadius: '50%' }} />
                <span>Compromised Node (Active Alert)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '10px', height: '10px', backgroundColor: '#172235', border: '2px solid #f59e0b', borderRadius: '50%' }} />
                <span>Critical Asset (Criticality ≥ {networkData.meta.critical_threshold})</span>
              </div>
              <div style={{ color: '#64748b', fontSize: '10px', marginTop: '2px' }}>
                * Node radius scales with criticality (1–10)
              </div>
            </div>
          </div>

          {/* Tab 2: Priority Queue (Max-Heap) */}
          {activeTab === 'queue' && (
            <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
              <div style={{ maxWidth: '900px', margin: '0 auto' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                  <div>
                    <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc' }}>
                      Prioritized Incident Queue (Max-Heap)
                    </h2>
                    <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                      Incidents ranked by explicit formula: <code style={{ color: '#38bdf8' }}>Score = Severity × Confidence × Impact</code>. Ties broken by earliest timestamp.
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {queueData.map((item, idx) => (
                    <div
                      key={item.incident_id}
                      style={{
                        backgroundColor: '#111827',
                        border: '1px solid #1f2937',
                        borderRadius: '10px',
                        padding: '18px 20px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '12px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ backgroundColor: '#2563eb', color: '#fff', fontSize: '12px', fontWeight: 800, padding: '2px 8px', borderRadius: '4px' }}>
                            RANK #{idx + 1}
                          </span>
                          <span style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc' }}>
                            {item.incident_id}
                          </span>
                          <span style={{ color: '#94a3b8', fontSize: '13px' }}>
                            Target Asset: <strong style={{ color: '#f1f5f9' }}>{item.node_id}</strong>
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '12px', color: '#94a3b8' }}>Score:</span>
                          <span style={{ fontSize: '20px', fontWeight: 800, color: idx === 0 ? '#38bdf8' : '#94a3b8' }}>
                            {item.score.toFixed(2)}
                          </span>
                        </div>
                      </div>

                      {/* Score Breakdown Formula */}
                      <div style={{ backgroundColor: '#090d16', padding: '12px 16px', borderRadius: '6px', border: '1px solid #1e293b', fontSize: '12px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
                        <div>
                          <div style={{ color: '#64748b' }}>Severity</div>
                          <div style={{ fontWeight: 700, color: '#f43f5e', fontSize: '15px' }}>{item.breakdown.severity} / 10</div>
                        </div>
                        <div>
                          <div style={{ color: '#64748b' }}>Confidence</div>
                          <div style={{ fontWeight: 700, color: '#a855f7', fontSize: '15px' }}>{(item.breakdown.confidence * 100).toFixed(0)}%</div>
                        </div>
                        <div>
                          <div style={{ color: '#64748b' }}>Impact (Own + Blast)</div>
                          <div style={{ fontWeight: 700, color: '#38bdf8', fontSize: '15px' }}>
                            {item.breakdown.impact.toFixed(2)}
                            <span style={{ fontSize: '10px', color: '#94a3b8', marginLeft: '4px' }}>
                              ({item.breakdown.own_criticality} + {item.breakdown.reachable_weighted_criticality.toFixed(1)})
                            </span>
                          </div>
                        </div>
                        <div>
                          <div style={{ color: '#64748b' }}>Timestamp</div>
                          <div style={{ fontWeight: 600, color: '#e2e8f0', fontSize: '12px' }}>{item.timestamp}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Attack Paths & Containment */}
          {activeTab === 'paths' && (
            <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
              <div style={{ maxWidth: '900px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div>
                  <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc' }}>
                    Attack Paths & Containment Recommendations
                  </h2>
                  <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                    Dijkstra shortest paths under additive weights <code style={{ color: '#38bdf8' }}>w = -ln(p)</code> and differential risk isolation simulator.
                  </p>
                </div>

                {/* Most Probable Attack Paths */}
                <div style={{ backgroundColor: '#111827', padding: '18px', borderRadius: '10px', border: '1px solid #1f2937' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#e2e8f0', marginBottom: '12px' }}>
                    Most Probable Attack Paths to Critical Assets
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {attackPaths.map((p, idx) => (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: '#090d16',
                          border: '1px solid #1e293b',
                          borderRadius: '6px',
                          padding: '12px 16px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 600, color: '#f1f5f9' }}>
                            <span>Path:</span>
                            {p.nodes.map((node, nIdx) => (
                              <React.Fragment key={nIdx}>
                                <span style={{ color: nIdx === p.nodes.length - 1 ? '#f59e0b' : '#38bdf8' }}>{node}</span>
                                {nIdx < p.nodes.length - 1 && <span style={{ color: '#64748b' }}>→</span>}
                              </React.Fragment>
                            ))}
                          </div>
                          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
                            Target Criticality: High (≥ {networkData.meta.critical_threshold}) | Additive Cost: {p.total_weight.toFixed(4)}
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <span style={{ fontSize: '14px', fontWeight: 700, color: '#38bdf8' }}>
                            P = {(p.probability * 100).toFixed(1)}%
                          </span>
                          <button
                            onClick={() => {
                              setHighlightedPath(p.nodes);
                              setActiveTab('graph');
                            }}
                            style={btnSmallStyle}
                          >
                            Trace on Graph
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Containment Recommendations */}
                <div style={{ backgroundColor: '#111827', padding: '18px', borderRadius: '10px', border: '1px solid #1f2937' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#e2e8f0', marginBottom: '12px' }}>
                    Recommended Isolation Points (Containment)
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {containmentOptions.map((opt) => (
                      <div
                        key={opt.node_id}
                        style={{
                          backgroundColor: '#090d16',
                          border: isolatedNodeId === opt.node_id ? '2px solid #10b981' : '1px solid #1e293b',
                          borderRadius: '6px',
                          padding: '14px 18px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>
                              Isolate Node: {opt.node_id}
                            </span>
                            <span style={{ backgroundColor: '#064e3b', color: '#6ee7b7', fontSize: '11px', fontWeight: 700, padding: '2px 8px', borderRadius: '4px' }}>
                              -{opt.risk_removed_pct.toFixed(1)}% Risk Reduction
                            </span>
                          </div>
                          <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                            Risk Before: <strong style={{ color: '#f43f5e' }}>{opt.risk_before.toFixed(2)}</strong> → After: <strong style={{ color: '#10b981' }}>{opt.risk_after.toFixed(2)}</strong> | Disruption Cost: {opt.disruption_cost} | Paths Severed: {opt.paths_covered}
                          </div>
                        </div>

                        <button
                          onClick={() => handleIsolateToggle(opt.node_id)}
                          style={{
                            padding: '6px 14px',
                            backgroundColor: isolatedNodeId === opt.node_id ? '#dc2626' : '#059669',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '12px',
                            fontWeight: 600,
                          }}
                        >
                          {isolatedNodeId === opt.node_id ? 'Undo Isolation' : 'Apply Isolation'}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 4: Dependency-Safe Restore Order */}
          {activeTab === 'restore' && (
            <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
              <div style={{ maxWidth: '900px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc' }}>
                    Dependency-Safe Restoration Plan
                  </h2>
                  <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                    Topological sort over functional dependencies. If system <code style={{ color: '#a855f7' }}>A requires D</code>, system <code style={{ color: '#a855f7' }}>D</code> is restored first.
                  </p>
                </div>

                {restorePlan && (
                  <div style={{ backgroundColor: '#111827', padding: '20px', borderRadius: '10px', border: '1px solid #1f2937' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                      <span style={{ backgroundColor: restorePlan.ok ? '#064e3b' : '#7f1d1d', color: restorePlan.ok ? '#6ee7b7' : '#fca5a5', padding: '4px 10px', borderRadius: '9999px', fontSize: '12px', fontWeight: 700 }}>
                        {restorePlan.ok ? '✓ Acyclic & Safe' : '⚠ Dependency Cycle Detected'}
                      </span>
                      <span style={{ color: '#94a3b8', fontSize: '13px' }}>{restorePlan.explanation}</span>
                    </div>

                    {restorePlan.ok && restorePlan.order && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {restorePlan.order.map((nodeId, idx) => {
                          const node = networkData.nodes.find((n) => n.id === nodeId);
                          const deps = networkData.edges.filter((e) => e.kind === 'dependency' && e.source === nodeId).map((e) => e.target);
                          return (
                            <div
                              key={nodeId}
                              style={{
                                backgroundColor: '#090d16',
                                border: '1px solid #1e293b',
                                borderRadius: '6px',
                                padding: '12px 16px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '16px',
                              }}
                            >
                              <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#1e293b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '13px', color: '#38bdf8' }}>
                                {idx + 1}
                              </div>
                              <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '14px' }}>
                                  {nodeId} <span style={{ color: '#94a3b8', fontWeight: 400 }}>({node?.name || 'System'})</span>
                                </div>
                                <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                                  Type: {node?.type} | Criticality: {node?.criticality}/10
                                </div>
                              </div>
                              <div style={{ fontSize: '12px', color: '#a855f7' }}>
                                {deps.length > 0 ? `Requires: ${deps.join(', ')}` : 'Independent (Leaf)'}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tab 5: Simulation & Strategy Comparison */}
          {activeTab === 'simulate' && (
            <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
              <div style={{ maxWidth: '900px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc' }}>
                    Incident Response Strategy Simulation
                  </h2>
                  <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                    Discrete time-step simulation comparing First-Come-First-Served, Severity-Only, and Graph-Aware policies under identical seeds.
                  </p>
                </div>

                {simResults && (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                    {[
                      { key: 'fcfs', name: 'First-Come-First-Served', color: '#3b82f6', desc: 'Handled in strict arrival order' },
                      { key: 'severity_only', name: 'Severity-Only', color: '#f59e0b', desc: 'Handled by raw alert severity' },
                      { key: 'graph_aware', name: 'Graph-Aware (Ours)', color: '#10b981', desc: 'Handled by dynamic topology score' },
                    ].map((s) => {
                      const data = simResults[s.key];
                      const isWinner = s.key === 'graph_aware';
                      return (
                        <div
                          key={s.key}
                          style={{
                            backgroundColor: '#111827',
                            border: isWinner ? '2px solid #10b981' : '1px solid #1f2937',
                            borderRadius: '10px',
                            padding: '20px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '12px',
                          }}
                        >
                          <div>
                            <div style={{ fontSize: '12px', fontWeight: 700, color: s.color, textTransform: 'uppercase' }}>
                              {s.name}
                            </div>
                            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>{s.desc}</div>
                          </div>

                          <div style={{ margin: '10px 0' }}>
                            <div style={{ fontSize: '11px', color: '#94a3b8' }}>Total Accumulated Damage</div>
                            <div style={{ fontSize: '28px', fontWeight: 800, color: '#f8fafc' }}>
                              {data.total_damage.toFixed(1)}
                            </div>
                          </div>

                          <div>
                            <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>Handling Sequence</div>
                            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                              {data.handled_order.map((incId, i) => (
                                <span
                                  key={i}
                                  style={{
                                    backgroundColor: '#090d16',
                                    border: '1px solid #334155',
                                    padding: '2px 8px',
                                    borderRadius: '4px',
                                    fontSize: '11px',
                                    fontWeight: 600,
                                  }}
                                >
                                  {i + 1}. {incId}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Pedagogical Insight Callout */}
                <div style={{ backgroundColor: '#064e3b', border: '1px solid #059669', borderRadius: '8px', padding: '16px 20px', color: '#ecfdf5', fontSize: '13px', lineHeight: '1.6' }}>
                  <strong>Key Algorithmic Finding:</strong> In both scenarios, the <em>Severity-Only</em> policy isolates low-impact peripherals (like printers) first because of their high raw severity, leaving pivotable laptops uncontained to inflict lateral damage on the database core. The <em>Graph-Aware</em> policy cuts total damage significantly by containing assets based on their reachable blast radius.
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar Inspector */}
        <aside
          style={{
            width: '320px',
            borderLeft: '1px solid #1e293b',
            backgroundColor: '#0a0f1d',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
            overflowY: 'auto',
          }}
        >
          {/* Active Network Summary */}
          <div style={{ backgroundColor: '#111827', padding: '16px', borderRadius: '8px', border: '1px solid #1f2937' }}>
            <h3 style={{ fontSize: '12px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Active Network Specs
            </h3>
            <div style={{ marginTop: '10px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
              <div style={statBoxStyle}>
                <div style={{ color: '#64748b', fontSize: '10px' }}>Nodes</div>
                <div style={{ fontSize: '16px', fontWeight: 700 }}>{networkData.nodes.length}</div>
              </div>
              <div style={statBoxStyle}>
                <div style={{ color: '#64748b', fontSize: '10px' }}>Incidents</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#f43f5e' }}>{networkData.incidents.length}</div>
              </div>
              <div style={statBoxStyle}>
                <div style={{ color: '#64748b', fontSize: '10px' }}>Network Edges</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#38bdf8' }}>
                  {networkData.edges.filter((e) => e.kind === 'network').length}
                </div>
              </div>
              <div style={statBoxStyle}>
                <div style={{ color: '#64748b', fontSize: '10px' }}>Dependencies</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#c084fc' }}>
                  {networkData.edges.filter((e) => e.kind === 'dependency').length}
                </div>
              </div>
            </div>
          </div>

          {/* Selected Node Details */}
          <div style={{ backgroundColor: '#111827', padding: '16px', borderRadius: '8px', border: '1px solid #1f2937' }}>
            <h3 style={{ fontSize: '12px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Node Inspector
            </h3>
            {selectedNode ? (
              <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                <div style={detailRowStyle}>
                  <span style={{ color: '#64748b' }}>ID:</span>
                  <strong>{selectedNode.id}</strong>
                </div>
                <div style={detailRowStyle}>
                  <span style={{ color: '#64748b' }}>Name:</span>
                  <span>{selectedNode.name}</span>
                </div>
                <div style={detailRowStyle}>
                  <span style={{ color: '#64748b' }}>Type:</span>
                  <span style={{ color: '#38bdf8' }}>{selectedNode.type}</span>
                </div>
                <div style={detailRowStyle}>
                  <span style={{ color: '#64748b' }}>Criticality:</span>
                  <strong style={{ color: selectedNode.isCritical ? '#f59e0b' : '#10b981' }}>
                    {selectedNode.criticality} / 10 {selectedNode.isCritical ? '(Critical Asset)' : ''}
                  </strong>
                </div>
                <div style={detailRowStyle}>
                  <span style={{ color: '#64748b' }}>Status:</span>
                  <span style={{ color: selectedNode.status === 'compromised' ? '#f43f5e' : '#10b981', fontWeight: 700 }}>
                    {selectedNode.status.toUpperCase()}
                  </span>
                </div>

                {blastData && (
                  <div style={{ marginTop: '12px', borderTop: '1px solid #1e293b', paddingTop: '10px' }}>
                    <div style={{ fontWeight: 700, color: '#38bdf8', marginBottom: '6px' }}>
                      Blast Radius ({Object.keys(blastData.blast_radius || {}).length} reachable):
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '11px' }}>
                      {Object.entries(blastData.blast_radius || {}).map(([target, d]) => (
                        <div key={target} style={{ display: 'flex', justifyContent: 'space-between', color: '#cbd5e1' }}>
                          <span>→ {target} ({d.hops} hops)</span>
                          <span style={{ color: '#38bdf8', fontWeight: 600 }}>P={(d.reach_probability * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                      {Object.keys(blastData.blast_radius || {}).length === 0 && (
                        <span style={{ color: '#64748b', fontStyle: 'italic' }}>No outgoing attack paths.</span>
                      )}
                    </div>
                  </div>
                )}

                <button
                  onClick={() => handleIsolateToggle(selectedNode.id)}
                  style={{
                    marginTop: '10px',
                    padding: '8px',
                    backgroundColor: isolatedNodeId === selectedNode.id ? '#dc2626' : '#1e293b',
                    color: '#fff',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '11px',
                    fontWeight: 600,
                  }}
                >
                  {isolatedNodeId === selectedNode.id ? 'Restore Node' : 'Simulate Isolation'}
                </button>
              </div>
            ) : (
              <div style={{ marginTop: '12px', color: '#64748b', fontSize: '12px', fontStyle: 'italic' }}>
                Click any node on the graph canvas to inspect its criticality, status, and blast radius.
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

const btnSmallStyle = {
  backgroundColor: '#1e293b',
  color: '#e2e8f0',
  border: '1px solid #334155',
  padding: '4px 10px',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '11px',
  fontWeight: 600,
};

const statBoxStyle = {
  backgroundColor: '#090d16',
  padding: '8px 10px',
  borderRadius: '6px',
  border: '1px solid #1e293b',
};

const detailRowStyle = {
  display: 'flex',
  justifyContent: 'space-between',
};
