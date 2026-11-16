// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState, useEffect } from "react";
import { api } from "../../services/api";

/**
 * Lightweight, 100% local Markdown + [[WikiLink]] + #tag renderer
 */
function renderMarkdownWithWikiLinks(
  md = "",
  { onWikiLinkClick, onTagClick }
) {
  if (!md) {
    return (
      <div style={{ color: "var(--text-muted)", fontStyle: "italic" }}>
        Empty note. Switch to Edit or Split mode to write Markdown and [[WikiLinks]].
      </div>
    );
  }

  const lines = md.split("\n");
  const elements = [];

  const renderInline = (text, keyPrefix) => {
    // Tokenize [[WikiLinks]], **bold**, `code`, and #tags
    const tokenRegex = /(\[\[[^\[\]\n]+\]\]|\*\*[^*\n]+\*\*|`[^`\n]+`|(?:\s|^)#[a-zA-Z][a-zA-Z0-9_-]{1,35}\b)/g;
    const parts = text.split(tokenRegex);

    return parts.map((part, idx) => {
      if (!part) return null;
      const key = `${keyPrefix}_${idx}`;

      if (part.startsWith("[[") && part.endsWith("]]")) {
        const inner = part.slice(2, -2).trim();
        const isDoc = /^(?:Doc|Document)\s*:/i.test(inner);
        const isRisk = /^Risk\s*:/i.test(inner);
        const isObl = /^Obligation\s*:/i.test(inner);

        let badgeColor = "#06B6D4";
        let badgeBg = "rgba(6, 182, 212, 0.14)";
        let icon = "📝";
        if (isDoc) {
          badgeColor = "#10B981";
          badgeBg = "rgba(16, 185, 129, 0.15)";
          icon = "📄";
        } else if (isRisk) {
          badgeColor = "#EF4444";
          badgeBg = "rgba(239, 68, 68, 0.15)";
          icon = "⚠️";
        } else if (isObl) {
          badgeColor = "#14B8A6";
          badgeBg = "rgba(20, 184, 166, 0.15)";
          icon = "📋";
        }

        const displayLabel = inner.includes("|") ? inner.split("|")[1].trim() : inner;

        return (
          <button
            key={key}
            type="button"
            onClick={() => onWikiLinkClick && onWikiLinkClick(inner)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              background: badgeBg,
              color: badgeColor,
              border: `1px solid ${badgeColor}44`,
              borderRadius: "5px",
              padding: "1px 7px",
              margin: "0 2px",
              fontSize: "0.8rem",
              fontWeight: 600,
              cursor: "pointer",
              fontFamily: "var(--font-sans)",
            }}
            title={`Click to navigate: ${inner}`}
          >
            <span>{icon}</span>
            <span>{displayLabel}</span>
          </button>
        );
      }

      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={key} style={{ color: "#F8FAFC" }}>{part.slice(2, -2)}</strong>;
      }

      if (part.startsWith("`") && part.endsWith("`")) {
        return (
          <code
            key={key}
            style={{
              background: "rgba(255,255,255,0.08)",
              padding: "1px 5px",
              borderRadius: "4px",
              fontFamily: "var(--font-mono)",
              fontSize: "0.8em",
              color: "#E2E8F0",
            }}
          >
            {part.slice(1, -1)}
          </code>
        );
      }

      if (/^\s*#[a-zA-Z]/.test(part)) {
        const leadingSpace = part.startsWith(" ") ? " " : "";
        const tagText = part.trim();
        return (
          <React.Fragment key={key}>
            {leadingSpace}
            <span
              onClick={() => onTagClick && onTagClick(tagText.slice(1))}
              style={{
                display: "inline-block",
                background: "rgba(168, 85, 247, 0.16)",
                color: "#C084FC",
                border: "1px solid rgba(168, 85, 247, 0.35)",
                borderRadius: "999px",
                padding: "0px 8px",
                fontSize: "0.75rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {tagText}
            </span>
          </React.Fragment>
        );
      }

      return <span key={key}>{part}</span>;
    });
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) {
      elements.push(<div key={idx} style={{ height: "0.55rem" }} />);
    } else if (trimmed === "---") {
      elements.push(
        <hr
          key={idx}
          style={{
            border: "none",
            borderTop: "1px solid rgba(255,255,255,0.1)",
            margin: "0.85rem 0",
          }}
        />
      );
    } else if (trimmed.startsWith("### ")) {
      elements.push(
        <h3
          key={idx}
          style={{
            fontSize: "0.96rem",
            fontWeight: 700,
            color: "#F8FAFC",
            margin: "0.75rem 0 0.35rem",
          }}
        >
          {renderInline(trimmed.slice(4), `h3_${idx}`)}
        </h3>
      );
    } else if (trimmed.startsWith("## ")) {
      elements.push(
        <h2
          key={idx}
          style={{
            fontSize: "1.1rem",
            fontWeight: 700,
            color: "#10B981",
            margin: "0.9rem 0 0.4rem",
          }}
        >
          {renderInline(trimmed.slice(3), `h2_${idx}`)}
        </h2>
      );
    } else if (trimmed.startsWith("# ")) {
      elements.push(
        <h1
          key={idx}
          style={{
            fontSize: "1.25rem",
            fontWeight: 800,
            color: "#F8FAFC",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
            paddingBottom: "0.35rem",
            margin: "0.5rem 0 0.65rem",
          }}
        >
          {renderInline(trimmed.slice(2), `h1_${idx}`)}
        </h1>
      );
    } else if (trimmed.startsWith("> ")) {
      elements.push(
        <blockquote
          key={idx}
          style={{
            borderLeft: "3px solid #10B981",
            background: "rgba(16, 185, 129, 0.06)",
            padding: "0.55rem 0.85rem",
            margin: "0.45rem 0",
            borderRadius: "0 6px 6px 0",
            color: "#E2E8F0",
            fontSize: "0.85rem",
            lineHeight: 1.55,
          }}
        >
          {renderInline(trimmed.slice(2), `bq_${idx}`)}
        </blockquote>
      );
    } else if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      elements.push(
        <div
          key={idx}
          style={{
            display: "flex",
            gap: "0.5rem",
            paddingLeft: "0.5rem",
            margin: "0.2rem 0",
            fontSize: "0.86rem",
            lineHeight: 1.55,
            color: "#CBD5E1",
          }}
        >
          <span style={{ color: "#10B981" }}>&bull;</span>
          <div style={{ flex: 1 }}>{renderInline(trimmed.slice(2), `li_${idx}`)}</div>
        </div>
      );
    } else {
      elements.push(
        <p
          key={idx}
          style={{
            margin: "0.25rem 0",
            fontSize: "0.86rem",
            lineHeight: 1.6,
            color: "#CBD5E1",
          }}
        >
          {renderInline(line, `p_${idx}`)}
        </p>
      );
    }
  });

  return <div>{elements}</div>;
}

export default function NoteEditor({
  vaultId,
  note,
  documents = [],
  allNotes = [],
  onNoteSaved,
  onSelectNoteById,
  onCreateLinkedNote,
  onOpenDocumentCitation,
  onFilterByTag,
}) {
  const [title, setTitle] = useState("");
  const [contentMd, setContentMd] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [pageNumber, setPageNumber] = useState("");
  const [pinned, setPinned] = useState(false);
  const [editorMode, setEditorMode] = useState("split"); // "edit" | "split" | "preview"
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");

  // Version History Drawer State
  const [showHistory, setShowHistory] = useState(false);
  const [versions, setVersions] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [loadingVersions, setLoadingVersions] = useState(false);

  useEffect(() => {
    if (note) {
      setTitle(note.title || "");
      setContentMd(note.content_md || "");
      setDocumentId(note.document_id || "");
      setPageNumber(note.page_number || "");
      setPinned(Boolean(note.pinned));
      setShowHistory(false);
      setSelectedVersion(null);
    }
  }, [note?.id, note?.current_version]);

  const handleSave = async () => {
    if (!vaultId || !note) return;
    setSaving(true);
    setSaveMessage("");
    try {
      const updated = await api.updateNote(vaultId, note.id, {
        title: title.trim() || "Untitled Note",
        content_md: contentMd,
        document_id: documentId || "",
        page_number: pageNumber ? parseInt(pageNumber, 10) : null,
        pinned,
      });
      setSaveMessage(`Saved v${updated.current_version}`);
      if (onNoteSaved) onNoteSaved(updated);
      setTimeout(() => setSaveMessage(""), 2500);
    } catch (err) {
      console.error("Failed to save note:", err);
      setSaveMessage("Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleOpenHistory = async () => {
    if (!vaultId || !note) return;
    const nextState = !showHistory;
    setShowHistory(nextState);
    if (nextState) {
      setLoadingVersions(true);
      try {
        const vList = await api.listNoteVersions(vaultId, note.id);
        setVersions(vList || []);
        if (vList && vList.length > 0) {
          setSelectedVersion(vList[0]);
        }
      } catch (err) {
        console.error("Failed to load note versions:", err);
      } finally {
        setLoadingVersions(false);
      }
    }
  };

  const handleRestoreVersion = async (ver) => {
    if (!vaultId || !note || !ver) return;
    try {
      const restored = await api.restoreNoteVersion(vaultId, note.id, ver.id);
      setShowHistory(false);
      setSaveMessage(`Restored v${ver.version_number} -> v${restored.current_version}`);
      if (onNoteSaved) onNoteSaved(restored);
      setTimeout(() => setSaveMessage(""), 3000);
    } catch (err) {
      console.error("Failed to restore version:", err);
    }
  };

  const insertSnippet = (snippet) => {
    setContentMd((prev) => `${prev}${prev.endsWith("\n") || !prev ? "" : "\n"}${snippet}`);
  };

  const handleWikiLinkClick = (innerText) => {
    const targetPart = innerText.split("|")[0].trim();
    const docMatch = targetPart.match(/^(?:Doc|Document)\s*:\s*([^#]+?)(?:#(?:Page|p\.?)\s*(\d+))?$/i);
    if (docMatch) {
      const fname = docMatch[1].trim();
      const page = docMatch[2] ? parseInt(docMatch[2], 10) : 1;
      const doc = documents.find(
        (d) =>
          d.filename.toLowerCase() === fname.toLowerCase() ||
          d.filename.toLowerCase().includes(fname.toLowerCase())
      );
      if (onOpenDocumentCitation) {
        onOpenDocumentCitation({
          document_id: doc?.id,
          filename: doc?.filename || fname,
          page_number: page,
          clause_title: `${fname} (Page ${page})`,
        });
      }
      return;
    }

    // Check if Note exists by title
    const existingNote = allNotes.find(
      (n) => n.title.toLowerCase() === targetPart.toLowerCase()
    );
    if (existingNote) {
      onSelectNoteById && onSelectNoteById(existingNote.id);
    } else if (onCreateLinkedNote) {
      onCreateLinkedNote(targetPart);
    }
  };

  if (!note) {
    return (
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--text-muted)",
          padding: "2rem",
          textAlign: "center",
        }}
      >
        <div>
          <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>🧠</div>
          <div style={{ fontWeight: 600, color: "var(--text-secondary)" }}>
            Select a Note or Create a New Research Note
          </div>
          <div style={{ fontSize: "0.8rem", marginTop: "0.35rem", maxWidth: "360px" }}>
            Use <code>[[Note Title]]</code>, <code>[[Doc:Filename#Page 6]]</code>, and <code>#tags</code> to build your grounded legal knowledge graph.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        overflow: "hidden",
        background: "var(--bg-primary)",
      }}
    >
      {/* Top Note Editor Toolbar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "0.6rem",
          padding: "0.65rem 1rem",
          borderBottom: "1px solid var(--border-subtle)",
          background: "var(--bg-secondary)",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flex: 1, minWidth: "220px" }}>
          <button
            type="button"
            className="btn-icon"
            onClick={() => setPinned((p) => !p)}
            title={pinned ? "Unpin Note" : "Pin Note"}
            style={{
              color: pinned ? "#F59E0B" : "var(--text-muted)",
              background: pinned ? "rgba(245, 158, 11, 0.14)" : "transparent",
            }}
          >
            📌
          </button>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Note Title..."
            style={{
              flex: 1,
              background: "rgba(15, 23, 42, 0.7)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "6px",
              padding: "0.38rem 0.65rem",
              color: "#F8FAFC",
              fontSize: "0.92rem",
              fontWeight: 700,
            }}
          />
          <span
            className="badge"
            style={{
              background: "rgba(6, 182, 212, 0.14)",
              color: "#06B6D4",
              border: "1px solid rgba(6, 182, 212, 0.3)",
              fontSize: "0.7rem",
            }}
          >
            v{note.current_version || 1}
          </span>
        </div>

        {/* Mode Switcher + History + Save */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.45rem", flexWrap: "wrap" }}>
          <div
            style={{
              display: "inline-flex",
              background: "rgba(15, 23, 42, 0.8)",
              borderRadius: "6px",
              padding: "2px",
              border: "1px solid var(--border-subtle)",
            }}
          >
            {["edit", "split", "preview"].map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setEditorMode(m)}
                style={{
                  background: editorMode === m ? "rgba(16, 185, 129, 0.2)" : "transparent",
                  color: editorMode === m ? "#10B981" : "#94A3B8",
                  border: "none",
                  borderRadius: "4px",
                  padding: "0.24rem 0.55rem",
                  fontSize: "0.73rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  textTransform: "capitalize",
                }}
              >
                {m}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={handleOpenHistory}
            style={{
              background: showHistory ? "rgba(59, 130, 246, 0.2)" : "rgba(255,255,255,0.06)",
              color: showHistory ? "#60A5FA" : "#CBD5E1",
              border: "1px solid rgba(255,255,255,0.12)",
              borderRadius: "6px",
              padding: "0.32rem 0.65rem",
              fontSize: "0.75rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
            title="Inspect and restore prior NoteVersion snapshots"
          >
            🕒 History (v{note.current_version || 1})
          </button>

          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            style={{
              background: "#10B981",
              color: "#06281E",
              border: "none",
              borderRadius: "6px",
              padding: "0.35rem 0.8rem",
              fontSize: "0.76rem",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            {saving ? "Saving..." : "💾 Save"}
          </button>
          {saveMessage && (
            <span style={{ fontSize: "0.74rem", color: "#10B981", fontWeight: 600 }}>
              {saveMessage}
            </span>
          )}
        </div>
      </div>

      {/* Document Anchor & Quick-Insert Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "0.5rem",
          padding: "0.4rem 1rem",
          borderBottom: "1px solid var(--border-subtle)",
          background: "rgba(15, 23, 42, 0.55)",
          fontSize: "0.75rem",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.45rem", flexWrap: "wrap" }}>
          <span style={{ color: "var(--text-muted)" }}>Contract Anchor:</span>
          <select
            value={documentId}
            onChange={(e) => setDocumentId(e.target.value)}
            style={{
              background: "var(--bg-secondary)",
              color: "#E2E8F0",
              border: "1px solid var(--border-subtle)",
              borderRadius: "5px",
              padding: "0.2rem 0.45rem",
              fontSize: "0.74rem",
            }}
          >
            <option value="">🌐 Vault-Wide Note</option>
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                📄 {d.filename}
              </option>
            ))}
          </select>
          {documentId && (
            <input
              type="number"
              min="1"
              value={pageNumber}
              onChange={(e) => setPageNumber(e.target.value)}
              placeholder="Page #"
              style={{
                width: "68px",
                background: "var(--bg-secondary)",
                color: "#E2E8F0",
                border: "1px solid var(--border-subtle)",
                borderRadius: "5px",
                padding: "0.2rem 0.4rem",
                fontSize: "0.74rem",
              }}
            />
          )}
          {documentId && (
            <button
              type="button"
              onClick={() => {
                const doc = documents.find((d) => d.id === documentId);
                if (doc && onOpenDocumentCitation) {
                  onOpenDocumentCitation({
                    document_id: doc.id,
                    filename: doc.filename,
                    page_number: pageNumber ? parseInt(pageNumber, 10) : 1,
                  });
                }
              }}
              style={{
                background: "rgba(16, 185, 129, 0.14)",
                color: "#10B981",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                borderRadius: "5px",
                padding: "0.18rem 0.5rem",
                fontSize: "0.72rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              ↗ Open Contract
            </button>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
          <button
            type="button"
            onClick={() => insertSnippet("[[Related Note Title]]")}
            style={{
              background: "rgba(6, 182, 212, 0.12)",
              color: "#06B6D4",
              border: "1px solid rgba(6, 182, 212, 0.25)",
              borderRadius: "4px",
              padding: "0.15rem 0.45rem",
              fontSize: "0.71rem",
              cursor: "pointer",
            }}
          >
            + [[Note]]
          </button>
          <button
            type="button"
            onClick={() => {
              const fname = documents[0]?.filename || "Contract.docx";
              insertSnippet(`[[Doc:${fname}#Page 1]]`);
            }}
            style={{
              background: "rgba(16, 185, 129, 0.12)",
              color: "#10B981",
              border: "1px solid rgba(16, 185, 129, 0.25)",
              borderRadius: "4px",
              padding: "0.15rem 0.45rem",
              fontSize: "0.71rem",
              cursor: "pointer",
            }}
          >
            + [[Doc#Page]]
          </button>
          <button
            type="button"
            onClick={() => insertSnippet("#legal-review ")}
            style={{
              background: "rgba(168, 85, 247, 0.12)",
              color: "#C084FC",
              border: "1px solid rgba(168, 85, 247, 0.25)",
              borderRadius: "4px",
              padding: "0.15rem 0.45rem",
              fontSize: "0.71rem",
              cursor: "pointer",
            }}
          >
            + #tag
          </button>
        </div>
      </div>

      {/* Optional Version History Drawer */}
      {showHistory && (
        <div
          style={{
            background: "rgba(15, 23, 42, 0.96)",
            borderBottom: "1px solid rgba(59, 130, 246, 0.35)",
            padding: "0.75rem 1rem",
            maxHeight: "230px",
            overflowY: "auto",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "#60A5FA" }}>
              🕒 Non-Destructive Note Version History ({versions.length} snapshots)
            </span>
            <button
              type="button"
              onClick={() => setShowHistory(false)}
              style={{ background: "none", border: "none", color: "#94A3B8", cursor: "pointer", fontSize: "0.8rem" }}
            >
              ✕ Close
            </button>
          </div>
          {loadingVersions ? (
            <div style={{ fontSize: "0.76rem", color: "var(--text-muted)" }}>Loading versions...</div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: "0.75rem" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                {versions.map((v) => (
                  <div
                    key={v.id}
                    onClick={() => setSelectedVersion(v)}
                    style={{
                      padding: "0.35rem 0.55rem",
                      borderRadius: "6px",
                      cursor: "pointer",
                      background:
                        selectedVersion?.id === v.id
                          ? "rgba(59, 130, 246, 0.2)"
                          : "rgba(255,255,255,0.03)",
                      border:
                        selectedVersion?.id === v.id
                          ? "1px solid rgba(59, 130, 246, 0.45)"
                          : "1px solid transparent",
                      fontSize: "0.74rem",
                    }}
                  >
                    <div style={{ fontWeight: 700, color: "#F8FAFC" }}>
                      v{v.version_number} — {v.summary || v.title}
                    </div>
                    <div style={{ fontSize: "0.68rem", color: "#94A3B8" }}>
                      {new Date(v.created_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
              {selectedVersion && (
                <div
                  style={{
                    background: "rgba(2, 6, 23, 0.7)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "6px",
                    padding: "0.6rem 0.8rem",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.35rem" }}>
                      <span style={{ fontSize: "0.76rem", fontWeight: 700, color: "#E2E8F0" }}>
                        Snapshot v{selectedVersion.version_number}: {selectedVersion.title}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRestoreVersion(selectedVersion)}
                        style={{
                          background: "rgba(59, 130, 246, 0.2)",
                          color: "#60A5FA",
                          border: "1px solid rgba(59, 130, 246, 0.4)",
                          borderRadius: "5px",
                          padding: "0.2rem 0.55rem",
                          fontSize: "0.72rem",
                          fontWeight: 700,
                          cursor: "pointer",
                        }}
                      >
                        ↺ Restore v{selectedVersion.version_number}
                      </button>
                    </div>
                    <pre
                      style={{
                        whiteSpace: "pre-wrap",
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.73rem",
                        color: "#CBD5E1",
                        maxHeight: "95px",
                        overflowY: "auto",
                        margin: 0,
                      }}
                    >
                      {selectedVersion.content_md}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Main Editor / Split / Preview Body */}
      <div
        style={{
          flex: 1,
          display: "grid",
          gridTemplateColumns:
            editorMode === "split" ? "1fr 1fr" : "1fr",
          overflow: "hidden",
        }}
      >
        {(editorMode === "edit" || editorMode === "split") && (
          <textarea
            value={contentMd}
            onChange={(e) => setContentMd(e.target.value)}
            placeholder="Write Markdown notes here... Use [[Note Title]], [[Doc:Filename#Page 6]], and #tags."
            style={{
              width: "100%",
              height: "100%",
              background: "rgba(2, 6, 23, 0.55)",
              color: "#F8FAFC",
              border: "none",
              borderRight: editorMode === "split" ? "1px solid var(--border-subtle)" : "none",
              padding: "1rem",
              fontFamily: "var(--font-mono)",
              fontSize: "0.84rem",
              lineHeight: 1.6,
              resize: "none",
              outline: "none",
            }}
          />
        )}

        {(editorMode === "preview" || editorMode === "split") && (
          <div
            style={{
              height: "100%",
              overflowY: "auto",
              padding: "1rem 1.2rem",
              background: "rgba(15, 23, 42, 0.35)",
            }}
          >
            {renderMarkdownWithWikiLinks(contentMd, {
              onWikiLinkClick: handleWikiLinkClick,
              onTagClick: onFilterByTag,
            })}
          </div>
        )}
      </div>

      {/* Bi-Directional Backlinks & Grounded References Footer */}
      <div
        style={{
          borderTop: "1px solid var(--border-subtle)",
          background: "var(--bg-secondary)",
          padding: "0.55rem 1rem",
          maxHeight: "135px",
          overflowY: "auto",
          fontSize: "0.75rem",
        }}
      >
        <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
          {/* Outgoing Links */}
          <div style={{ flex: 1, minWidth: "220px" }}>
            <div style={{ fontWeight: 700, color: "#94A3B8", marginBottom: "0.3rem", textTransform: "uppercase", fontSize: "0.68rem" }}>
              ↗ Outgoing References ({note.links_out?.length || 0})
            </div>
            <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
              {!note.links_out || note.links_out.length === 0 ? (
                <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>None</span>
              ) : (
                note.links_out.map((lnk) => (
                  <button
                    key={lnk.id}
                    type="button"
                    onClick={() => {
                      if (lnk.target_note_id && onSelectNoteById) {
                        onSelectNoteById(lnk.target_note_id);
                      } else if (lnk.target_doc_id && onOpenDocumentCitation) {
                        onOpenDocumentCitation({
                          document_id: lnk.target_doc_id,
                          filename: lnk.target_doc_filename,
                          page_number: lnk.target_page || 1,
                        });
                      } else {
                        handleWikiLinkClick(lnk.link_text);
                      }
                    }}
                    style={{
                      background: "rgba(255,255,255,0.05)",
                      color: "#E2E8F0",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "5px",
                      padding: "2px 7px",
                      fontSize: "0.72rem",
                      cursor: "pointer",
                    }}
                  >
                    {lnk.link_type === "DOCUMENT" && "📄 "}
                    {lnk.link_type === "RISK" && "⚠️ "}
                    {lnk.link_type === "OBLIGATION" && "📋 "}
                    {lnk.link_type === "NOTE" && "📝 "}
                    {lnk.link_text}
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Incoming Backlinks */}
          <div style={{ flex: 1, minWidth: "220px" }}>
            <div style={{ fontWeight: 700, color: "#06B6D4", marginBottom: "0.3rem", textTransform: "uppercase", fontSize: "0.68rem" }}>
              ↙ Incoming Backlinks ({note.backlinks?.length || 0})
            </div>
            <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
              {!note.backlinks || note.backlinks.length === 0 ? (
                <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>
                  No other notes link here yet
                </span>
              ) : (
                note.backlinks.map((bl) => (
                  <button
                    key={bl.id}
                    type="button"
                    onClick={() => onSelectNoteById && onSelectNoteById(bl.source_note_id)}
                    style={{
                      background: "rgba(6, 182, 212, 0.14)",
                      color: "#06B6D4",
                      border: "1px solid rgba(6, 182, 212, 0.3)",
                      borderRadius: "5px",
                      padding: "2px 8px",
                      fontSize: "0.72rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    📝 {bl.source_note_title || "Linked Note"}
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

