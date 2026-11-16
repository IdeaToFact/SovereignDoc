// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState } from "react";
import { api } from "../../services/api";

export default function RedlineDiffView({ vaultId, documents }) {
  const [docAId, setDocAId] = useState(documents && documents.length > 0 ? documents[0].id : "");
  const [docBId, setDocBId] = useState(documents && documents.length > 1 ? documents[1].id : (documents && documents[0] ? documents[0].id : ""));
  const [diffResult, setDiffResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCompare = async () => {
    if (!vaultId || !docAId || !docBId) return;
    setLoading(true);
    try {
      const res = await api.compareContracts(vaultId, docAId, docBId);
      setDiffResult(res);
    } catch (err) {
      console.error("Failed to compare contracts", err);
      alert("Failed to compare contracts. Ensure both documents have indexed content.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="redline-view">
      {/* Header Selector Card */}
      <div className="redline-header-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2 style={{ margin: "0 0 0.35rem 0", fontSize: "1.25rem", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>⚖️</span> Contract Redline & Word Diff Viewer
            </h2>
            <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-muted)" }}>
              Side-by-side synchronized clause matching and token-level change detection.
            </p>
          </div>

          <button
            className="btn-audit-primary"
            onClick={handleCompare}
            disabled={loading || !docAId || !docBId || docAId === docBId}
          >
            {loading ? "Comparing Documents..." : "⚡ Run Redline Comparison"}
          </button>
        </div>

        {/* Document Selectors Row */}
        <div className="doc-selectors-row">
          <div className="doc-select-group">
            <label>Base Contract (Document A):</label>
            <select
              className="doc-select-dropdown"
              value={docAId}
              onChange={(e) => setDocAId(e.target.value)}
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename} ({d.chunk_count} chunks)
                </option>
              ))}
            </select>
          </div>

          <div style={{ fontSize: "1.2rem", color: "var(--text-muted)", alignSelf: "flex-end", marginBottom: "0.5rem" }}>
            ➔
          </div>

          <div className="doc-select-group">
            <label>Revised Contract (Document B):</label>
            <select
              className="doc-select-dropdown"
              value={docBId}
              onChange={(e) => setDocBId(e.target.value)}
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename} ({d.chunk_count} chunks)
                </option>
              ))}
            </select>
          </div>
        </div>

        {docAId === docBId && (
          <div style={{ fontSize: "0.8rem", color: "#F59E0B" }}>
            ⚠️ Please select two different documents to perform a meaningful contract comparison.
          </div>
        )}

        {/* Diff Stats Bar */}
        {diffResult && (
          <div className="diff-stats-bar">
            <span>Summary: <strong>{diffResult.summary_text}</strong></span>
            <span className="chip-additions">+{diffResult.total_additions} Words Added</span>
            <span className="chip-deletions">-{diffResult.total_deletions} Words Deleted</span>
          </div>
        )}
      </div>

      {/* Diff Clauses List */}
      {diffResult ? (
        <div className="diff-clauses-list">
          {diffResult.clauses.map((clause, idx) => (
            <div key={idx} className={`diff-clause-card status-${clause.status}`}>
              <div className="diff-clause-title-bar">
                <h4 className="diff-clause-title">
                  Section {clause.section}: {clause.title}
                </h4>
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    +{clause.additions} / -{clause.deletions}
                  </span>
                  <span className={`diff-status-pill ${clause.status}`}>
                    {clause.status}
                  </span>
                </div>
              </div>

              {/* Rendered Word Diff */}
              <div className="diff-content-box">
                {clause.tokens.map((tk, tIdx) => {
                  if (tk.type === "ins") {
                    return (
                      <span key={tIdx} className="diff-ins">
                        {tk.text}
                      </span>
                    );
                  }
                  if (tk.type === "del") {
                    return (
                      <span key={tIdx} className="diff-del">
                        {tk.text}
                      </span>
                    );
                  }
                  return <span key={tIdx}>{tk.text}</span>;
                })}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div
          style={{
            background: "var(--bg-surface)",
            border: "1px dashed var(--border-hover)",
            borderRadius: "var(--radius-lg)",
            padding: "4rem 2rem",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "1rem",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "2.5rem" }}>📄 ➔ 📝</div>
          <h3 style={{ margin: 0, fontSize: "1.2rem", color: "var(--text-primary)" }}>
            Select Two Documents to Compare
          </h3>
          <p style={{ margin: 0, color: "var(--text-muted)", maxWidth: "480px", fontSize: "0.88rem" }}>
            The local diff engine aligns matching legal clauses, computes word-level additions and deletions, and highlights revisions inline without sending contract drafts to external servers.
          </p>
        </div>
      )}
    </div>
  );
}
