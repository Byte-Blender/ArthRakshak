// File: frontend/src/pages/Saheli.jsx | Location: frontend/src/pages/Saheli.jsx
import { useState, useEffect } from "react";
import axios from "axios";
 
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
 
export default function Saheli() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
 
  const fetchTrustGraph = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_BASE}/trust-graph`);
      setData(res.data);
    } catch (err) {
      setError("Backend not reachable.");
    } finally {
      setLoading(false);
    }
  };
 
  useEffect(() => {
    fetchTrustGraph();
  }, []);
 
  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: 20 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 10,
        }}
      >
        <h2 style={{ margin: 0 }}>Saheli — Trust Graph</h2>
        <button
          onClick={fetchTrustGraph}
          style={{
            padding: "8px 16px",
            borderRadius: 8,
            border: "1px solid #6C63FF",
            background: "transparent",
            color: "#6C63FF",
            cursor: "pointer",
          }}
        >
          Refresh
        </button>
      </div>
      <p style={{ color: "#666", marginTop: 0 }}>
        Influence scores computed from message content similarity and timing (NetworkX PageRank).
        Arrows show inferred information flow.
      </p>
 
      {loading && <p>Loading trust graph...</p>}
      {error && <p style={{ color: "#c0392b" }}>{error}</p>}
 
      {!loading && !error && data && (
        <>
          <TopConnectorCard topConnector={data.top_connector} explanation={data.explanation} />
          <TrustGraphViz graph={data.graph} />
          <NodeTable graph={data.graph} />
        </>
      )}
    </div>
  );
}
 
function TopConnectorCard({ topConnector, explanation }) {
  if (!topConnector || topConnector.error) {
    return (
      <div
        style={{
          background: "#fff8e6",
          border: "1px solid #f1c40f",
          borderRadius: 10,
          padding: 16,
          marginBottom: 20,
        }}
      >
        {topConnector?.error ||
          "No interaction data yet — message Saheli from a couple of different numbers to generate a graph."}
      </div>
    );
  }
 
  return (
    <div
      style={{
        background: "#f4f3ff",
        border: "1px solid #6C63FF",
        borderRadius: 10,
        padding: 16,
        marginBottom: 20,
      }}
    >
      <div style={{ fontSize: 13, color: "#6C63FF", fontWeight: 600 }}>
        TOP CONNECTOR
      </div>
      <div style={{ fontSize: 20, fontWeight: 700, margin: "4px 0" }}>
        {topConnector.name}
      </div>
      <div style={{ fontSize: 14, color: "#333" }}>
        Influence score: <strong>{topConnector.score}</strong> · scored across{" "}
        {topConnector.total_members_scored} member(s)
      </div>
      {explanation && (
        <div
          style={{
            marginTop: 10,
            fontSize: 14,
            color: "#444",
            fontStyle: "italic",
            borderTop: "1px solid #ddd",
            paddingTop: 10,
          }}
        >
          {explanation}
        </div>
      )}
    </div>
  );
}
 
function TrustGraphViz({ graph }) {
  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return null;
  }
 
  const width = 700;
  const height = 500;
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) / 2 - 60;
 
  const positions = {};
  graph.nodes.forEach((node, i) => {
    const angle = (i / graph.nodes.length) * 2 * Math.PI - Math.PI / 2;
    positions[node.id] = {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    };
  });
 
  const maxWeight = Math.max(1, ...graph.edges.map((e) => e.weight));
 
  return (
    <div
      style={{
        border: "1px solid #ccc",
        borderRadius: 10,
        marginBottom: 20,
        overflow: "auto",
      }}
    >
      <svg width={width} height={height}>
        <defs>
          <marker
            id="arrowhead"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#6C63FF" />
          </marker>
        </defs>

        {graph.edges.map((edge, i) => {
          const from = positions[edge.source];
          const to = positions[edge.target];
          if (!from || !to) return null;

          // shorten the line so it stops at the target circle's edge instead
          // of running under it — otherwise the arrowhead gets hidden.
          const targetNode = graph.nodes.find((n) => n.id === edge.target);
          const targetRadius = targetNode ? 14 + targetNode.score * 22 : 14;
          const dx = to.x - from.x;
          const dy = to.y - from.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const endX = to.x - (dx / dist) * (targetRadius + 6);
          const endY = to.y - (dy / dist) * (targetRadius + 6);

          const opacity = Math.min(1, 0.2 + (edge.weight / maxWeight) * 0.8);
          return (
            <line
              key={i}
              x1={from.x}
              y1={from.y}
              x2={endX}
              y2={endY}
              stroke="#6C63FF"
              strokeWidth={1 + (edge.weight / maxWeight) * 3}
              opacity={opacity}
              markerEnd="url(#arrowhead)"
            />
          );
        })}
 
        {graph.nodes.map((node) => {
          const pos = positions[node.id];
          const nodeRadius = 14 + node.score * 22;
          const isTop = node.is_top_connector;
          return (
            <g key={node.id}>
              <circle
                cx={pos.x}
                cy={pos.y}
                r={nodeRadius}
                fill={isTop ? "#f1c40f" : "#6C63FF"}
                stroke={isTop ? "#b8930a" : "#4a41cc"}
                strokeWidth={isTop ? 3 : 1.5}
              />
              <text
                x={pos.x}
                y={pos.y + nodeRadius + 16}
                textAnchor="middle"
                fontSize={12}
                fill="#333"
              >
                {node.name}
              </text>
              <text
                x={pos.x}
                y={pos.y + 4}
                textAnchor="middle"
                fontSize={11}
                fill="#fff"
                fontWeight={600}
              >
                {node.score.toFixed(2)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
 
function NodeTable({ graph }) {
  if (!graph || !graph.nodes || graph.nodes.length === 0) return null;
 
  const sorted = [...graph.nodes].sort((a, b) => b.score - a.score);
 
  return (
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
      <thead>
        <tr style={{ textAlign: "left", borderBottom: "2px solid #ddd" }}>
          <th style={{ padding: 8 }}>Member</th>
          <th style={{ padding: 8 }}>Influence Score</th>
          <th style={{ padding: 8 }}>Interactions</th>
          <th style={{ padding: 8 }}>Top Connector</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((node) => (
          <tr key={node.id} style={{ borderBottom: "1px solid #eee" }}>
            <td style={{ padding: 8 }}>{node.name}</td>
            <td style={{ padding: 8 }}>{node.score.toFixed(3)}</td>
            <td style={{ padding: 8 }}>{node.interaction_count}</td>
            <td style={{ padding: 8 }}>{node.is_top_connector ? "⭐" : ""}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
 