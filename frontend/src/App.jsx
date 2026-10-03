import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import mockData from './worked_example_mock.json';

export default function App() {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Build elements from mockData
    const elements = [
      ...mockData.nodes.map((node) => ({
        data: {
          id: node.id,
          label: `${node.id}\n${node.name}\n[Crit: ${node.criticality}]`,
          name: node.name,
          type: node.type,
          criticality: node.criticality,
          status: node.status,
          isCritical: node.criticality >= (mockData.meta.critical_threshold || 8),
        },
      })),
      ...mockData.edges.map((edge) => ({
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          kind: edge.kind,
          probability: edge.probability,
          label: edge.kind === 'network' ? `p = ${edge.probability}` : 'requires',
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
            'text-max-width': '80px',
            'font-family': 'Outfit, sans-serif',
            'font-size': '11px',
            'font-weight': '600',
            'color': '#ffffff',
            'text-outline-color': '#0f172a',
            'text-outline-width': 2,
            // Sized by criticality: 1 -> 38px, 10 -> 82px
            'width': 'mapData(criticality, 1, 10, 38, 82)',
            'height': 'mapData(criticality, 1, 10, 38, 82)',
            'background-color': '#1e293b',
            'border-width': 3,
            'border-color': '#475569',
            'transition-property': 'background-color, border-color, border-width',
            'transition-duration': '0.2s',
          },
        },
        {
          selector: 'node[status = "compromised"]',
          style: {
            'background-color': '#881337',
            'border-color': '#f43f5e',
            'border-width': 4,
          },
        },
        {
          selector: 'node[?isCritical]',
          style: {
            'border-color': '#f59e0b',
            'border-style': 'solid',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#38bdf8',
            'border-width': 5,
            'shadow-blur': 15,
            'shadow-color': '#38bdf8',
            'shadow-opacity': 0.6,
          },
        },
        {
          selector: 'edge[kind = "network"]',
          style: {
            'width': 3,
            'line-color': '#06b6d4',
            'target-arrow-color': '#06b6d4',
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
            'text-border-color': '#0e7490',
            'text-border-width': 1,
            'text-border-opacity': 0.8,
            'arrow-scale': 1.2,
          },
        },
        {
          selector: 'edge[kind = "dependency"]',
          style: {
            'width': 2.5,
            'line-color': '#a855f7',
            'line-style': 'dashed',
            'line-dash-pattern': [6, 4],
            'target-arrow-color': '#a855f7',
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
            'text-border-color': '#7e22ce',
            'text-border-width': 1,
            'text-border-opacity': 0.8,
            'arrow-scale': 1.2,
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        nodeRepulsion: () => 450000,
        idealEdgeLength: () => 140,
        edgeElasticity: () => 100,
        padding: 50,
      },
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedNode(node.data());
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, []);

  const handleFit = () => {
    if (cyRef.current) {
      cyRef.current.fit(undefined, 40);
    }
  };

  const handleResetLayout = () => {
    if (cyRef.current) {
      cyRef.current.layout({
        name: 'cose',
        animate: true,
        animationDuration: 400,
        nodeRepulsion: () => 450000,
        idealEdgeLength: () => 140,
        padding: 50,
      }).run();
    }
  };

  const networkEdgesCount = mockData.edges.filter((e) => e.kind === 'network').length;
  const dependencyEdgesCount = mockData.edges.filter((e) => e.kind === 'dependency').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#0a0d14' }}>
      {/* Top Navigation Bar */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px 24px',
          borderBottom: '1px solid #1e293b',
          backgroundColor: '#0f172a',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              style={{
                backgroundColor: '#dc2626',
                color: '#fff',
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '4px',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              DAA Problem #92
            </span>
            <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc' }}>
              Cyber Incident Response Planner
            </h1>
          </div>
          <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '3px' }}>
            Phase 0: Graph Topology & Criticality Visualization (Worked Example)
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={handleFit}
            style={{
              padding: '6px 14px',
              backgroundColor: '#1e293b',
              color: '#e2e8f0',
              border: '1px solid #334155',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 500,
            }}
          >
            Fit View
          </button>
          <button
            onClick={handleResetLayout}
            style={{
              padding: '6px 14px',
              backgroundColor: '#1e293b',
              color: '#e2e8f0',
              border: '1px solid #334155',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 500,
            }}
          >
            Rearrange
          </button>
          <span
            style={{
              padding: '4px 10px',
              backgroundColor: '#064e3b',
              color: '#6ee7b7',
              border: '1px solid #059669',
              borderRadius: '9999px',
              fontSize: '11px',
              fontWeight: 600,
            }}
          >
            ● Phase 0 Ready
          </span>
        </div>
      </header>

      {/* Main Graph View Area */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Cytoscape Container */}
        <div style={{ flex: 1, position: 'relative' }}>
          <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

          {/* Graph Legend Overlay */}
          <div
            style={{
              position: 'absolute',
              bottom: 20,
              left: 20,
              backgroundColor: 'rgba(15, 23, 42, 0.92)',
              border: '1px solid #334155',
              borderRadius: '8px',
              padding: '14px 18px',
              backdropFilter: 'blur(8px)',
              fontSize: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div style={{ fontWeight: 600, color: '#f1f5f9', marginBottom: '2px' }}>
              Graph Legend
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '22px', height: '3px', backgroundColor: '#06b6d4', display: 'inline-block' }} />
              <span>Network Lateral Pivot (w = -ln(p))</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  width: '22px',
                  height: '0px',
                  borderTop: '2px dashed #a855f7',
                  display: 'inline-block',
                }}
              />
              <span>Functional Dependency (source requires target)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  width: '12px',
                  height: '12px',
                  backgroundColor: '#881337',
                  border: '2px solid #f43f5e',
                  borderRadius: '50%',
                  display: 'inline-block',
                }}
              />
              <span>Compromised System (Active Incident)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  width: '12px',
                  height: '12px',
                  backgroundColor: '#1e293b',
                  border: '2px solid #f59e0b',
                  borderRadius: '50%',
                  display: 'inline-block',
                }}
              />
              <span>Critical Asset (Criticality ≥ {mockData.meta.critical_threshold})</span>
            </div>
            <div style={{ color: '#94a3b8', fontSize: '11px', marginTop: '2px' }}>
              * Node radius scales proportionally with criticality (1–10)
            </div>
          </div>
        </div>

        {/* Sidebar Info Panel */}
        <aside
          style={{
            width: '320px',
            borderLeft: '1px solid #1e293b',
            backgroundColor: '#0b1120',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
            overflowY: 'auto',
          }}
        >
          {/* Network Summary Stats */}
          <div style={{ backgroundColor: '#131d31', padding: '16px', borderRadius: '8px', border: '1px solid #23334d' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 600, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Network Overview
            </h3>
            <div style={{ marginTop: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div style={{ backgroundColor: '#0f172a', padding: '8px 12px', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Total Nodes</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc' }}>{mockData.nodes.length}</div>
              </div>
              <div style={{ backgroundColor: '#0f172a', padding: '8px 12px', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Incidents</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#f43f5e' }}>{mockData.incidents.length}</div>
              </div>
              <div style={{ backgroundColor: '#0f172a', padding: '8px 12px', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Network Edges</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#38bdf8' }}>{networkEdgesCount}</div>
              </div>
              <div style={{ backgroundColor: '#0f172a', padding: '8px 12px', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Dependencies</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#c084fc' }}>{dependencyEdgesCount}</div>
              </div>
            </div>
          </div>

          {/* Active Incidents Card */}
          <div style={{ backgroundColor: '#131d31', padding: '16px', borderRadius: '8px', border: '1px solid #23334d' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 600, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Active Incidents
            </h3>
            <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {mockData.incidents.map((inc) => (
                <div
                  key={inc.id}
                  style={{
                    padding: '10px 12px',
                    backgroundColor: '#1e293b',
                    borderRadius: '6px',
                    borderLeft: '4px solid #f43f5e',
                    fontSize: '12px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, color: '#f1f5f9' }}>
                    <span>{inc.id}</span>
                    <span style={{ color: '#fb7185' }}>Severity {inc.severity}/10</span>
                  </div>
                  <div style={{ color: '#94a3b8', marginTop: '4px' }}>
                    Target: <strong style={{ color: '#e2e8f0' }}>{inc.node_id}</strong> | Confidence: {inc.confidence}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Selected Node Details */}
          <div style={{ backgroundColor: '#131d31', padding: '16px', borderRadius: '8px', border: '1px solid #23334d' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 600, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Node Inspector
            </h3>
            {selectedNode ? (
              <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>ID:</span>
                  <strong style={{ color: '#f8fafc' }}>{selectedNode.id}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Name:</span>
                  <span style={{ color: '#e2e8f0' }}>{selectedNode.name}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Type:</span>
                  <span style={{ color: '#38bdf8' }}>{selectedNode.type}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Criticality:</span>
                  <strong style={{ color: selectedNode.isCritical ? '#f59e0b' : '#10b981' }}>
                    {selectedNode.criticality} / 10 {selectedNode.isCritical ? '(Critical)' : ''}
                  </strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Status:</span>
                  <span
                    style={{
                      color: selectedNode.status === 'compromised' ? '#f43f5e' : '#10b981',
                      fontWeight: 600,
                    }}
                  >
                    {selectedNode.status.toUpperCase()}
                  </span>
                </div>
              </div>
            ) : (
              <div style={{ marginTop: '12px', color: '#64748b', fontSize: '12px', fontStyle: 'italic' }}>
                Click any node on the graph canvas to inspect its criticality, status, and edge relationships.
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
