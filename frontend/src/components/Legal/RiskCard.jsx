// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React from "react";

export default function RiskCard({ risk, onJumpToEvidence, onPinRisk, isPinned }) {
  const {
    id,
    rule_id,
    category,
    risk_level,
    issue_title,
    description,
    page_number,
    section,
    verbatim_text,
    confidence,
    detection_method,
    bbox,
  } = risk;

  const handleJump = () => {
    if (onJumpToEvidence) {
      onJumpToEvidence({
        page_number: page_number || 1,
        section: section || null,
        bbox: bbox || null,
        verbatim_excerpt: verbatim_text,
        confidence_score: Math.round(confidence * 100),
      });
    }
  };

  return (
    <div className={`risk-card severity-${risk_level}`}>
      <div className="risk-card-header">
        <span className={`severity-pill ${risk_level}`}>{risk_level} RISK</span>
        <span className="category-chip">{category}</span>
      </div>

      <h4 className="risk-card-title">{issue_title}</h4>
      <p className="risk-card-desc">{description}</p>

      {verbatim_text && (
        <div className="risk-quote-box">
          "{verbatim_text.length > 220 ? verbatim_text.slice(0, 220) + "..." : verbatim_text}"
        </div>
      )}

      <div className="risk-provenance-bar">
        <span>Rule: <code>{rule_id}</code></span>
        <span>Method: <code>{detection_method}</code> ({Math.round(confidence * 100)}%)</span>
        <span>Page {page_number}{section ? ` (Sec ${section})` : ""}</span>
      </div>

      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.25rem" }}>
        <button className="btn-jump-evidence" style={{ flex: 1 }} onClick={handleJump}>
          <span>🔍</span> Jump to Page {page_number} Evidence
        </button>
        {onPinRisk && (
          <button
            type="button"
            className="btn-jump-evidence"
            onClick={() => onPinRisk(risk)}
            style={{
              background: isPinned ? "rgba(16, 185, 129, 0.2)" : "rgba(6, 182, 212, 0.14)",
              color: isPinned ? "#10B981" : "#38BDF8",
              borderColor: isPinned ? "rgba(16, 185, 129, 0.4)" : "rgba(6, 182, 212, 0.35)",
            }}
            title="Pin this Risk finding to your Second Brain Note"
          >
            {isPinned ? "✓ Saved to Note" : "📌 Save to Note"}
          </button>
        )}
      </div>
    </div>
  );
}
