// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState } from "react";

export default function ObligationsTable({
  obligations,
  onJumpToEvidence,
  onPinObligation,
  pinnedObligationIds = {},
}) {
  const [partyFilter, setPartyFilter] = useState("ALL");

  const filteredObligations = obligations.filter((o) => {
    if (partyFilter === "ALL") return true;
    return o.party === partyFilter;
  });

  const handleRowClick = (obl) => {
    if (onJumpToEvidence) {
      onJumpToEvidence({
        page_number: obl.page_number || 1,
        section: obl.section || null,
        bbox: obl.bbox || null,
        verbatim_excerpt: obl.verbatim_text || obl.action_required,
        confidence_score: Math.round((obl.confidence || 0.9) * 100),
      });
    }
  };

  return (
    <div className="obligations-wrapper" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Party Filter Pills */}
      <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>
          Party Filter:
        </span>
        {["ALL", "CUSTOMER", "VENDOR", "MUTUAL"].map((p) => (
          <button
            key={p}
            onClick={() => setPartyFilter(p)}
            style={{
              background: partyFilter === p ? "rgba(16, 185, 129, 0.2)" : "rgba(30, 41, 59, 0.5)",
              color: partyFilter === p ? "#10B981" : "var(--text-secondary)",
              border: `1px solid ${partyFilter === p ? "rgba(16, 185, 129, 0.4)" : "var(--border-base)"}`,
              borderRadius: "var(--radius-sm)",
              padding: "4px 10px",
              fontSize: "0.78rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            {p === "ALL" ? `All (${obligations.length})` : p}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="obligations-container">
        {filteredObligations.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.9rem" }}>
            No affirmative obligations match the selected filter.
          </div>
        ) : (
          <table className="obligations-table">
            <thead>
              <tr>
                <th style={{ width: "120px" }}>Party</th>
                <th>Mandatory Action Required</th>
                <th style={{ width: "220px" }}>Pre-Condition / Trigger</th>
                <th style={{ width: "180px" }}>Deadline / Cadence</th>
                <th style={{ width: "80px" }}>Location</th>
                <th style={{ width: "80px" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredObligations.map((obl, idx) => (
                <tr key={obl.id || idx}>
                  <td>
                    <span className={`party-badge ${obl.party}`}>{obl.party}</span>
                  </td>
                  <td style={{ fontWeight: 500, color: "var(--text-primary)" }}>
                    {obl.action_required}
                  </td>
                  <td style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>
                    {obl.trigger_or_condition ? obl.trigger_or_condition : <span style={{ color: "var(--text-muted)" }}>—</span>}
                  </td>
                  <td style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>
                    {obl.deadline_or_cadence ? (
                      <span style={{ color: "#F59E0B", fontWeight: 600 }}>{obl.deadline_or_cadence}</span>
                    ) : (
                      <span style={{ color: "var(--text-muted)" }}>—</span>
                    )}
                  </td>
                  <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    Page {obl.page_number}
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: "0.35rem" }}>
                      <button
                        className="btn-jump-evidence"
                        style={{ padding: "4px 8px", fontSize: "0.72rem" }}
                        onClick={() => handleRowClick(obl)}
                        title="Jump to bounding box in PDF viewer"
                      >
                        🔍 Jump
                      </button>
                      {onPinObligation && (
                        <button
                          type="button"
                          className="btn-jump-evidence"
                          style={{
                            padding: "4px 8px",
                            fontSize: "0.72rem",
                            background: pinnedObligationIds[obl.id]
                              ? "rgba(16, 185, 129, 0.2)"
                              : "rgba(6, 182, 212, 0.14)",
                            color: pinnedObligationIds[obl.id] ? "#10B981" : "#38BDF8",
                          }}
                          onClick={() => onPinObligation(obl)}
                          title="Save this Obligation to your Second Brain Note"
                        >
                          {pinnedObligationIds[obl.id] ? "✓ Saved" : "📌 Pin"}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
