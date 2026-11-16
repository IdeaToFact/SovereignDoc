// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState } from "react";

export default function MultiCitationGroup({
  evidenceList,
  onCitationClick,
  onHoverEvidence,
  onPinEvidence,
  pinnedIds = {},
}) {
  const [expanded, setExpanded] = useState(false);

  if (!evidenceList || evidenceList.length === 0) return null;

  const topConfidence = Math.max(...evidenceList.map((e) => e.confidence || 0.8));
  const topConfidencePct = Math.round(topConfidence * 100);

  return (
    <div className="sources-accordion">
      <div className="sources-header" onClick={() => setExpanded(!expanded)}>
        <span>
          {expanded ? "▼" : "▶"} Sources ({evidenceList.length}) — {topConfidencePct}% Grounded Confidence
        </span>
        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
          {expanded ? "Click to collapse" : "Click to view sources"}
        </span>
      </div>

      {expanded && (
        <div className="evidence-chip-list">
          {evidenceList.map((ev, i) => (
            <div
              key={ev.citation_id || i}
              className="evidence-chip"
              onClick={() => onCitationClick(ev)}
              onMouseEnter={(e) => onHoverEvidence(e, ev)}
              onMouseLeave={() => onHoverEvidence(null, null)}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <span style={{ color: "var(--emerald-primary)", fontWeight: 700 }}>■</span>
                <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                  {ev.clause_title || `Page ${ev.page_number}`}
                </span>
                <span style={{ color: "var(--text-muted)", fontSize: "0.7rem" }}>
                  (Page {ev.page_number})
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
                <span style={{ fontSize: "0.7rem", color: "var(--emerald-primary)", fontWeight: 600 }}>
                  {Math.round((ev.confidence || 0.85) * 100)}%
                </span>
                {onPinEvidence && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onPinEvidence(ev);
                    }}
                    style={{
                      background: pinnedIds[ev.citation_id]
                        ? "rgba(16, 185, 129, 0.2)"
                        : "rgba(6, 182, 212, 0.14)",
                      color: pinnedIds[ev.citation_id] ? "#10B981" : "#38BDF8",
                      border: "1px solid rgba(6, 182, 212, 0.3)",
                      borderRadius: "4px",
                      padding: "1px 6px",
                      fontSize: "0.68rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                    title="Pin this grounded excerpt to your Second Brain Note"
                  >
                    {pinnedIds[ev.citation_id] ? "✓ Saved" : "📌 Save to Note"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}