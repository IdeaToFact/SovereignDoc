// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import SystemDiagnosticsModal from "./SystemDiagnosticsModal";

export default function Header({
  hardware,
  activeModel,
  onSelectModel,
  sidebarCollapsed,
  onToggleSidebar,
  activeMode = "reviewer",
  onSelectMode,
  activeVault,
}) {
  const [models, setModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);
  const [diagnosticsTab, setDiagnosticsTab] = useState("airgap");

  const openDiagnostics = (tab = "airgap") => {
    setDiagnosticsTab(tab);
    setDiagnosticsOpen(true);
  };

  const fetchModels = async () => {
    setLoadingModels(true);
    try {
      const res = await api.getModels();
      setModels(res.models || []);
    } catch (err) {
      console.error("Failed to fetch models", err);
    } finally {
      setLoadingModels(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleModelChange = async (e) => {
    const model = e.target.value;
    if (model) {
      await onSelectModel(model);
    }
  };

  const getHardwareCompactLabel = () => {
    if (!hardware) return "Local System";
    const acc = hardware.accelerator || {};
    if (acc.device === "cuda") {
      const name = acc.device_name || "GPU";
      const short = name
        .replace("NVIDIA GeForce ", "")
        .replace(" Laptop GPU", "")
        .replace(" GPU", "")
        .trim();
      return short || "CUDA";
    }
    if (acc.device === "metal") {
      return "Metal";
    }
    const cores = hardware.cpu?.physical_cores;
    return cores ? `${cores} Cores` : "CPU";
  };

  return (
    <header className="top-header">
      <div className="brand-section" style={{ display: "flex", alignItems: "center", gap: "0.65rem" }}>
        <button
          className="btn-icon"
          onClick={onToggleSidebar}
          title={sidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>

        {/* SovereignDoc Brand & AirGap Axis Badge */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          {/* SovereignDoc Document Shield Logo */}
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M16 3L5 7V14C5 21.5 10.2 27.8 16 30C21.8 27.8 27 21.5 27 14V7L16 3Z"
              fill="#0F172A"
              stroke="#10B981"
              strokeWidth="2"
              strokeLinejoin="round"
            />
            <path d="M11 10H18L21 13V22H11V10Z" fill="#06B6D4" opacity="0.85" />
            <path d="M18 10V13H21" fill="#10B981" />
            <line x1="13" y1="17" x2="19" y2="17" stroke="#0F172A" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="13" y1="19.5" x2="17" y2="19.5" stroke="#0F172A" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <span style={{ fontWeight: 700, fontSize: "1rem", letterSpacing: "-0.01em", color: "#F1F5F9" }}>
            SovereignDoc
          </span>
          <span
            style={{
              fontSize: "0.68rem",
              padding: "0.1rem 0.4rem",
              borderRadius: "4px",
              backgroundColor: "rgba(6, 78, 59, 0.75)",
              color: "#34D399",
              border: "1px solid rgba(16, 185, 129, 0.35)",
              fontFamily: "monospace",
              fontWeight: 600,
            }}
          >
            v1.1.0
          </span>
        </div>

        <div style={{ height: "16px", width: "1px", backgroundColor: "#1E293B", margin: "0 0.15rem" }} />

        {/* AirGap Axis Platform Brand Tag */}
        <div
          title="AirGap Axis Zero-Trust Platform Architecture"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.38rem",
            fontSize: "0.75rem",
            color: "#94A3B8",
            userSelect: "none",
          }}
        >
          <svg width="14" height="14" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="13" stroke="#10B981" strokeWidth="2.5" strokeDasharray="18 4" />
            <circle cx="16" cy="16" r="4" fill="#06B6D4" />
            <line x1="16" y1="4" x2="16" y2="8" stroke="#10B981" strokeWidth="2" strokeLinecap="round" />
            <line x1="16" y1="24" x2="16" y2="28" stroke="#10B981" strokeWidth="2" strokeLinecap="round" />
            <line x1="4" y1="16" x2="8" y2="16" stroke="#10B981" strokeWidth="2" strokeLinecap="round" />
            <line x1="24" y1="16" x2="28" y2="16" stroke="#10B981" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <span style={{ fontWeight: 500, color: "#94A3B8" }}>AirGap Axis</span>
        </div>
      </div>

      {/* Mode Switcher Tabs */}
      <nav className="mode-nav">
        <button
          className={`mode-tab-btn ${activeMode === "reviewer" ? "active" : ""}`}
          onClick={() => onSelectMode && onSelectMode("reviewer")}
        >
          <span>📄</span> Reviewer
        </button>
        <button
          className={`mode-tab-btn ${activeMode === "audit" ? "active" : ""}`}
          onClick={() => onSelectMode && onSelectMode("audit")}
        >
          <span>⚠️</span> Risk & Obligations
        </button>
        <button
          className={`mode-tab-btn ${activeMode === "redline" ? "active" : ""}`}
          onClick={() => onSelectMode && onSelectMode("redline")}
        >
          <span>⚖️</span> Redline Diff
        </button>
        <button
          className={`mode-tab-btn ${activeMode === "second_brain" ? "active" : ""}`}
          onClick={() => onSelectMode && onSelectMode("second_brain")}
        >
          <span>🧠</span> Second Brain
        </button>
      </nav>

      {/* Right Action Controls: Unified System Status & Model Selector */}
      <div className="header-badges" style={{ display: "flex", alignItems: "center", gap: "0.55rem" }}>
        {/* Unified System Diagnostics Status Pill */}
        <button
          className="badge badge-sovereign"
          title="System Diagnostics: 100% Local Air-Gap Verification & Hardware Profiler"
          onClick={() => openDiagnostics("airgap")}
          style={{
            cursor: "pointer",
            border: "1px solid rgba(16, 185, 129, 0.35)",
            display: "flex",
            alignItems: "center",
            gap: "0.45rem",
            padding: "0.28rem 0.65rem",
          }}
        >
          <span>🔒</span>
          <span style={{ fontWeight: 600 }}>Air-Gapped</span>
          <span style={{ color: "rgba(255, 255, 255, 0.2)", fontSize: "0.7rem" }}>•</span>
          <span style={{ color: "#38BDF8", fontWeight: 500 }}>⚡ {getHardwareCompactLabel()}</span>
        </button>

        {/* Dynamic Model Selector */}
        <div className="model-selector-wrapper">
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Model:</span>
          <select
            className="model-select"
            value={activeModel || ""}
            onChange={handleModelChange}
            disabled={models.length === 0}
          >
            {models.length === 0 ? (
              <option value="">No local models (pull via Ollama)</option>
            ) : (
              models.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name} ({m.size_gb} GB)
                </option>
              ))
            )}
          </select>
          <button
            className="btn-icon"
            onClick={fetchModels}
            title="Refresh local models"
            style={{ animation: loadingModels ? "spin 1s linear infinite" : "none" }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M23 4v6h-6"></path>
              <path d="M1 20v-6h6"></path>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
          </button>
        </div>
      </div>

      <SystemDiagnosticsModal
        isOpen={diagnosticsOpen}
        onClose={() => setDiagnosticsOpen(false)}
        initialTab={diagnosticsTab}
        hardware={hardware}
        activeVault={activeVault}
      />
    </header>
  );
}
