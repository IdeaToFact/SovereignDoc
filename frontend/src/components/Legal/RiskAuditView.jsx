// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState, useEffect } from "react";
import { api } from "../../services/api";
import RiskCard from "./RiskCard";
import ObligationsTable from "./ObligationsTable";

export default function RiskAuditView({ vaultId, activeDocument, onJumpToEvidence }) {
  const [reviewRuns, setReviewRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeSubTab, setActiveSubTab] = useState("risks"); // "risks" | "obligations"
  const [severityFilter, setSeverityFilter] = useState("ALL"); // "ALL" | "HIGH" | "MEDIUM" | "LOW"
  const [pinnedItemIds, setPinnedItemIds] = useState({});

  const handlePinRisk = async (risk) => {
    if (!vaultId || !activeDocument || !risk) return;
    try {
      await api.quickCaptureToNote(vaultId, {
        document_id: activeDocument.id,
        filename: activeDocument.filename,
        page_number: risk.page_number || 1,
        section: risk.section || null,
        clause_title: risk.issue_title,
        verbatim_text: risk.verbatim_text || risk.description,
        commentary: risk.description,
        source_type: "RISK",
        risk_id: risk.id,
        risk_level: risk.risk_level,
        rule_id: risk.rule_id,
      });
      setPinnedItemIds((prev) => ({ ...prev, [risk.id]: true }));
    } catch (err) {
      console.error("Failed to pin risk to note:", err);
    }
  };

  const handlePinObligation = async (obl) => {
    if (!vaultId || !activeDocument || !obl) return;
    try {
      await api.quickCaptureToNote(vaultId, {
        document_id: activeDocument.id,
        filename: activeDocument.filename,
        page_number: obl.page_number || 1,
        section: obl.section || null,
        clause_title: obl.action_required,
        verbatim_text: obl.verbatim_text || obl.action_required,
        commentary: obl.trigger_or_condition
          ? `Trigger: ${obl.trigger_or_condition}`
          : null,
        source_type: "OBLIGATION",
        obligation_id: obl.id,
        party: obl.party,
        deadline: obl.deadline_or_cadence,
      });
      setPinnedItemIds((prev) => ({ ...prev, [obl.id]: true }));
    } catch (err) {
      console.error("Failed to pin obligation to note:", err);
    }
  };

  // Load existing review runs when active document changes
  useEffect(() => {
    if (!vaultId || !activeDocument) {
      setReviewRuns([]);
      setSelectedRun(null);
      return;
    }

    const loadRuns = async () => {
      try {
        const runs = await api.listReviewRuns(vaultId, activeDocument.id);
        const validRuns = Array.isArray(runs) ? runs : [];
        setReviewRuns(validRuns);
        if (validRuns.length > 0) {
          // If the latest run used the legacy 1.0.0 ruleset, automatically run a fresh 1.1.0 review
          if (validRuns[0].ruleset_version === "1.0.0") {
            const upgradedRun = await api.createReviewRun(vaultId, activeDocument.id);
            setSelectedRun(upgradedRun);
            const updatedRuns = await api.listReviewRuns(vaultId, activeDocument.id);
            setReviewRuns(Array.isArray(updatedRuns) ? updatedRuns : []);
          } else {
            const latest = await api.getReviewRun(vaultId, activeDocument.id, validRuns[0].id);
            setSelectedRun(latest);
          }
        } else {
          setSelectedRun(null);
        }
      } catch (err) {
        console.error("Failed to load review runs", err);
        setReviewRuns([]);
        setSelectedRun(null);
      }
    };

    loadRuns();
  }, [vaultId, activeDocument]);

  // Execute a new ReviewRun
  const handleExecuteReview = async () => {
    if (!vaultId || !activeDocument) return;
    setLoading(true);
    try {
      const newRun = await api.createReviewRun(vaultId, activeDocument.id);
      setSelectedRun(newRun);
      const runs = await api.listReviewRuns(vaultId, activeDocument.id);
      setReviewRuns(runs || []);
    } catch (err) {
      console.error("Error executing review run", err);
      alert("Review run failed. Ensure document has indexed text chunks.");
    } finally {
      setLoading(false);
    }
  };

  // Change selected historical review run
  const handleSelectRun = async (runId) => {
    if (!vaultId || !activeDocument || !runId) return;
    setLoading(true);
    try {
      const runData = await api.getReviewRun(vaultId, activeDocument.id, runId);
      setSelectedRun(runData);
    } catch (err) {
      console.error("Failed to fetch historical run", err);
    } finally {
      setLoading(false);
    }
  };

  // Export Review Package (.ZIP)
  const handleExportPackage = () => {
    if (!vaultId || !activeDocument || !selectedRun) return;
    const url = api.getExportReviewPackageUrl(vaultId, activeDocument.id, selectedRun.id);
    window.open(url, "_blank");
  };

  if (!activeDocument) {
    return (
      <div className="legal-audit-view" style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ color: "var(--text-muted)", fontSize: "1rem" }}>
          Select or upload a contract document to perform a Legal Risk & Obligations Audit.
        </div>
      </div>
    );
  }

  const risks = selectedRun?.risks || [];
  const obligations = selectedRun?.obligations || [];

  const highRisksCount = risks.filter((r) => r.risk_level === "HIGH").length;
  const medRisksCount = risks.filter((r) => r.risk_level === "MEDIUM").length;
  const lowRisksCount = risks.filter((r) => r.risk_level === "LOW").length;

  const filteredRisks = risks.filter((r) => {
    if (severityFilter === "ALL") return true;
    return r.risk_level === severityFilter;
  });

  return (
    <div className="legal-audit-view">
      {/* Top Action Bar */}
      <div className="legal-top-bar">
        <div className="legal-title-section">
          <h2>
            <span>⚖️</span> Legal & Contract Intelligence Audit
          </h2>
          <p>
            Document: <strong>{activeDocument.filename}</strong> &bull; Versioned Non-Destructive Review Engine
          </p>
        </div>

        <div className="legal-actions-group">
          {reviewRuns.length > 0 && (
            <select
              className="run-select-dropdown"
              value={selectedRun?.id || ""}
              onChange={(e) => handleSelectRun(e.target.value)}
              disabled={loading}
            >
              {reviewRuns.map((r, i) => (
                <option key={r.id} value={r.id}>
                  Review #{reviewRuns.length - i} &bull; {new Date(r.started_at).toLocaleTimeString()} ({r.total_risks} risks)
                </option>
              ))}
            </select>
          )}

          <button
            className="btn-audit-primary"
            onClick={handleExecuteReview}
            disabled={loading}
          >
            {loading ? "Analyzing Contract..." : selectedRun ? "🔄 Re-run Review" : "⚡ Run Contract Audit"}
          </button>

          <button
            className="btn-export-pkg"
            onClick={handleExportPackage}
            disabled={!selectedRun || loading}
            title="Download contract_review.zip with markdown audit brief, risk matrix CSV, and obligations CSV"
          >
            <span>📥</span> Export Review Package (.ZIP)
          </button>
        </div>
      </div>

      {selectedRun ? (
        <>
          {/* Summary Metrics Banner */}
          <div className="audit-metrics-banner">
            <div
              className="metric-card high-risk"
              style={{ cursor: "pointer" }}
              onClick={() => {
                setActiveSubTab("risks");
                setSeverityFilter("HIGH");
              }}
              title="Filter High Severity Risks"
            >
              <div>
                <div className="metric-value">{highRisksCount}</div>
                <div className="metric-label">High Severity Risks</div>
              </div>
            </div>

            <div
              className="metric-card med-risk"
              style={{ cursor: "pointer" }}
              onClick={() => {
                setActiveSubTab("risks");
                setSeverityFilter("MEDIUM");
              }}
              title="Filter Medium Severity Risks"
            >
              <div>
                <div className="metric-value">{medRisksCount}</div>
                <div className="metric-label">Medium Severity Risks</div>
              </div>
            </div>

            <div
              className="metric-card low-risk"
              style={{ cursor: "pointer" }}
              onClick={() => {
                setActiveSubTab("risks");
                setSeverityFilter("LOW");
              }}
              title="Filter Low / Standard Terms"
            >
              <div>
                <div className="metric-value">{lowRisksCount}</div>
                <div className="metric-label">Low / Standard Terms</div>
              </div>
            </div>

            <div
              className="metric-card obligations"
              style={{ cursor: "pointer" }}
              onClick={() => setActiveSubTab("obligations")}
              title="View Affirmative Obligations Register"
            >
              <div>
                <div className="metric-value">{obligations.length}</div>
                <div className="metric-label">Affirmative Obligations</div>
              </div>
            </div>
          </div>

          {/* Subtab Navigation (Risks vs Obligations) */}
          <div className="subtab-nav">
            <button
              className={`subtab-btn ${activeSubTab === "risks" ? "active" : ""}`}
              onClick={() => setActiveSubTab("risks")}
            >
              ⚠️ Risk Matrix ({risks.length})
            </button>
            <button
              className={`subtab-btn ${activeSubTab === "obligations" ? "active" : ""}`}
              onClick={() => setActiveSubTab("obligations")}
            >
              📋 Affirmative Obligations ({obligations.length})
            </button>
          </div>

          {/* Subtab 1: Risk Matrix Cards */}
          {activeSubTab === "risks" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {/* Severity Filter Pills */}
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>
                  Filter Severity:
                </span>
                {["ALL", "HIGH", "MEDIUM", "LOW"].map((s) => (
                  <button
                    key={s}
                    onClick={() => setSeverityFilter(s)}
                    style={{
                      background: severityFilter === s ? "rgba(16, 185, 129, 0.2)" : "rgba(30, 41, 59, 0.5)",
                      color: severityFilter === s ? "#10B981" : "var(--text-secondary)",
                      border: `1px solid ${severityFilter === s ? "rgba(16, 185, 129, 0.4)" : "var(--border-base)"}`,
                      borderRadius: "var(--radius-sm)",
                      padding: "4px 10px",
                      fontSize: "0.78rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    {s === "ALL" ? `All (${risks.length})` : s}
                  </button>
                ))}
              </div>

              {filteredRisks.length === 0 ? (
                <div style={{ background: "var(--bg-surface)", padding: "2.5rem", borderRadius: "var(--radius-md)", textAlign: "center", color: "var(--text-muted)" }}>
                  ✅ No risks match the selected filter.
                </div>
              ) : (
                <div className="risk-cards-grid">
                  {filteredRisks.map((risk) => (
                    <RiskCard
                      key={risk.id}
                      risk={risk}
                      onJumpToEvidence={onJumpToEvidence}
                      onPinRisk={handlePinRisk}
                      isPinned={Boolean(pinnedItemIds[risk.id])}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Subtab 2: Obligations Table */}
          {activeSubTab === "obligations" && (
            <ObligationsTable
              obligations={obligations}
              onJumpToEvidence={onJumpToEvidence}
              onPinObligation={handlePinObligation}
              pinnedObligationIds={pinnedItemIds}
            />
          )}
        </>
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
          <div style={{ fontSize: "2.5rem" }}>🛡️</div>
          <h3 style={{ margin: 0, fontSize: "1.2rem", color: "var(--text-primary)" }}>
            No Audit Executed for this Document
          </h3>
          <p style={{ margin: 0, color: "var(--text-muted)", maxWidth: "480px", fontSize: "0.88rem" }}>
            Run the 100% local deterministic risk engine to scan for uncapped liability, unilateral indemnity, evergreen renewals, short notice periods, and affirmative covenants.
          </p>
          <button
            className="btn-audit-primary"
            style={{ marginTop: "0.5rem" }}
            onClick={handleExecuteReview}
            disabled={loading}
          >
            {loading ? "Analyzing Contract..." : "⚡ Run Contract Audit Now"}
          </button>
        </div>
      )}
    </div>
  );
}
