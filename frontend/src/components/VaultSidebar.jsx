// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState, useRef } from "react";
import { api } from "../services/api";


function getDocumentTypeIcon(filename = "", isSelected = false) {
  const ext = (filename || "").split(".").pop().toLowerCase();

  // Word / DOCX: Blue document with distinct 'W' monogram
  if (ext === "docx" || ext === "doc") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" fill="rgba(59, 130, 246, 0.15)" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M14 2v6h6" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M7.5 12.5l1.5 5 1.5-4 1.5 4 1.5-5" stroke="#60A5FA" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }

  // PDF: Red document with folded corner and document lines
  if (ext === "pdf") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" fill="rgba(239, 68, 68, 0.15)" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M14 2v6h6" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <line x1="8" y1="13" x2="16" y2="13" stroke="#F87171" strokeWidth="1.8" strokeLinecap="round" />
        <line x1="8" y1="16.5" x2="13" y2="16.5" stroke="#F87171" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    );
  }

  // Spreadsheet / CSV / Excel: Emerald table grid
  if (ext === "csv" || ext === "xlsx" || ext === "xls") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" fill="rgba(16, 185, 129, 0.15)" stroke="#10B981" strokeWidth="2" />
        <line x1="3" y1="9" x2="21" y2="9" stroke="#10B981" strokeWidth="1.6" />
        <line x1="3" y1="15" x2="21" y2="15" stroke="#10B981" strokeWidth="1.6" />
        <line x1="9" y1="3" x2="9" y2="21" stroke="#10B981" strokeWidth="1.6" />
        <line x1="15" y1="3" x2="15" y2="21" stroke="#10B981" strokeWidth="1.6" />
      </svg>
    );
  }

  // Markdown / Text: Purple text document
  if (ext === "md" || ext === "markdown" || ext === "txt") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" fill="rgba(168, 85, 247, 0.15)" stroke="#A855F7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M14 2v6h6" stroke="#A855F7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <line x1="8" y1="13" x2="16" y2="13" stroke="#C084FC" strokeWidth="1.8" strokeLinecap="round" />
        <line x1="8" y1="16.5" x2="13" y2="16.5" stroke="#C084FC" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    );
  }

  // Generic document fallback
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" fill="rgba(6, 182, 212, 0.15)" stroke="#06B6D4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 2v6h6" stroke="#06B6D4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function VaultSidebar({
  vaults,
  activeVault,
  onSelectVault,
  onCreateVaultClick,
  documents,
  activeDocument,
  onSelectDocument,
  onDocumentUploaded,
  onDocumentDeleted,
  sessions,
  activeSession,
  onSelectSession,
  onCreateSession,
  onSessionDeleted,
  collapsed,
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const fileInputRef = useRef(null);
  const [sessionFilterMode, setSessionFilterMode] = useState("document"); // "document" | "vault"

  const docSessions = activeDocument
    ? sessions.filter((s) => s.document_id === activeDocument.id)
    : [];

  const displayedSessions =
    sessionFilterMode === "document" && activeDocument
      ? docSessions
      : sessions;

  if (collapsed) {
    return (
      <aside className="sidebar-pane" style={{ alignItems: "center", padding: "1rem 0" }}>
        <button
          className="btn-icon"
          title="Active Vault Documents"
          onClick={() => {}}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
          </svg>
        </button>
      </aside>
    );
  }

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await processUpload(files[0]);
    }
  };

  const handleFileInputChange = async (e) => {
    if (e.target.files.length > 0) {
      await processUpload(e.target.files[0]);
      e.target.value = "";
    }
  };

  const processUpload = async (file) => {
    if (!activeVault) {
      alert("Please select or create a vault first.");
      return;
    }
    setUploading(true);
    setUploadStatus(`Indexing ${file.name}...`);
    try {
      const res = await api.uploadDocument(activeVault.id, file);
      if (res.error_message) {
        setUploadStatus(res.error_message);
      } else {
        setUploadStatus(`Ready! (${res.processing_time_ms} ms)`);
      }
      await onDocumentUploaded();
    } catch (err) {
      setUploadStatus("Upload failed.");
      console.error(err);
    } finally {
      setTimeout(() => {
        setUploading(false);
        setUploadStatus("");
      }, 3000);
    }
  };

  const handleDeleteDoc = async (e, docId) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to remove this document from the vault?")) return;
    try {
      await api.deleteDocument(activeVault.id, docId);
      await onDocumentDeleted(docId);
    } catch (err) {
      console.error("Failed to delete document", err);
    }
  };

  const handleDeleteSession = async (e, sessId) => {
    e.stopPropagation();
    if (!confirm("Delete this analysis session?")) return;
    try {
      if (api.deleteSession) {
        await api.deleteSession(activeVault.id, sessId);
      }
      if (onSessionDeleted) {
        onSessionDeleted(sessId);
      }
    } catch (err) {
      console.error("Failed to delete session", err);
    }
  };

  return (
    <aside className="sidebar-pane">
      {/* Vault Header & Selector */}
      <div className="sidebar-header">
        <div style={{ flex: 1, marginRight: "0.5rem" }}>
          <select
            className="vault-select-box"
            value={activeVault?.id || ""}
            onChange={(e) => {
              const selected = vaults.find((v) => v.id === e.target.value);
              if (selected) onSelectVault(selected);
            }}
          >
            {vaults.map((v) => (
              <option key={v.id} value={v.id}>
                📁 {v.name}
              </option>
            ))}
          </select>
        </div>
        <button
          className="btn-icon"
          onClick={onCreateVaultClick}
          title="Create New Vault"
          style={{ background: "rgba(255,255,255,0.06)" }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </button>
      </div>

      <div className="sidebar-content">
        {/* Document Dropzone */}
        <div
          className={`dropzone ${isDragging ? "drag-active" : ""}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: "none" }}
            accept=".pdf,.docx,.txt,.md,.csv"
            onChange={handleFileInputChange}
          />
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--emerald-primary)" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          <p><strong>Click or Drag</strong> PDF, DOCX, CSV</p>
          {uploading && (
            <div style={{ fontSize: "0.72rem", color: "var(--emerald-primary)", marginTop: "0.3rem" }}>
              {uploadStatus}
            </div>
          )}
        </div>

        {/* Documents Section */}
        <div>
          <div style={{ fontSize: "0.74rem", fontWeight: 700, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem", display: "flex", alignItems: "center", gap: "6px" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
            Vault Documents ({documents.length})
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {documents.length === 0 ? (
              <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontStyle: "italic", textAlign: "center", padding: "1rem" }}>
                No documents in vault.
              </div>
            ) : (
              documents.map((doc) => {
                const isSelected = activeDocument?.id === doc.id;
                return (
                  <div
                    key={doc.id}
                    className={`doc-card ${isSelected ? "active" : ""}`}
                    onClick={() => onSelectDocument(doc)}
                  >
                    <div className="doc-title-row">
                      <span style={{ display: "flex", alignItems: "center", gap: "8px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontWeight: 600, color: isSelected ? "#10B981" : "#F8FAFC" }}>
                        {getDocumentTypeIcon(doc.filename, isSelected)}
                        {doc.filename}
                      </span>
                      <button
                        className="btn-icon"
                        onClick={(e) => handleDeleteDoc(e, doc.id)}
                        title="Delete Document"
                        style={{ padding: "0.15rem" }}
                      >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2">
                          <polyline points="3 6 5 6 21 6"></polyline>
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                      </button>
                    </div>
                    <div className="doc-meta-row">
                      <span className={`doc-type-pill doc-type-${(doc.file_type || doc.filename.split('.').pop()).replace('.', '').toLowerCase()}`}>
                        {(doc.file_type || doc.filename.split('.').pop()).replace('.', '').toUpperCase()}
                      </span>
                      <span>&bull;</span>
                      <span>{doc.page_count} {doc.page_count === 1 ? "page" : "pages"}</span>
                      <span>&bull;</span>
                      <span>{doc.chunk_count} chunks</span>
                      <span>&bull;</span>
                      <span className="sha256-chip" title={`SHA-256: ${doc.checksum_sha256}`}>
                        {doc.checksum_sha256.substring(0, 7)}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Chat Sessions History (Scoped & High-Contrast) */}
        <div className="sidebar-sessions-section">
          <div className="sessions-header">
            <div className="sessions-filter-pills">
              <button
                className={`session-filter-pill ${sessionFilterMode === "document" ? "active" : ""}`}
                onClick={() => setSessionFilterMode("document")}
                title="Show sessions for the active contract"
              >
                <span style={{ display: "inline-flex", alignItems: "center", gap: "5px" }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                  </svg>
                  This Doc ({docSessions.length})
                </span>
              </button>
              <button
                className={`session-filter-pill ${sessionFilterMode === "vault" ? "active" : ""}`}
                onClick={() => setSessionFilterMode("vault")}
                title="Show all sessions across vault"
              >
                <span style={{ display: "inline-flex", alignItems: "center", gap: "5px" }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="2" y1="12" x2="22" y2="12"></line>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                  </svg>
                  All ({sessions.length})
                </span>
              </button>
            </div>
            <button
              className="btn-icon"
              onClick={() => onCreateSession(activeDocument?.id)}
              title="New Analysis Session"
              style={{ background: "rgba(16, 185, 129, 0.15)", color: "#10B981", padding: "0.25rem" }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </button>
          </div>

          <div className="sessions-list-container">
            {displayedSessions.length === 0 ? (
              <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontStyle: "italic", textAlign: "center", padding: "0.75rem" }}>
                {sessionFilterMode === "document" && activeDocument
                  ? "No sessions for this contract. Click + to start an analysis."
                  : "No active sessions."}
              </div>
            ) : (
              displayedSessions.map((s) => {
                const isSelected = activeSession?.id === s.id;
                return (
                  <div
                    key={s.id}
                    className={`session-item-card ${isSelected ? "active" : ""}`}
                    onClick={() => onSelectSession(s)}
                    title={s.title}
                  >
                    <div className="session-card-header">
                      <div className="session-card-title">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={isSelected ? "#10B981" : "#94A3B8"} strokeWidth="2" style={{ flexShrink: 0 }}>
                          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                        <span>{s.title}</span>
                      </div>
                      <button
                        className="btn-icon"
                        onClick={(e) => handleDeleteSession(e, s.id)}
                        title="Delete Session"
                        style={{ padding: "0.15rem", opacity: 0.7 }}
                      >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2">
                          <line x1="18" y1="6" x2="6" y2="18"></line>
                          <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                      </button>
                    </div>

                    <div className="session-card-meta">
                      {sessionFilterMode === "vault" && (
                        <span className={`session-doc-badge ${s.document_id ? "" : "vault-wide"}`}>
                          {s.document_filename
                            ? (s.document_filename.length > 18 ? s.document_filename.slice(0, 16) + "..." : s.document_filename)
                            : "Vault-Wide"}
                        </span>
                      )}
                      <span className="session-msg-badge">
                        {s.message_count !== undefined ? `${s.message_count} msgs` : "Active"}
                      </span>
                      <span>
                        {s.created_at ? new Date(s.created_at).toLocaleDateString([], { month: "short", day: "numeric" }) : ""}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
