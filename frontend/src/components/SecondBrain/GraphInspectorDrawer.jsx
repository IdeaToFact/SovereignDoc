// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState, useMemo } from "react";

const ENTITY_CONFIG = {
  DOCUMENT: { color: "#10B981", badge: "DOC", label: "Document" },
  REVIEW_RUN: { color: "#3B82F6", badge: "RUN", label: "Review Run" },
  CLAUSE_CATEGORY: { color: "#6366F1", badge: "CLS", label: "Clause Category" },
  RISK: { color: "#EF4444", badge: "RISK", label: "Legal Risk" },
  OBLIGATION: { color: "#14B8A6", badge: "DUTY", label: "Affirmative Duty" },
  NOTE: { color: "#06B6D4", badge: "NOTE", label: "Matter Note" },
  TAG: { color: "#A855F7", badge: "#", label: "Tag" },
};

const RISK_BADGES = {
  HIGH: { bg: "rgba(239, 68, 68, 0.18)", text: "#EF4444", border: "rgba(239, 68, 68, 0.4)", label: "HIGH RISK" },
  MEDIUM: { bg: "rgba(245, 158, 11, 0.18)", text: "#F59E0B", border: "rgba(245, 158, 11, 0.4)", label: "MEDIUM RISK" },
  LOW: { bg: "rgba(16, 185, 129, 0.18)", text: "#10B981", border: "rgba(16, 185, 129, 0.4)", label: "LOW RISK" },
};

const PARTY_BADGES = {
  VENDOR: { bg: "rgba(20, 184, 166, 0.18)", text: "#14B8A6", border: "rgba(20, 184, 166, 0.4)", label: "VENDOR DUTY" },
  CUSTOMER: { bg: "rgba(59, 130, 246, 0.18)", text: "#60A5FA", border: "rgba(59, 130, 246, 0.4)", label: "CUSTOMER DUTY" },
  MUTUAL: { bg: "rgba(168, 85, 247, 0.18)", text: "#C084FC", border: "rgba(168, 85, 247, 0.4)", label: "MUTUAL DUTY" },
};

