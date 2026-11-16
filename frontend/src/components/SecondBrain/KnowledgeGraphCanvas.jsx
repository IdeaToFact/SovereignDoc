// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState, useEffect, useRef, useMemo } from "react";
import GraphInspectorDrawer from "./GraphInspectorDrawer";

const NODE_STYLES = {
  DOCUMENT: { color: "#10B981", radius: 20, badge: "DOC", label: "Documents" },
  REVIEW_RUN: { color: "#3B82F6", radius: 16, badge: "RUN", label: "Review Runs" },
  CLAUSE_CATEGORY: { color: "#6366F1", radius: 15, badge: "CLS", label: "Clauses" },
  RISK: { color: "#EF4444", radius: 14, badge: "RISK", label: "Risks" },
  OBLIGATION: { color: "#14B8A6", radius: 14, badge: "DUTY", label: "Obligations" },
  NOTE: { color: "#06B6D4", radius: 17, badge: "NOTE", label: "Notes" },
  TAG: { color: "#A855F7", radius: 12, badge: "#", label: "Tags" },
};

export default function KnowledgeGraphCanvas({
  graphData,
  onSelectNoteNode,
  onOpenDocumentCitation,
  onPinToNote,
  onRefreshGraph,
}) {
  const canvasRef = useRef(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeMatchIndex, setActiveMatchIndex] = useState(0);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [hoverPos, setHoverPos] = useState(null);

  // Hygiene & Isolation Filters
  const [viewMode, setViewMode] = useState("current"); // "current" (default) | "timeline"
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL"); // "ALL" | "HIGH" | "MEDIUM" | "LOW"
  const [partyFilter, setPartyFilter] = useState("ALL"); // "ALL" | "VENDOR" | "CUSTOMER" | "MUTUAL"

  const [enabledTypes, setEnabledTypes] = useState({
    DOCUMENT: true,
    REVIEW_RUN: true,
    CLAUSE_CATEGORY: true,
    RISK: true,
    OBLIGATION: true,
    NOTE: true,
    TAG: true,
  });

  // Simulation and Camera refs
  const simNodesRef = useRef([]);
  const simEdgesRef = useRef([]);
  const cameraRef = useRef({ x: 0, y: 0, zoom: 1.0, targetX: null, targetY: null, targetZoom: null });
  const dragRef = useRef({ mode: null, node: null, lastX: 0, lastY: 0, moved: false });

  // Extract all distinct Clause Categories detected in the graph
  const availableCategories = useMemo(() => {
    const cats = new Set();
    for (const n of graphData?.nodes || []) {
      if (n.entity_type === "CLAUSE_CATEGORY" && n.label) {
        cats.add(n.label);
      } else if (n.metadata?.category) {
        const pretty = n.metadata.category.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
        cats.add(pretty);
      }
    }
    return Array.from(cats).sort();
  }, [graphData]);

  // Filter nodes & edges with View Mode, Category Isolation, Severity, Party, and Type toggles
  const filteredGraph = useMemo(() => {
    const rawNodes = graphData?.nodes || [];
    const rawEdges = graphData?.edges || [];

    // 1. View Mode: "current" keeps only latest review run per document
    let nodes = rawNodes;
    if (viewMode === "current") {
      const maxRunPerDoc = new Map();
      for (const n of rawNodes) {
        if (n.entity_type === "REVIEW_RUN" && n.metadata?.document_id) {
          const curr = maxRunPerDoc.get(n.metadata.document_id) || 0;
          const runNum = n.metadata.run_number || 1;
          if (runNum > curr) maxRunPerDoc.set(n.metadata.document_id, runNum);
        }
      }

      nodes = rawNodes.filter((n) => {
        if (["DOCUMENT", "CLAUSE_CATEGORY", "NOTE", "TAG"].includes(n.entity_type)) {
          return true;
        }
        if (n.metadata?.is_latest !== undefined) {
          return n.metadata.is_latest === true;
        }
        const docId = n.metadata?.document_id;
        const maxRun = maxRunPerDoc.get(docId);
        if (maxRun && n.metadata?.run_number) {
          return n.metadata.run_number === maxRun;
        }
        return true;
      });
    }

    // 2. Clause Category Isolation
    if (categoryFilter !== "ALL") {
      const catNormalized = categoryFilter.toLowerCase().replace(/[^a-z0-9]/g, "");
      nodes = nodes.filter((n) => {
        if (n.entity_type === "DOCUMENT") return true;
        const nCat = (n.metadata?.category || n.label || "").toLowerCase().replace(/[^a-z0-9]/g, "");
        return nCat.includes(catNormalized) || catNormalized.includes(nCat);
      });
    }

    // 3. Severity Filtering
    if (severityFilter !== "ALL") {
      nodes = nodes.filter((n) => {
        if (n.entity_type === "RISK") {
          return n.metadata?.risk_level === severityFilter;
        }
        return true;
      });
    }

    // 4. Party Filtering
    if (partyFilter !== "ALL") {
      nodes = nodes.filter((n) => {
        if (n.entity_type === "OBLIGATION") {
          return n.metadata?.party === partyFilter;
        }
        return true;
      });
    }

    // 5. Entity Type Toggles
    const visibleNodes = nodes.filter((n) => enabledTypes[n.entity_type] !== false);
    const visibleIds = new Set(visibleNodes.map((n) => n.id));
    const visibleEdges = rawEdges.filter(
      (e) => visibleIds.has(e.source_id) && visibleIds.has(e.target_id)
    );
    return { nodes: visibleNodes, edges: visibleEdges };
  }, [graphData, viewMode, categoryFilter, severityFilter, partyFilter, enabledTypes]);

  // Compute search matches across visible nodes
  const matchedNodes = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return [];
    return filteredGraph.nodes.filter((n) => {
      const meta = n.metadata || {};
      const hay = [
        n.label,
        n.entity_type,
        meta.category || "",
        meta.risk_level || "",
        meta.party || "",
        meta.rule_id || "",
        meta.verbatim_text || "",
        meta.action_required || "",
        Array.isArray(meta.tags) ? meta.tags.join(" ") : "",
      ]
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [filteredGraph.nodes, searchQuery]);

  // Initialize simulation coordinates whenever filteredGraph changes
  useEffect(() => {
    const prevMap = new Map(simNodesRef.current.map((n) => [n.id, n]));
    const count = filteredGraph.nodes.length || 1;
    const radiusSpread = Math.min(260, Math.max(120, count * 14));

    simNodesRef.current = filteredGraph.nodes.map((n, idx) => {
      const existing = prevMap.get(n.id);
      const angle = (2 * Math.PI * idx) / count;
      return {
        ...n,
        x: existing ? existing.x : Math.cos(angle) * radiusSpread,
        y: existing ? existing.y : Math.sin(angle) * radiusSpread,
        vx: 0,
        vy: 0,
        pinned: false,
      };
    });

    simEdgesRef.current = filteredGraph.edges;
  }, [filteredGraph]);

  // Auto-zoom camera when search query or activeMatchIndex changes
  useEffect(() => {
    if (matchedNodes.length === 0) {
      cameraRef.current.targetX = null;
      cameraRef.current.targetY = null;
      cameraRef.current.targetZoom = null;
      return;
    }
    const idx = activeMatchIndex % matchedNodes.length;
    const matchTarget = matchedNodes[idx];
    const simNode = simNodesRef.current.find((sn) => sn.id === matchTarget.id);
    if (simNode) {
      cameraRef.current.targetX = -simNode.x;
      cameraRef.current.targetY = -simNode.y;
      cameraRef.current.targetZoom = 1.45;
      setSelectedNode(simNode);
    }
  }, [matchedNodes, activeMatchIndex]);

  // Force-directed physics + 60 FPS Canvas render loop with Level-of-Detail (LOD)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let animId;
    let tick = 0;

    const resizeCanvas = () => {
      const rect = canvas.parentElement.getBoundingClientRect();
      canvas.width = rect.width || 800;
      canvas.height = rect.height || 600;
    };
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    const matchedIdSet = new Set(matchedNodes.map((m) => m.id));

    const stepPhysicsAndRender = () => {
      tick += 1;
      const nodes = simNodesRef.current;
      const edges = simEdgesRef.current;
      const nodeMap = new Map(nodes.map((n) => [n.id, n]));

      // 1. Physics Step
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        if (a.pinned) continue;

        // Gentle center gravity
        a.vx += -a.x * 0.0018;
        a.vy += -a.y * 0.0018;

        // Pairwise Coulomb repulsion
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          let dx = a.x - b.x;
          let dy = a.y - b.y;
          let distSq = dx * dx + dy * dy + 0.1;
          if (distSq < 36000) {
            const force = 1600 / distSq;
            const dist = Math.sqrt(distSq);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            a.vx += fx;
            a.vy += fy;
            if (!b.pinned) {
              b.vx -= fx;
              b.vy -= fy;
            }
          }
        }
      }

      // Hooke spring attraction along edges
      for (const e of edges) {
        const src = nodeMap.get(e.source_id);
        const tgt = nodeMap.get(e.target_id);
        if (!src || !tgt) continue;
        const dx = tgt.x - src.x;
        const dy = tgt.y - src.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const targetLen = 115;
        const spring = (dist - targetLen) * 0.012;
        const fx = (dx / dist) * spring;
        const fy = (dy / dist) * spring;
        if (!src.pinned) {
          src.vx += fx;
          src.vy += fy;
        }
        if (!tgt.pinned) {
          tgt.vx -= fx;
          tgt.vy -= fy;
        }
      }

      // Velocity damping
      for (const n of nodes) {
        if (n.pinned) continue;
        n.vx *= 0.82;
        n.vy *= 0.82;
        n.x += Math.max(-8, Math.min(8, n.vx));
        n.y += Math.max(-8, Math.min(8, n.vy));
      }

      // Camera interpolation
      const cam = cameraRef.current;
      if (cam.targetX !== null && cam.targetY !== null) {
        cam.x += (cam.targetX - cam.x) * 0.12;
        cam.y += (cam.targetY - cam.y) * 0.12;
        if (cam.targetZoom !== null) {
          cam.zoom += (cam.targetZoom - cam.zoom) * 0.12;
        }
        if (Math.abs(cam.targetX - cam.x) < 0.8 && Math.abs(cam.targetY - cam.y) < 0.8) {
          cam.targetX = null;
          cam.targetY = null;
          cam.targetZoom = null;
        }
      }

      // 2. Render Step
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const hoveredNodeId = hoveredNode?.id || null;
      const neighborIds = new Set();
      if (hoveredNodeId) {
        neighborIds.add(hoveredNodeId);
        for (const e of edges) {
          if (e.source_id === hoveredNodeId) neighborIds.add(e.target_id);
          if (e.target_id === hoveredNodeId) neighborIds.add(e.source_id);
        }
      }

      ctx.save();
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.scale(cam.zoom, cam.zoom);
      ctx.translate(cam.x, cam.y);

      // Draw Edges
      for (const e of edges) {
        const src = nodeMap.get(e.source_id);
        const tgt = nodeMap.get(e.target_id);
        if (!src || !tgt) continue;

        const isHighlighted = hoveredNodeId && (e.source_id === hoveredNodeId || e.target_id === hoveredNodeId);

        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.strokeStyle = isHighlighted
          ? "rgba(16, 185, 129, 0.75)"
          : hoveredNodeId
          ? "rgba(148, 163, 184, 0.1)"
          : "rgba(148, 163, 184, 0.28)";
        ctx.lineWidth = isHighlighted ? 2.0 : 1.1;
        ctx.stroke();

        // Edge label when zoomed in or highlighted
        if ((cam.zoom >= 1.15 || isHighlighted) && e.edge_type) {
          const mx = (src.x + tgt.x) / 2;
          const my = (src.y + tgt.y) / 2;
          ctx.font = "500 9px Inter, sans-serif";
          ctx.fillStyle = isHighlighted ? "#10B981" : "rgba(148, 163, 184, 0.65)";
          ctx.textAlign = "center";
          ctx.fillText(e.edge_type, mx, my - 3);
        }
      }

      // Draw Nodes
      for (const n of nodes) {
        const style = NODE_STYLES[n.entity_type] || NODE_STYLES.NOTE;
        let nodeColor = style.color;
        if (n.entity_type === "RISK" && n.metadata?.risk_level === "MEDIUM") {
          nodeColor = "#F59E0B";
        }

        const isMatched = matchedIdSet.has(n.id);
        const isSelected = selectedNode?.id === n.id;
        const isHovered = hoveredNodeId === n.id;
        const isHighlighted = isHovered || isSelected || isMatched;
        const isDimmed = (hoveredNodeId && !neighborIds.has(n.id)) || (matchedIdSet.size > 0 && !isMatched);

        ctx.save();
        ctx.globalAlpha = isDimmed ? 0.25 : 1.0;

        // Animated radar pulse for matches or selected node
        if (isMatched || isSelected) {
          const pulseRadius = style.radius + 6 + Math.sin(tick * 0.12) * 3;
          ctx.beginPath();
          ctx.arc(n.x, n.y, pulseRadius, 0, Math.PI * 2);
          ctx.strokeStyle = isMatched ? "#10B981" : "#38BDF8";
          ctx.lineWidth = 2.2;
          ctx.stroke();
        }

        // Node Circle
        ctx.beginPath();
        ctx.arc(n.x, n.y, style.radius, 0, Math.PI * 2);
        ctx.fillStyle = "#0F172A";
        ctx.fill();
        ctx.lineWidth = isSelected ? 3 : 2;
        ctx.strokeStyle = nodeColor;
        ctx.stroke();

        // Inner colored core
        ctx.beginPath();
        ctx.arc(n.x, n.y, style.radius - 4, 0, Math.PI * 2);
        ctx.fillStyle = `${nodeColor}33`;
        ctx.fill();

        // Short Type Badge inside node
        ctx.font = "700 8px Inter, sans-serif";
        ctx.fillStyle = nodeColor;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(style.badge, n.x, n.y);

        // Level-of-Detail (LOD) Node Label below node
        let shouldShowLabel = true;
        let shortLbl = n.label;

        if (cam.zoom < 0.72 && !isHighlighted) {
          // Low Zoom: Only show major hubs (DOC, CLAUSE_CATEGORY)
          if (["RISK", "OBLIGATION", "TAG"].includes(n.entity_type)) {
            shouldShowLabel = false;
          } else {
            shortLbl = n.label.length > 20 ? n.label.slice(0, 18) + "..." : n.label;
          }
        } else if (cam.zoom < 1.15 && !isHighlighted) {
          // Mid Zoom: Truncate leaf labels
          shortLbl = n.label.length > 18 ? n.label.slice(0, 16) + "..." : n.label;
        } else {
          // High Zoom or Highlighted: Full label
          shortLbl = n.label.length > 32 ? n.label.slice(0, 30) + "..." : n.label;
        }

        if (shouldShowLabel) {
          ctx.font = isHighlighted ? "700 11px Inter, sans-serif" : "600 10px Inter, sans-serif";
          ctx.fillStyle = isHighlighted ? "#FFFFFF" : "rgba(241, 245, 249, 0.88)";
          ctx.textAlign = "center";
          ctx.textBaseline = "top";
          ctx.fillText(shortLbl, n.x, n.y + style.radius + 5);
        }

        ctx.restore();
      }

      ctx.restore();
      animId = requestAnimationFrame(stepPhysicsAndRender);
    };

    animId = requestAnimationFrame(stepPhysicsAndRender);
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resizeCanvas);
    };
  }, [filteredGraph, hoveredNode, matchedNodes, selectedNode]);

  // Screen to world coordinates helper
  const screenToWorld = (clientX, clientY) => {
    const canvas = canvasRef.current;
    if (!canvas) return { wx: 0, wy: 0 };
    const rect = canvas.getBoundingClientRect();
    const sx = clientX - rect.left - canvas.width / 2;
    const sy = clientY - rect.top - canvas.height / 2;
    const cam = cameraRef.current;
    return {
      wx: sx / cam.zoom - cam.x,
      wy: sy / cam.zoom - cam.y,
    };
  };

  const findNodeAt = (wx, wy) => {
    const nodes = simNodesRef.current;
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const r = (NODE_STYLES[n.entity_type]?.radius || 16) + 5;
      const dx = wx - n.x;
      const dy = wy - n.y;
      if (dx * dx + dy * dy <= r * r) {
        return n;
      }
    }
    return null;
  };

  const handleMouseDown = (e) => {
    const { wx, wy } = screenToWorld(e.clientX, e.clientY);
    const hit = findNodeAt(wx, wy);
    if (hit) {
      hit.pinned = true;
      dragRef.current = {
        mode: "node",
        node: hit,
        lastX: e.clientX,
        lastY: e.clientY,
        moved: false,
      };
    } else {
      dragRef.current = {
        mode: "pan",
        node: null,
        lastX: e.clientX,
        lastY: e.clientY,
        moved: false,
      };
    }
  };

  const handleMouseMove = (e) => {
    const { wx, wy } = screenToWorld(e.clientX, e.clientY);
    const drag = dragRef.current;

    if (drag.mode === "node" && drag.node) {
      const dx = (e.clientX - drag.lastX) / cameraRef.current.zoom;
      const dy = (e.clientY - drag.lastY) / cameraRef.current.zoom;
      if (Math.abs(dx) > 1 || Math.abs(dy) > 1) drag.moved = true;
      drag.node.x += dx;
      drag.node.y += dy;
      drag.lastX = e.clientX;
      drag.lastY = e.clientY;
      return;
    }

    if (drag.mode === "pan") {
      const dx = (e.clientX - drag.lastX) / cameraRef.current.zoom;
      const dy = (e.clientY - drag.lastY) / cameraRef.current.zoom;
      if (Math.abs(dx) > 1 || Math.abs(dy) > 1) drag.moved = true;
      cameraRef.current.x += dx;
      cameraRef.current.y += dy;
      drag.lastX = e.clientX;
      drag.lastY = e.clientY;
      return;
    }

    const hit = findNodeAt(wx, wy);
    setHoveredNode(hit || null);
    setHoverPos(hit ? { x: e.clientX, y: e.clientY } : null);
  };

  const handleMouseUp = () => {
    const drag = dragRef.current;
    if (drag.mode === "node" && drag.node) {
      drag.node.pinned = false;
      if (!drag.moved) {
        setSelectedNode(drag.node);
      }
    } else if (drag.mode === "pan" && !drag.moved) {
      setSelectedNode(null);
    }
    dragRef.current = { mode: null, node: null, lastX: 0, lastY: 0, moved: false };
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.12 : 0.9;
    cameraRef.current.zoom = Math.max(0.35, Math.min(2.6, cameraRef.current.zoom * factor));
  };

  const handleResetView = () => {
    cameraRef.current = {
      x: 0,
      y: 0,
      zoom: 1.0,
      targetX: null,
      targetY: null,
      targetZoom: null,
    };
  };

  const stats = graphData?.stats || {};

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        background: "radial-gradient(circle at center, #0F172A 0%, #020617 100%)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Top Header Row: View Mode Switcher, Search, and Action Buttons */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "0.6rem",
          padding: "0.5rem 0.9rem",
          background: "rgba(15, 23, 42, 0.95)",
          borderBottom: "1px solid rgba(51, 65, 85, 0.7)",
          zIndex: 10,
          flexWrap: "wrap",
        }}
      >
        {/* Left: View Mode Segmented Pill */}
        <div style={{ display: "flex", alignItems: "center", background: "rgba(2, 6, 23, 0.7)", borderRadius: "6px", padding: "2px", border: "1px solid rgba(51, 65, 85, 0.7)" }}>
          <button
            type="button"
            onClick={() => setViewMode("current")}
            style={{
              background: viewMode === "current" ? "#10B981" : "transparent",
              color: viewMode === "current" ? "#022C22" : "#94A3B8",
              border: "none",
              borderRadius: "4px",
              padding: "3px 9px",
              fontSize: "0.72rem",
              fontWeight: 700,
              cursor: "pointer",
            }}
            title="Display active legal contract state (latest review run only)"
          >
            🎯 Current State
          </button>
          <button
            type="button"
            onClick={() => setViewMode("timeline")}
            style={{
              background: viewMode === "timeline" ? "#3B82F6" : "transparent",
              color: viewMode === "timeline" ? "#FFFFFF" : "#94A3B8",
              border: "none",
              borderRadius: "4px",
              padding: "3px 9px",
              fontSize: "0.72rem",
              fontWeight: 700,
              cursor: "pointer",
            }}
            title="Display all historical review runs and audit progressions"
          >
            📚 Review Timeline
          </button>
        </div>

        {/* Center: Search in Graph */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flex: 1, maxWidth: "360px" }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setActiveMatchIndex(0);
            }}
            placeholder="🔍 Find in Graph (e.g. Audit, High, Vendor)..."
            style={{
              width: "100%",
              background: "rgba(2, 6, 23, 0.8)",
              border: "1px solid rgba(16, 185, 129, 0.35)",
              borderRadius: "6px",
              padding: "0.3rem 0.65rem",
              color: "#F8FAFC",
              fontSize: "0.75rem",
            }}
          />
          {searchQuery && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.3rem", fontSize: "0.72rem", flexShrink: 0 }}>
              <span style={{ color: matchedNodes.length > 0 ? "#10B981" : "#EF4444", fontWeight: 700 }}>
                {matchedNodes.length > 0
                  ? `${(activeMatchIndex % matchedNodes.length) + 1} of ${matchedNodes.length}`
                  : "0 matches"}
              </span>
              {matchedNodes.length > 1 && (
                <button
                  type="button"
                  onClick={() => setActiveMatchIndex((i) => i + 1)}
                  style={{
                    background: "rgba(16, 185, 129, 0.16)",
                    color: "#10B981",
                    border: "1px solid rgba(16, 185, 129, 0.35)",
                    borderRadius: "4px",
                    padding: "1px 6px",
                    fontSize: "0.7rem",
                    cursor: "pointer",
                  }}
                >
                  Next ›
                </button>
              )}
            </div>
          )}
        </div>

        {/* Right: Camera Reset & Refresh */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
          <button
            type="button"
            onClick={handleResetView}
            style={{
              background: "rgba(255,255,255,0.06)",
              color: "#CBD5E1",
              border: "1px solid rgba(255,255,255,0.12)",
              borderRadius: "5px",
              padding: "3px 8px",
              fontSize: "0.72rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
            title="Reset Camera Zoom & Pan"
          >
            🎯 Fit
          </button>
          {onRefreshGraph && (
            <button
              type="button"
              onClick={onRefreshGraph}
              style={{
                background: "rgba(255,255,255,0.06)",
                color: "#CBD5E1",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: "5px",
                padding: "3px 8px",
                fontSize: "0.72rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
              title="Resynchronize Graph from SQLite"
            >
              ↻ Sync
            </button>
          )}
        </div>
      </div>

      {/* Second Toolbar Row: Clause Category Isolation, Severity & Party Filter Pills */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          padding: "0.4rem 0.9rem",
          background: "rgba(15, 23, 42, 0.85)",
          borderBottom: "1px solid rgba(51, 65, 85, 0.4)",
          zIndex: 8,
          flexWrap: "wrap",
        }}
      >
        {/* Clause Category Isolation Selector */}
        <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <span style={{ fontSize: "0.68rem", fontWeight: 700, color: "#6366F1", textTransform: "uppercase" }}>
            Clause:
          </span>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            style={{
              background: categoryFilter !== "ALL" ? "rgba(99, 102, 241, 0.2)" : "rgba(2, 6, 23, 0.7)",
              color: categoryFilter !== "ALL" ? "#A5B4FC" : "#CBD5E1",
              border: `1px solid ${categoryFilter !== "ALL" ? "rgba(99, 102, 241, 0.5)" : "rgba(51, 65, 85, 0.7)"}`,
              borderRadius: "5px",
              padding: "2px 6px",
              fontSize: "0.72rem",
              fontWeight: 600,
              cursor: "pointer",
              maxWidth: "200px",
            }}
          >
            <option value="ALL">All Categories ({availableCategories.length})</option>
            {availableCategories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
          {categoryFilter !== "ALL" && (
            <button
              type="button"
              onClick={() => setCategoryFilter("ALL")}
              style={{
                background: "transparent",
                border: "none",
                color: "#94A3B8",
                fontSize: "0.72rem",
                cursor: "pointer",
                padding: "0 2px",
              }}
              title="Clear Category Filter"
            >
              ✕
            </button>
          )}
        </div>

        {/* Severity Filter Pills */}
        <div style={{ display: "flex", alignItems: "center", gap: "3px" }}>
          <span style={{ fontSize: "0.68rem", fontWeight: 700, color: "#94A3B8", textTransform: "uppercase" }}>
            Risk:
          </span>
          {["ALL", "HIGH", "MEDIUM", "LOW"].map((sev) => {
            const active = severityFilter === sev;
            const colors = {
              ALL: "#94A3B8",
              HIGH: "#EF4444",
              MEDIUM: "#F59E0B",
              LOW: "#10B981",
            };
            return (
              <button
                key={sev}
                type="button"
                onClick={() => setSeverityFilter(sev)}
                style={{
                  background: active ? `${colors[sev]}26` : "transparent",
                  color: active ? colors[sev] : "#64748B",
                  border: `1px solid ${active ? colors[sev] + "66" : "rgba(255,255,255,0.06)"}`,
                  borderRadius: "4px",
                  padding: "1px 6px",
                  fontSize: "0.66rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {sev}
              </button>
            );
          })}
        </div>

        {/* Party Filter Pills */}
        <div style={{ display: "flex", alignItems: "center", gap: "3px" }}>
          <span style={{ fontSize: "0.68rem", fontWeight: 700, color: "#94A3B8", textTransform: "uppercase" }}>
            Party:
          </span>
          {["ALL", "VENDOR", "CUSTOMER", "MUTUAL"].map((party) => {
            const active = partyFilter === party;
            const colors = {
              ALL: "#94A3B8",
              VENDOR: "#14B8A6",
              CUSTOMER: "#60A5FA",
              MUTUAL: "#C084FC",
            };
            return (
              <button
                key={party}
                type="button"
                onClick={() => setPartyFilter(party)}
                style={{
                  background: active ? `${colors[party]}26` : "transparent",
                  color: active ? colors[party] : "#64748B",
                  border: `1px solid ${active ? colors[party] + "66" : "rgba(255,255,255,0.06)"}`,
                  borderRadius: "4px",
                  padding: "1px 6px",
                  fontSize: "0.66rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {party}
              </button>
            );
          })}
        </div>

        {/* Entity Type Legend & Quick Toggles */}
        <div style={{ display: "flex", alignItems: "center", gap: "3px", marginLeft: "auto" }}>
          {[
            { type: "DOCUMENT", count: stats.documents || 0 },
            { type: "CLAUSE_CATEGORY", count: stats.clause_categories || 0 },
            { type: "RISK", count: stats.risks || 0 },
            { type: "OBLIGATION", count: stats.obligations || 0 },
            { type: "REVIEW_RUN", count: stats.review_runs || 0 },
            { type: "NOTE", count: stats.notes || 0 },
          ].map(({ type, count }) => {
            const st = NODE_STYLES[type];
            const active = enabledTypes[type] !== false;
            return (
              <button
                key={type}
                type="button"
                onClick={() => setEnabledTypes((prev) => ({ ...prev, [type]: !active }))}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "3px",
                  background: active ? `${st.color}20` : "transparent",
                  color: active ? st.color : "#475569",
                  border: `1px solid ${active ? st.color + "44" : "rgba(255,255,255,0.06)"}`,
                  borderRadius: "4px",
                  padding: "1px 5px",
                  fontSize: "0.64rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
                title={`Toggle ${st.label}`}
              >
                <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: active ? st.color : "#475569" }} />
                <span>{st.badge}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2D Force-Directed HTML5 Canvas */}
      <div style={{ flex: 1, position: "relative" }}>
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onWheel={handleWheel}
          style={{
            width: "100%",
            height: "100%",
            cursor: hoveredNode ? "pointer" : "grab",
            display: "block",
          }}
        />

        {/* Instant Zero-Click Floating Hover Tooltip */}
        {hoveredNode && hoverPos && !selectedNode && (
          <div
            style={{
              position: "fixed",
              left: Math.min(window.innerWidth - 320, hoverPos.x + 14),
              top: Math.min(window.innerHeight - 170, hoverPos.y + 14),
              width: "290px",
              background: "rgba(15, 23, 42, 0.95)",
              backdropFilter: "blur(10px)",
              border: `1px solid ${NODE_STYLES[hoveredNode.entity_type]?.color || "#10B981"}88`,
              borderRadius: "8px",
              padding: "0.65rem 0.85rem",
              boxShadow: "0 10px 25px rgba(0,0,0,0.6)",
              pointerEvents: "none",
              zIndex: 50,
              display: "flex",
              flexDirection: "column",
              gap: "0.3rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span
                style={{
                  fontSize: "0.66rem",
                  fontWeight: 700,
                  color: NODE_STYLES[hoveredNode.entity_type]?.color || "#10B981",
                  textTransform: "uppercase",
                }}
              >
                {hoveredNode.entity_type}
                {hoveredNode.metadata?.risk_level ? ` • ${hoveredNode.metadata.risk_level} RISK` : ""}
                {hoveredNode.metadata?.party ? ` • ${hoveredNode.metadata.party}` : ""}
              </span>
              {hoveredNode.metadata?.page_number && (
                <span style={{ fontSize: "0.64rem", color: "#94A3B8" }}>
                  Page {hoveredNode.metadata.page_number}
                </span>
              )}
            </div>

            <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#F8FAFC", lineHeight: 1.3 }}>
              {hoveredNode.label}
            </div>

            {(hoveredNode.metadata?.action_required || hoveredNode.metadata?.description || hoveredNode.metadata?.verbatim_text) && (
              <div
                style={{
                  fontSize: "0.72rem",
                  color: "#CBD5E1",
                  background: "rgba(2, 6, 23, 0.5)",
                  padding: "0.3rem 0.5rem",
                  borderRadius: "4px",
                  lineHeight: 1.35,
                }}
              >
                {(() => {
                  const text = hoveredNode.metadata.action_required || hoveredNode.metadata.description || hoveredNode.metadata.verbatim_text;
                  return text.length > 95 ? text.slice(0, 92) + "..." : text;
                })()}
              </div>
            )}

            {hoveredNode.metadata?.deadline_or_cadence && (
              <div style={{ fontSize: "0.68rem", fontWeight: 600, color: "#F59E0B" }}>
                ⏱️ Deadline: {hoveredNode.metadata.deadline_or_cadence}
              </div>
            )}
          </div>
        )}

        {/* Selected Node Slide-Out Inspector Drawer */}
        {selectedNode && (
          <GraphInspectorDrawer
            node={selectedNode}
            allNodes={filteredGraph.nodes}
            edges={filteredGraph.edges}
            onClose={() => setSelectedNode(null)}
            onSelectNode={setSelectedNode}
            onOpenDocumentCitation={onOpenDocumentCitation}
            onPinToNote={onPinToNote}
          />
        )}
      </div>
    </div>
  );
}
