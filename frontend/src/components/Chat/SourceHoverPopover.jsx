// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React from "react";

export default function SourceHoverPopover({ evidence, position, onCitationClick }) {
  if (!evidence || !position) return null;

  const confidencePct = Math.round((evidence.confidence || 0.85) * 100);
  const confidenceColor =
    confidencePct >= 85 ? "var(--emerald-primary)" : confidencePct >= 70 ? "var(--amber-primary)" : "var(--text-muted)";

  const handleClick = (e) => {
    e.stopPropagation();
    if (onCitationClick) {
      onCitationClick(evidence);
    }
  };

  return (
    <div
      className="hover-preview-card"
      onClick={handleClick}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        cursor: "pointer",
        pointerEvents: "auto",
        zIndex: 9999,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.35rem" }}>
        <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--cyan-primary)" }}>
          {evidence.clause_title || `Page ${evidence.page_number}`}
        </span>
        <span
          style={{
            fontSize: "0.7rem",
            fontWeight: 600,
            color: confidenceColor,
            background: "rgba(255,255,255,0.06)",
            padding: "0.1rem 0.35rem",
            borderRadius: "4px",
          }}
        >
          {confidencePct}% Match
        </span>
      </div>

      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "0.45rem" }}>
        Doc: {evidence.filename} • Page {evidence.page_number} {evidence.section ? `• Section ${String(evidence.section).replace(/^(?:Section|Sec\.?|§)\s*/i, "")}` : ""}
      </div>

      <div
        style={{
          fontSize: "0.78rem",
          color: "var(--text-primary)",
          lineHeight: 1.45,
          fontStyle: "italic",
          background: "rgba(0,0,0,0.3)",
          padding: "0.45rem 0.6rem",
          borderRadius: "4px",
          borderLeft: "2px solid var(--emerald-primary)",
        }}
      >
        "{evidence.evidence_text}"
      </div>

      <div style={{ fontSize: "0.7rem", color: "#10B981", marginTop: "0.45rem", textAlign: "right", fontWeight: 600 }}>
        ⚡ Click to jump to paragraph &amp; highlight
      </div>
    </div>
  );
}