export default function GraphInspectorDrawer({
  node,
  allNodes = [],
  edges = [],
  onClose,
  onSelectNode,
  onOpenDocumentCitation,
  onPinToNote,
}) {
  const [copied, setCopied] = useState(false);

  // Compute connected neighbors unconditionally at top level (Rules of Hooks)
  const connectedNeighbors = useMemo(() => {
    if (!node || !edges || edges.length === 0) return [];
    const neighborMap = new Map();
    const nodeMap = new Map((allNodes || []).map((n) => [n.id, n]));

    for (const e of edges) {
      if (e.source_id === node.id && nodeMap.has(e.target_id)) {
        const target = nodeMap.get(e.target_id);
        neighborMap.set(target.id, { node: target, relation: e.edge_type || "CONNECTS" });
      } else if (e.target_id === node.id && nodeMap.has(e.source_id)) {
        const source = nodeMap.get(e.source_id);
        neighborMap.set(source.id, { node: source, relation: e.edge_type || "CONNECTS" });
      }
    }
    return Array.from(neighborMap.values());
  }, [node, allNodes, edges]);

  // Early return after all hooks are declared
  if (!node) return null;

  const cfg = ENTITY_CONFIG[node.entity_type] || ENTITY_CONFIG.NOTE;
  const meta = node.metadata || {};

  const handleCopyCitation = () => {
    const citationText = meta.verbatim_text
      ? `"${meta.verbatim_text}"\n— ${node.label} (Page ${meta.page_number || 1}${meta.section ? `, ${meta.section}` : ""})`
      : `${node.label} [${node.entity_type}]`;
    navigator.clipboard?.writeText(citationText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleJumpToViewer = () => {
    if (!onOpenDocumentCitation) return;
    onOpenDocumentCitation({
      document_id: meta.document_id,
      page_number: meta.page_number || 1,
      section: meta.section,
      verbatim_text: meta.verbatim_text,
    });
  };

  const riskBadge = meta.risk_level ? RISK_BADGES[meta.risk_level] || RISK_BADGES.LOW : null;
  const partyBadge = meta.party ? PARTY_BADGES[meta.party] || PARTY_BADGES.MUTUAL : null;

  const prettyCategory = meta.category
    ? meta.category.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
    : "Operational";

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        right: 0,
        bottom: 0,
        width: "420px",
        maxWidth: "92%",
        background: "rgba(15, 23, 42, 0.97)",
        backdropFilter: "blur(12px)",
        borderLeft: "1px solid rgba(51, 65, 85, 0.8)",
        boxShadow: "-8px 0 32px rgba(0, 0, 0, 0.65)",
        zIndex: 40,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        animation: "drawerSlideIn 0.22s cubic-bezier(0.16, 1, 0.3, 1)",
      }}
    >
      <style>{`
        @keyframes drawerSlideIn {
          from { transform: translateX(100%); opacity: 0.5; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>

      {/* Top Drawer Header */}
      <div
        style={{
          padding: "1rem 1.1rem 0.85rem",
          borderBottom: "1px solid rgba(51, 65, 85, 0.6)",
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "0.5rem",
          background: "rgba(2, 6, 23, 0.4)",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem", flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.45rem", flexWrap: "wrap" }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                background: `${cfg.color}22`,
                color: cfg.color,
                border: `1px solid ${cfg.color}55`,
                borderRadius: "4px",
                padding: "2px 7px",
                fontSize: "0.68rem",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
              }}
            >
              <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: cfg.color }} />
              {cfg.label}
            </span>

            {riskBadge && (
              <span
                style={{
                  background: riskBadge.bg,
                  color: riskBadge.text,
                  border: `1px solid ${riskBadge.border}`,
                  borderRadius: "4px",
                  padding: "2px 7px",
                  fontSize: "0.68rem",
                  fontWeight: 700,
                }}
              >
                {riskBadge.label}
              </span>
            )}

            {partyBadge && (
              <span
                style={{
                  background: partyBadge.bg,
                  color: partyBadge.text,
                  border: `1px solid ${partyBadge.border}`,
                  borderRadius: "4px",
                  padding: "2px 7px",
                  fontSize: "0.68rem",
                  fontWeight: 700,
                }}
              >
                {partyBadge.label}
              </span>
            )}

            {meta.is_latest && (
              <span
                style={{
                  background: "rgba(16, 185, 129, 0.15)",
                  color: "#34D399",
                  borderRadius: "4px",
                  padding: "2px 6px",
                  fontSize: "0.65rem",
                  fontWeight: 600,
                }}
              >
                Latest Run
              </span>
            )}
          </div>

          <h2
            style={{
              margin: "0.2rem 0 0",
              fontSize: "1rem",
              fontWeight: 700,
              color: "#F8FAFC",
              lineHeight: 1.35,
              wordBreak: "break-word",
            }}
          >
            {node.label}
          </h2>
        </div>

        <button
          type="button"
          onClick={onClose}
          style={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: "6px",
            color: "#94A3B8",
            width: "28px",
            height: "28px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            flexShrink: 0,
          }}
          title="Close Inspector"
        >
          ✕
        </button>
      </div>

      {/* Scrollable Inspector Body */}
      <div style={{ flex: 1, overflowY: "auto", padding: "1rem 1.1rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
        {/* Specific Metadata Breakdown */}
        {node.entity_type === "OBLIGATION" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
            {meta.action_required && (
              <div
                style={{
                  background: "rgba(20, 184, 166, 0.08)",
                  border: "1px solid rgba(20, 184, 166, 0.25)",
                  borderRadius: "8px",
                  padding: "0.75rem",
                }}
              >
                <div style={{ fontSize: "0.68rem", fontWeight: 700, color: "#14B8A6", textTransform: "uppercase", marginBottom: "0.25rem" }}>
                  Action Required
                </div>
                <div style={{ fontSize: "0.82rem", color: "#F1F5F9", lineHeight: 1.45 }}>
                  {meta.action_required}
                </div>
              </div>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
              <div style={{ background: "rgba(2, 6, 23, 0.5)", border: "1px solid rgba(51, 65, 85, 0.6)", borderRadius: "6px", padding: "0.5rem 0.65rem" }}>
                <div style={{ fontSize: "0.66rem", color: "#94A3B8", textTransform: "uppercase" }}>Deadline / Cadence</div>
                <div style={{ fontSize: "0.8rem", fontWeight: 600, color: meta.deadline_or_cadence ? "#F59E0B" : "#64748B", marginTop: "2px" }}>
                  {meta.deadline_or_cadence ? `⏱️ ${meta.deadline_or_cadence}` : "None Specified"}
                </div>
              </div>
              <div style={{ background: "rgba(2, 6, 23, 0.5)", border: "1px solid rgba(51, 65, 85, 0.6)", borderRadius: "6px", padding: "0.5rem 0.65rem" }}>
                <div style={{ fontSize: "0.66rem", color: "#94A3B8", textTransform: "uppercase" }}>Clause Category</div>
                <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#6366F1", marginTop: "2px" }}>
                  {prettyCategory}
                </div>
              </div>
            </div>

            {meta.trigger_or_condition && (
              <div style={{ background: "rgba(2, 6, 23, 0.5)", border: "1px solid rgba(51, 65, 85, 0.6)", borderRadius: "6px", padding: "0.5rem 0.65rem" }}>
                <div style={{ fontSize: "0.66rem", color: "#94A3B8", textTransform: "uppercase", marginBottom: "2px" }}>Trigger / Condition</div>
                <div style={{ fontSize: "0.78rem", color: "#CBD5E1", fontStyle: "italic" }}>
                  {meta.trigger_or_condition}
                </div>
              </div>
            )}
          </div>
        )}

        {node.entity_type === "RISK" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
            <div
              style={{
                background: meta.risk_level === "HIGH" ? "rgba(239, 68, 68, 0.08)" : "rgba(245, 158, 11, 0.08)",
                border: `1px solid ${meta.risk_level === "HIGH" ? "rgba(239, 68, 68, 0.3)" : "rgba(245, 158, 11, 0.3)"}`,
                borderRadius: "8px",
                padding: "0.75rem",
              }}
            >
              <div style={{ fontSize: "0.68rem", fontWeight: 700, color: meta.risk_level === "HIGH" ? "#EF4444" : "#F59E0B", textTransform: "uppercase", marginBottom: "0.25rem" }}>
                Rule Issue: {meta.rule_id || "LEGAL_AUDIT_RULE"}
              </div>
              <div style={{ fontSize: "0.82rem", color: "#F1F5F9", lineHeight: 1.45 }}>
                {meta.description || meta.issue_title}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
              <div style={{ background: "rgba(2, 6, 23, 0.5)", border: "1px solid rgba(51, 65, 85, 0.6)", borderRadius: "6px", padding: "0.5rem 0.65rem" }}>
                <div style={{ fontSize: "0.66rem", color: "#94A3B8", textTransform: "uppercase" }}>Category</div>
                <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#A855F7", marginTop: "2px" }}>
                  {prettyCategory}
                </div>
              </div>
              <div style={{ background: "rgba(2, 6, 23, 0.5)", border: "1px solid rgba(51, 65, 85, 0.6)", borderRadius: "6px", padding: "0.5rem 0.65rem" }}>
                <div style={{ fontSize: "0.66rem", color: "#94A3B8", textTransform: "uppercase" }}>Detection Method</div>
                <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#38BDF8", marginTop: "2px" }}>
                  {meta.detection_method || "HEURISTIC"} ({Math.round((meta.confidence || 1) * 100)}%)
                </div>
              </div>
            </div>
          </div>
        )}

        {node.entity_type === "CLAUSE_CATEGORY" && (
          <div style={{ background: "rgba(99, 102, 241, 0.08)", border: "1px solid rgba(99, 102, 241, 0.3)", borderRadius: "8px", padding: "0.75rem" }}>
            <div style={{ fontSize: "0.68rem", fontWeight: 700, color: "#6366F1", textTransform: "uppercase", marginBottom: "0.25rem" }}>
              Category Classification
            </div>
            <div style={{ fontSize: "0.82rem", color: "#F1F5F9", lineHeight: 1.45 }}>
              Standard legal provisions for <strong>{node.label}</strong>. Contains linked risks and affirmative contractual duties.
            </div>
          </div>
        )}

        {node.entity_type === "REVIEW_RUN" && (
          <div style={{ background: "rgba(59, 130, 246, 0.08)", border: "1px solid rgba(59, 130, 246, 0.3)", borderRadius: "8px", padding: "0.75rem" }}>
            <div style={{ fontSize: "0.68rem", fontWeight: 700, color: "#60A5FA", textTransform: "uppercase", marginBottom: "0.25rem" }}>
              Review Audit Summary
            </div>
            <div style={{ fontSize: "0.82rem", color: "#F1F5F9", lineHeight: 1.45 }}>
              Run #{meta.run_number || 1} • Ruleset <code>{meta.ruleset_version || "1.0.0"}</code>
              <br />
              Identified <strong>{meta.total_risks || 0}</strong> risks and <strong>{meta.total_obligations || 0}</strong> affirmative duties.
            </div>
          </div>
        )}

        {/* Verbatim Contract Quote */}
        {meta.verbatim_text && (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                Verbatim Contract Excerpt
              </span>
              <button
                type="button"
                onClick={handleCopyCitation}
                style={{
                  background: "transparent",
                  border: "none",
                  color: copied ? "#10B981" : "#38BDF8",
                  fontSize: "0.7rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "3px",
                }}
              >
                {copied ? "✓ Copied!" : "📋 Copy Citation"}
              </button>
            </div>
            <div
              style={{
                fontSize: "0.78rem",
                color: "#E2E8F0",
                background: "rgba(2, 6, 23, 0.7)",
                borderLeft: `3px solid ${cfg.color}`,
                borderRadius: "0 6px 6px 0",
                padding: "0.65rem 0.8rem",
                lineHeight: 1.5,
                maxHeight: "180px",
                overflowY: "auto",
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                wordBreak: "break-word",
              }}
            >
              “{meta.verbatim_text}”
            </div>
          </div>
        )}

        {/* Grounding & Page Citation Info */}
        <div
          style={{
            background: "rgba(2, 6, 23, 0.4)",
            border: "1px solid rgba(51, 65, 85, 0.5)",
            borderRadius: "6px",
            padding: "0.55rem 0.75rem",
            fontSize: "0.72rem",
            color: "#94A3B8",
            display: "flex",
            flexDirection: "column",
            gap: "0.2rem",
          }}
        >
          <div>
            Entity ID: <code style={{ color: "#E2E8F0" }}>{node.entity_id}</code>
          </div>
          {meta.page_number && (
            <div>
              Citation: <strong>Page {meta.page_number}</strong> {meta.section ? `• ${meta.section}` : ""}
            </div>
          )}
          {meta.run_number && <div>Run Iteration: Review #{meta.run_number}</div>}
        </div>

        {/* Connected Graph Neighbors */}
        {connectedNeighbors.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "#94A3B8", textTransform: "uppercase" }}>
              Connected Entities ({connectedNeighbors.length})
            </span>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem", maxHeight: "150px", overflowY: "auto" }}>
              {connectedNeighbors.map(({ node: neighbor, relation }) => {
                const ncfg = ENTITY_CONFIG[neighbor.entity_type] || ENTITY_CONFIG.NOTE;
                return (
                  <button
                    key={neighbor.id}
                    type="button"
                    onClick={() => onSelectNode && onSelectNode(neighbor)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: "0.5rem",
                      background: "rgba(2, 6, 23, 0.5)",
                      border: "1px solid rgba(51, 65, 85, 0.6)",
                      borderRadius: "6px",
                      padding: "0.35rem 0.6rem",
                      textAlign: "left",
                      cursor: "pointer",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", minWidth: 0 }}>
                      <span
                        style={{
                          width: "7px",
                          height: "7px",
                          borderRadius: "50%",
                          background: ncfg.color,
                          flexShrink: 0,
                        }}
                      />
                      <span
                        style={{
                          fontSize: "0.74rem",
                          color: "#E2E8F0",
                          fontWeight: 500,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {neighbor.label}
                      </span>
                    </div>
                    <span style={{ fontSize: "0.62rem", color: "#64748B", flexShrink: 0, textTransform: "uppercase" }}>
                      {relation}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Sticky Action Footer */}
      <div
        style={{
          padding: "0.85rem 1.1rem",
          borderTop: "1px solid rgba(51, 65, 85, 0.6)",
          background: "rgba(2, 6, 23, 0.7)",
          display: "flex",
          flexDirection: "column",
          gap: "0.5rem",
        }}
      >
        {node.entity_type !== "TAG" && meta.document_id && (
          <button
            type="button"
            onClick={handleJumpToViewer}
            style={{
              width: "100%",
              background: "#10B981",
              color: "#022C22",
              border: "none",
              borderRadius: "6px",
              padding: "0.55rem 0.8rem",
              fontSize: "0.8rem",
              fontWeight: 700,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
            }}
          >
            <span>📄</span>
            <span>Open in Contract Viewer (Page {meta.page_number || 1})</span>
          </button>
        )}

        {onPinToNote && node.entity_type !== "NOTE" && (
          <button
            type="button"
            onClick={() => onPinToNote(node)}
            style={{
              width: "100%",
              background: "rgba(255, 255, 255, 0.06)",
              color: "#F8FAFC",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              borderRadius: "6px",
              padding: "0.45rem 0.8rem",
              fontSize: "0.76rem",
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
            }}
          >
            <span>📝</span>
            <span>Pin Citation to Active Note</span>
          </button>
        )}
      </div>
    </div>
  );
}
