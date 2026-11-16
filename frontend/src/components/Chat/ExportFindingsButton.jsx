// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React from "react";

export default function ExportFindingsButton({
  query,
  response,
  evidenceList,
  activeDocument,
  activeVault,
  activeModel,
}) {
  const handleExport = () => {
    const timestamp = new Date().toISOString().replace("T", " ").substring(0, 19);
    const docName = activeDocument?.filename || "Vault Documents";
    const sha = activeDocument?.checksum_sha256 || "N/A";
    const vaultName = activeVault?.name || "Default Vault";
    const model = activeModel || "Local LLM";

    let md = `# SovereignDoc Analysis Brief\n\n`;
    md += `**Generated**: ${timestamp} (Local Air-Gapped Session)\n`;
    md += `**Vault**: ${vaultName}\n`;
    md += `**Document**: ${docName} (SHA-256: \`${sha}\`)\n`;
    md += `**Inference Model**: ${model}\n\n`;
    md += `---\n\n`;
    md += `## 1. Inquiry\n> ${query}\n\n`;
    md += `## 2. Executive Analysis & Findings\n${response}\n\n`;
    md += `---\n\n`;
    md += `## 3. Verified Grounded Evidence Trail\n\n`;

    if (evidenceList && evidenceList.length > 0) {
      md += `| # | Section / Title | Page | Confidence | Verbatim Source Excerpt |\n`;
      md += `| :--- | :--- | :--- | :--- | :--- |\n`;
      evidenceList.forEach((ev, idx) => {
        const title = ev.clause_title || (ev.section ? `Section ${ev.section}` : `Page ${ev.page_number}`);
        const conf = `${Math.round((ev.confidence || 0.85) * 100)}%`;
        const excerpt = (ev.evidence_text || "").replace(/\|/g, "\\|").replace(/\n/g, " ");
        md += `| ${idx + 1} | ${title} | Page ${ev.page_number} | ${conf} | "${excerpt}" |\n`;
      });
    } else {
      md += `*No external evidence citations recorded for this inquiry.*\n`;
    }

    md += `\n---\n*SovereignDoc: Zero Cloud Calls • Zero Telemetry • 100% Local Inference*\n`;

    // Trigger local client-side download
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const safeDoc = (activeDocument?.filename || "analysis").replace(/[^a-zA-Z0-9_-]/g, "_");
    link.href = url;
    link.download = `SovereignDoc_${safeDoc}_Findings.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <button
      onClick={handleExport}
      className="btn-icon"
      style={{
        fontSize: "0.74rem",
        display: "inline-flex",
        alignItems: "center",
        gap: "0.35rem",
        background: "rgba(255,255,255,0.06)",
        padding: "0.25rem 0.55rem",
        borderRadius: "4px",
        color: "var(--text-secondary)",
      }}
      title="Export findings to Markdown"
    >
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      Export Findings
    </button>
  );
}