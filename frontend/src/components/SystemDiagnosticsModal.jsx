// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { api } from "../services/api";

export default function SystemDiagnosticsModal({
  isOpen,
  onClose,
  initialTab = "airgap", // "airgap" | "benchmark"
  hardware,
  activeVault,
}) {
  const [activeTab, setActiveTab] = useState(initialTab);
  const [auditReport, setAuditReport] = useState(null);
  const [loadingAudit, setLoadingAudit] = useState(false);
  const [vaultStats, setVaultStats] = useState(null);

  const [benchmarkResult, setBenchmarkResult] = useState(null);
  const [runningBenchmark, setRunningBenchmark] = useState(false);

  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  useEffect(() => {
    if (isOpen) {
      if (!auditReport) {
        loadAudit(false);
      }
      if (activeVault?.id) {
        api
          .getVaultGraphStats(activeVault.id)
          .then((res) => setVaultStats(res.stats || null))
          .catch(() => {});
      }
    }
  }, [isOpen, activeVault?.id]);

  const loadAudit = async (refresh = false) => {
    setLoadingAudit(true);
    try {
      const report = await api.getAirgapAudit(refresh);
      setAuditReport(report);
    } catch (err) {
      console.error("Failed to load air-gap audit", err);
    } finally {
      setLoadingAudit(false);
    }
  };

  const handleRunBenchmark = async () => {
    setRunningBenchmark(true);
    try {
      const res = await api.runHardwareBenchmark();
      setBenchmarkResult(res);
    } catch (err) {
      console.error("Failed to run hardware benchmark", err);
    } finally {
      setRunningBenchmark(false);
    }
  };

  if (!isOpen) return null;

  const e2e = benchmarkResult?.end_to_end_document_benchmark;
  const comp = benchmarkResult?.components;

  return createPortal(
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(9, 13, 22, 0.82)",
        backdropFilter: "blur(4px)",
        zIndex: 99999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem 1.5rem",
        overflowY: "auto",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "820px",
          maxHeight: "calc(100vh - 4rem)",
          margin: "auto",
          backgroundColor: "var(--bg-secondary, #111827)",
          border: "1px solid var(--border-color, #1F2937)",
          borderRadius: "12px",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          boxShadow: "0 24px 48px rgba(0,0,0,0.6)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "1rem 1.25rem",
            borderBottom: "1px solid var(--border-color, #1F2937)",
            backgroundColor: "rgba(17, 24, 39, 0.95)",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <span style={{ fontSize: "1.2rem" }}>🛡️</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: "1rem", color: "#F9FAFB" }}>
                SovereignDoc System Diagnostics & Air-Gap Auditor
              </div>
              <div style={{ fontSize: "0.75rem", color: "#9CA3AF" }}>
                100% Local Execution Verification & Hardware Pipeline Profiler
              </div>
            </div>
          </div>

          <button
            className="btn-icon"
            onClick={onClose}
            title="Close Diagnostics"
            style={{ fontSize: "1.1rem", color: "#9CA3AF" }}
          >
            ✕
          </button>
        </div>

        {/* Tab Bar */}
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            padding: "0.75rem 1.25rem",
            borderBottom: "1px solid var(--border-color, #1F2937)",
            backgroundColor: "#0B0F19",
            flexShrink: 0,
          }}
        >
          <button
            onClick={() => setActiveTab("airgap")}
            style={{
              padding: "0.45rem 0.9rem",
              borderRadius: "6px",
              border: activeTab === "airgap" ? "1px solid #10B981" : "1px solid transparent",
              backgroundColor: activeTab === "airgap" ? "rgba(16, 185, 129, 0.15)" : "transparent",
              color: activeTab === "airgap" ? "#10B981" : "#9CA3AF",
              fontWeight: 600,
              fontSize: "0.82rem",
              cursor: "pointer",
            }}
          >
            🔒 Air-Gap Security Audit
          </button>
          <button
            onClick={() => setActiveTab("benchmark")}
            style={{
              padding: "0.45rem 0.9rem",
              borderRadius: "6px",
              border: activeTab === "benchmark" ? "1px solid #3B82F6" : "1px solid transparent",
              backgroundColor: activeTab === "benchmark" ? "rgba(59, 130, 246, 0.15)" : "transparent",
              color: activeTab === "benchmark" ? "#60A5FA" : "#9CA3AF",
              fontWeight: 600,
              fontSize: "0.82rem",
              cursor: "pointer",
            }}
          >
            ⚡ Hardware & 25-Page E2E Benchmark
          </button>
        </div>

        {/* Body Content */}
        <div style={{ padding: "1.25rem", overflowY: "auto", flex: 1, minHeight: 0 }}>
          {activeTab === "airgap" ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {/* Prominent Last Audit Status Banner */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.9rem 1.1rem",
                  borderRadius: "8px",
                  backgroundColor: auditReport?.passed !== false
                    ? "rgba(16, 185, 129, 0.1)"
                    : "rgba(239, 68, 68, 0.12)",
                  border: auditReport?.passed !== false
                    ? "1px solid rgba(16, 185, 129, 0.35)"
                    : "1px solid rgba(239, 68, 68, 0.4)",
                }}
              >
                <div>
                  <div style={{ fontSize: "0.92rem", fontWeight: 700, color: "#F9FAFB" }}>
                    Status:{" "}
                    <span style={{ color: auditReport?.passed !== false ? "#10B981" : "#EF4444" }}>
                      {loadingAudit
                        ? "Running Verification..."
                        : auditReport?.passed
                        ? "PASS ✅ (100% Air-Gap Verified)"
                        : "FAIL ❌"}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.76rem", color: "#9CA3AF", marginTop: "0.2rem" }}>
                    Last Air-Gap Audit: <strong>{auditReport?.last_audit_at || "Initializing..."}</strong>{" "}
                    • Schema v{auditReport?.audit_version || "1.0"} • Blocked External Attempts:{" "}
                    <strong>{auditReport?.blocked_external_attempts ?? 0}</strong>
                  </div>
                </div>
                <button
                  onClick={() => loadAudit(true)}
                  disabled={loadingAudit}
                  style={{
                    padding: "0.45rem 0.85rem",
                    borderRadius: "6px",
                    border: "1px solid #374151",
                    backgroundColor: "#1F2937",
                    color: "#E5E7EB",
                    fontSize: "0.78rem",
                    fontWeight: 600,
                    cursor: loadingAudit ? "wait" : "pointer",
                  }}
                >
                  {loadingAudit ? "Auditing..." : "↻ Run Audit Again"}
                </button>
              </div>

              {/* Individual Security Check Cards */}
              {auditReport?.checks?.map((chk) => (
                <div
                  key={chk.id}
                  style={{
                    padding: "0.8rem 1rem",
                    borderRadius: "8px",
                    backgroundColor: "#0B0F19",
                    border: "1px solid #1F2937",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "#E5E7EB" }}>
                      {chk.name}
                    </div>
                    <div style={{ fontSize: "0.73rem", color: "#9CA3AF", marginTop: "0.15rem" }}>
                      Check ID: <code>{chk.id}</code>
                    </div>
                  </div>
                  <span
                    style={{
                      padding: "0.22rem 0.6rem",
                      borderRadius: "999px",
                      fontSize: "0.72rem",
                      fontWeight: 700,
                      backgroundColor: chk.passed ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                      color: chk.passed ? "#10B981" : "#EF4444",
                    }}
                  >
                    {chk.passed ? "PASS" : "FAIL"}
                  </span>
                </div>
              ))}

              {/* Intercepted Network Layers & Storage Paths */}
              {auditReport && (
                <div
                  style={{
                    padding: "0.85rem 1rem",
                    borderRadius: "8px",
                    backgroundColor: "#0B0F19",
                    border: "1px solid #1F2937",
                    fontSize: "0.76rem",
                    color: "#9CA3AF",
                  }}
                >
                  <div style={{ fontWeight: 600, color: "#D1D5DB", marginBottom: "0.35rem" }}>
                    Protected Multi-Layer Network Interceptors:
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", marginBottom: "0.75rem" }}>
                    {(auditReport.intercepted_layers || []).map((layer) => (
                      <span
                        key={layer}
                        style={{
                          padding: "0.18rem 0.5rem",
                          borderRadius: "4px",
                          backgroundColor: "#1F2937",
                          color: "#A7F3D0",
                          fontFamily: "monospace",
                          fontSize: "0.7rem",
                        }}
                      >
                        {layer}
                      </span>
                    ))}
                  </div>
                  <div style={{ fontWeight: 600, color: "#D1D5DB", marginBottom: "0.25rem" }}>
                    Local Sovereign Data Directory:
                  </div>
                  <code style={{ color: "#93C5FD" }}>{auditReport.storage_paths?.base_data_dir}</code>

                  {vaultStats && (
                    <div style={{ marginTop: "0.85rem", paddingTop: "0.75rem", borderTop: "1px solid #1F2937" }}>
                      <div style={{ fontWeight: 600, color: "#D1D5DB", marginBottom: "0.4rem" }}>
                        Active Vault Knowledge Graph Statistics ({activeVault?.name || "Current Vault"}):
                      </div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                        {[
                          ["Documents", vaultStats.documents],
                          ["Reviews", vaultStats.review_runs],
                          ["Risks", vaultStats.risks],
                          ["Obligations", vaultStats.obligations],
                          ["Notes", vaultStats.notes],
                          ["Tags", vaultStats.tags],
                          ["Edges", vaultStats.total_edges],
                        ].map(([lbl, count]) => (
                          <span
                            key={lbl}
                            style={{
                              padding: "0.22rem 0.55rem",
                              borderRadius: "6px",
                              backgroundColor: "#111827",
                              border: "1px solid #374151",
                              color: "#E5E7EB",
                              fontSize: "0.72rem",
                            }}
                          >
                            {lbl}: <strong style={{ color: "#10B981" }}>{count ?? 0}</strong>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {/* Hardware Overview */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.9rem 1.1rem",
                  borderRadius: "8px",
                  backgroundColor: "rgba(59, 130, 246, 0.1)",
                  border: "1px solid rgba(59, 130, 246, 0.35)",
                }}
              >
                <div>
                  <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#F9FAFB" }}>
                    Accelerator: {hardware?.accelerator?.primary || "Local CPU/GPU Engine"}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#9CA3AF", marginTop: "0.2rem" }}>
                    CPU: {hardware?.cpu?.physical_cores || "-"} Physical / {hardware?.cpu?.logical_cores || "-"}{" "}
                    Logical Cores • RAM: {hardware?.ram?.available_gb || "-"} GB Free /{" "}
                    {hardware?.ram?.total_gb || "-"} GB Total
                  </div>
                </div>
                <button
                  onClick={handleRunBenchmark}
                  disabled={runningBenchmark}
                  style={{
                    padding: "0.5rem 0.95rem",
                    borderRadius: "6px",
                    border: "1px solid #3B82F6",
                    backgroundColor: "#2563EB",
                    color: "#FFFFFF",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    cursor: runningBenchmark ? "wait" : "pointer",
                  }}
                >
                  {runningBenchmark ? "Running 25-Page Benchmark..." : "⚡ Run 25-Page E2E Benchmark"}
                </button>
              </div>

              {benchmarkResult ? (
                <>
                  {/* Headline 25-Page E2E Benchmark Card */}
                  <div
                    style={{
                      padding: "1rem",
                      borderRadius: "8px",
                      backgroundColor: "#0B0F19",
                      border: "1px solid #10B981",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <div>
                      <div style={{ fontSize: "0.75rem", color: "#10B981", fontWeight: 700, textTransform: "uppercase" }}>
                        Headline End-to-End Document Benchmark ({e2e?.document_pages} Pages)
                      </div>
                      <div style={{ fontSize: "0.8rem", color: "#9CA3AF", marginTop: "0.2rem" }}>
                        Upload/Chunk → FastEmbed ONNX → Cross-Encoder Rerank → Contract ReviewRun → 7-Entity Graph Sync
                      </div>
                    </div>
                    <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#10B981" }}>
                      {e2e?.end_to_end_ms} ms
                    </div>
                  </div>

                  {/* Stage Breakdown Grid */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(2, 1fr)",
                      gap: "0.75rem",
                    }}
                  >
                    <div style={{ padding: "0.8rem", borderRadius: "8px", backgroundColor: "#0B0F19", border: "1px solid #1F2937" }}>
                      <div style={{ fontSize: "0.75rem", color: "#9CA3AF" }}>FastEmbed ONNX Throughput</div>
                      <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#F9FAFB", marginTop: "0.2rem" }}>
                        {comp?.onnx_embeddings?.chunks_per_sec} chunks/sec
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "#6B7280" }}>
                        {e2e?.stages_ms?.embedding_ms} ms total ({comp?.onnx_embeddings?.model_name})
                      </div>
                    </div>

                    <div style={{ padding: "0.8rem", borderRadius: "8px", backgroundColor: "#0B0F19", border: "1px solid #1F2937" }}>
                      <div style={{ fontSize: "0.75rem", color: "#9CA3AF" }}>Cross-Encoder Reranker</div>
                      <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#F9FAFB", marginTop: "0.2rem" }}>
                        {comp?.cross_encoder_reranker?.pairs_per_sec} pairs/sec
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "#6B7280" }}>
                        {e2e?.stages_ms?.rerank_ms} ms total ({comp?.cross_encoder_reranker?.model_name})
                      </div>
                    </div>

                    <div style={{ padding: "0.8rem", borderRadius: "8px", backgroundColor: "#0B0F19", border: "1px solid #1F2937" }}>
                      <div style={{ fontSize: "0.75rem", color: "#9CA3AF" }}>Deterministic Contract ReviewRun</div>
                      <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#F9FAFB", marginTop: "0.2rem" }}>
                        {e2e?.stages_ms?.contract_review_ms} ms
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "#6B7280" }}>
                        {comp?.contract_intelligence?.risks_detected} Risks & {comp?.contract_intelligence?.obligations_extracted} Obligations extracted
                      </div>
                    </div>

                    <div style={{ padding: "0.8rem", borderRadius: "8px", backgroundColor: "#0B0F19", border: "1px solid #1F2937" }}>
                      <div style={{ fontSize: "0.75rem", color: "#9CA3AF" }}>7-Entity Knowledge Graph Sync</div>
                      <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#F9FAFB", marginTop: "0.2rem" }}>
                        {e2e?.stages_ms?.knowledge_graph_sync_ms} ms
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "#6B7280" }}>
                        {comp?.knowledge_graph?.total_nodes} Nodes, {comp?.knowledge_graph?.total_edges} Edges • 100% Grounded
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div
                  style={{
                    padding: "2rem",
                    textAlign: "center",
                    borderRadius: "8px",
                    backgroundColor: "#0B0F19",
                    border: "1px dashed #374151",
                    color: "#9CA3AF",
                    fontSize: "0.85rem",
                  }}
                >
                  Click <strong>⚡ Run 25-Page E2E Benchmark</strong> above to profile local ONNX embeddings,
                  Cross-Encoder reranking, Contract ReviewRun, and Knowledge Graph sync on your machine.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}

