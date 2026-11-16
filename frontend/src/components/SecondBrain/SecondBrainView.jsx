// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState, useEffect } from "react";
import { api } from "../../services/api";
import NoteEditor from "./NoteEditor";
import KnowledgeGraphCanvas from "./KnowledgeGraphCanvas";

export default function SecondBrainView({
  vaultId,
  activeDocument,
  documents = [],
  onOpenDocumentCitation,
}) {
  const [notes, setNotes] = useState([]);
  const [activeNote, setActiveNote] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTag, setSelectedTag] = useState("");
  const [layoutMode, setLayoutMode] = useState("split"); // "editor" | "split" | "graph"
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadNotesAndGraph = async (q = searchQuery, tag = selectedTag) => {
    if (!vaultId) return;
    setLoading(true);
    try {
      const [noteList, graphRes] = await Promise.all([
        api.listNotes(vaultId, { q, tag }),
        api.getVaultGraph(vaultId),
      ]);
      const safeNotes = Array.isArray(noteList) ? noteList : [];
      setNotes(safeNotes);
      setGraphData(graphRes && typeof graphRes === "object" ? graphRes : { nodes: [], edges: [], stats: {} });

      if (activeNote) {
        const refreshed = safeNotes.find((n) => n.id === activeNote.id);
        if (refreshed) setActiveNote(refreshed);
      } else if (safeNotes.length > 0) {
        setActiveNote(safeNotes[0]);
      }
    } catch (err) {
      console.error("Failed to load Second Brain data:", err);
      setNotes([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotesAndGraph("", "");
  }, [vaultId]);

  const handleSearchChange = async (e) => {
    const val = e.target.value;
    setSearchQuery(val);
    await loadNotesAndGraph(val, selectedTag);
  };

  const handleTagFilter = async (tag) => {
    const nextTag = selectedTag === tag ? "" : tag;
    setSelectedTag(nextTag);
    await loadNotesAndGraph(searchQuery, nextTag);
  };

  const handleCreateNote = async (initialTitle = null) => {
    if (!vaultId) return;
    try {
      const defaultTitle =
        typeof initialTitle === "string" && initialTitle.trim()
          ? initialTitle.trim()
          : activeDocument
          ? `Notes — ${activeDocument.filename}`
          : `Research Note ${notes.length + 1}`;

      const docLinkLine = activeDocument
        ? `Linked Contract: [[Doc:${activeDocument.filename}#Page 1]]\n\n`
        : "";

      const created = await api.createNote(vaultId, {
        title: defaultTitle,
        content_md: `# ${defaultTitle}\n\n${docLinkLine}Write key findings, clause citations, and #legal-review notes here.\n`,
        document_id: activeDocument?.id || null,
        page_number: 1,
        pinned: false,
      });

      setNotes((prev) => [created, ...prev]);
      setActiveNote(created);
      const updatedGraph = await api.getVaultGraph(vaultId);
      setGraphData(updatedGraph);
    } catch (err) {
      console.error("Failed to create note:", err);
    }
  };

  const handleDeleteNote = async (e, noteId) => {
    e.stopPropagation();
    if (!confirm("Delete this Second Brain note and its version history?")) return;
    try {
      await api.deleteNote(vaultId, noteId);
      const remaining = notes.filter((n) => n.id !== noteId);
      setNotes(remaining);
      if (activeNote?.id === noteId) {
        setActiveNote(remaining.length > 0 ? remaining[0] : null);
      }
      const updatedGraph = await api.getVaultGraph(vaultId);
      setGraphData(updatedGraph);
    } catch (err) {
      console.error("Failed to delete note:", err);
    }
  };

  const handleNoteSaved = async (updatedNote) => {
    setActiveNote(updatedNote);
    const [noteList, updatedGraph] = await Promise.all([
      api.listNotes(vaultId, { q: searchQuery, tag: selectedTag }),
      api.getVaultGraph(vaultId),
    ]);
    setNotes(noteList || []);
    setGraphData(updatedGraph);
  };

  const handleSelectNoteById = async (noteId) => {
    try {
      const fullNote = await api.getNote(vaultId, noteId);
      setActiveNote(fullNote);
      if (layoutMode === "graph") {
        setLayoutMode("split");
      }
    } catch (err) {
      console.error("Failed to select note:", err);
    }
  };

  const handleSyncGraph = async () => {
    if (!vaultId) return;
    const synced = await api.syncVaultGraph(vaultId);
    setGraphData(synced);
  };

  const handlePinNodeToNote = async (node) => {
    if (!vaultId || !node) return;
    try {
      const meta = node.metadata || {};
      const citation = `\n\n> **${node.label}**\n> "${meta.verbatim_text || meta.action_required || node.label}"\n> — *Page ${meta.page_number || 1}${meta.section ? `, ${meta.section}` : ""}*\n`;

      if (activeNote) {
        const updated = await api.updateNote(vaultId, activeNote.id, {
          title: activeNote.title,
          content_md: (activeNote.content_md || "") + citation,
          tags: activeNote.tags || [],
        });
        await handleNoteSaved(updated);
      } else {
        const created = await api.createNote(vaultId, {
          title: `Findings — ${node.label.slice(0, 40)}`,
          content_md: `# Legal Review Notes\n${citation}`,
          document_id: meta.document_id || null,
          page_number: meta.page_number || 1,
        });
        setNotes((prev) => [created, ...prev]);
        setActiveNote(created);
        const updatedGraph = await api.getVaultGraph(vaultId);
        setGraphData(updatedGraph);
      }
    } catch (err) {
      console.error("Failed to pin node to note:", err);
    }
  };

  // Collect all unique tags across notes
  const allTags = Array.from(
    new Set(notes.flatMap((n) => n.tags || []))
  );

  return (
    <div
      style={{
        gridColumn: "span 2",
        display: "grid",
        gridTemplateColumns: "290px 1fr",
        height: "100%",
        overflow: "hidden",
        background: "var(--bg-primary)",
      }}
    >
      {/* Left Column: Notes Explorer, Local Search & Tag Filter */}
      <div
        style={{
          borderRight: "1px solid var(--border-subtle)",
          background: "var(--bg-secondary)",
          display: "flex",
          flexDirection: "column",
          height: "100%",
          overflow: "hidden",
        }}
      >
        {/* Notes Header */}
        <div
          style={{
            padding: "0.75rem 0.9rem",
            borderBottom: "1px solid var(--border-subtle)",
            display: "flex",
            flexDirection: "column",
            gap: "0.55rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#F8FAFC" }}>
              🧠 Second Brain Notes ({notes.length})
            </span>
            <button
              type="button"
              onClick={() => handleCreateNote()}
              style={{
                background: "#10B981",
                color: "#06281E",
                border: "none",
                borderRadius: "6px",
                padding: "0.28rem 0.6rem",
                fontSize: "0.74rem",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              + New Note
            </button>
          </div>

          <input
            type="text"
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder="Search notes, [[links]], #tags..."
            style={{
              width: "100%",
              background: "rgba(2, 6, 23, 0.7)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "6px",
              padding: "0.35rem 0.6rem",
              color: "#F8FAFC",
              fontSize: "0.76rem",
            }}
          />

          {/* Tag Filter Bar */}
          {allTags.length > 0 && (
            <div style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap" }}>
              {allTags.map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => handleTagFilter(t)}
                  style={{
                    background:
                      selectedTag === t
                        ? "rgba(168, 85, 247, 0.28)"
                        : "rgba(168, 85, 247, 0.1)",
                    color: "#C084FC",
                    border:
                      selectedTag === t
                        ? "1px solid #A855F7"
                        : "1px solid rgba(168, 85, 247, 0.25)",
                    borderRadius: "999px",
                    padding: "1px 7px",
                    fontSize: "0.68rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  #{t}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Notes List */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "0.6rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.45rem",
          }}
        >
          {notes.length === 0 ? (
            <div
              style={{
                fontSize: "0.78rem",
                color: "var(--text-muted)",
                textAlign: "center",
                padding: "1.5rem 0.5rem",
              }}
            >
              {loading
                ? "Loading notes..."
                : "No notes yet. Click '+ New Note' or pin a Risk/Evidence card from a contract review."}
            </div>
          ) : (
            notes.map((n) => {
              const isSelected = activeNote?.id === n.id;
              return (
                <div
                  key={n.id}
                  onClick={() => setActiveNote(n)}
                  style={{
                    padding: "0.6rem 0.7rem",
                    borderRadius: "8px",
                    cursor: "pointer",
                    background: isSelected
                      ? "rgba(6, 182, 212, 0.14)"
                      : "rgba(15, 23, 42, 0.65)",
                    border: isSelected
                      ? "1px solid rgba(6, 182, 212, 0.45)"
                      : "1px solid var(--border-subtle)",
                    transition: "all 0.15s ease",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "0.35rem",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "0.82rem",
                        fontWeight: 700,
                        color: isSelected ? "#38BDF8" : "#F8FAFC",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {n.pinned ? "📌 " : "📝 "}
                      {n.title}
                    </span>
                    <button
                      type="button"
                      onClick={(e) => handleDeleteNote(e, n.id)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "#EF4444",
                        cursor: "pointer",
                        fontSize: "0.75rem",
                        opacity: 0.7,
                      }}
                      title="Delete Note"
                    >
                      ✕
                    </button>
                  </div>

                  {n.document_filename && (
                    <div
                      style={{
                        fontSize: "0.69rem",
                        color: "#10B981",
                        marginTop: "0.25rem",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      📄 {n.document_filename}
                    </div>
                  )}

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.4rem",
                      marginTop: "0.35rem",
                      fontSize: "0.68rem",
                      color: "#94A3B8",
                      flexWrap: "wrap",
                    }}
                  >
                    <span>v{n.current_version || 1}</span>
                    <span>&bull;</span>
                    <span>{n.outgoing_links_count || 0} links</span>
                    <span>&bull;</span>
                    <span>{n.backlinks_count || 0} backlinks</span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Workspace: Layout Mode Bar + NoteEditor / 2D Force Knowledge Graph */}
      <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
        {/* Sub-Header View Switcher */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0.45rem 1rem",
            background: "var(--bg-secondary)",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            {[
              { id: "editor", label: "📝 Note Editor" },
              { id: "split", label: "⚡ Split Editor + Graph" },
              { id: "graph", label: "🕸️ Full Knowledge Graph" },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setLayoutMode(tab.id)}
                style={{
                  background:
                    layoutMode === tab.id
                      ? "rgba(16, 185, 129, 0.18)"
                      : "rgba(255,255,255,0.04)",
                  color: layoutMode === tab.id ? "#10B981" : "#94A3B8",
                  border:
                    layoutMode === tab.id
                      ? "1px solid rgba(16, 185, 129, 0.4)"
                      : "1px solid var(--border-subtle)",
                  borderRadius: "6px",
                  padding: "0.28rem 0.7rem",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {graphData?.stats && (
            <div style={{ fontSize: "0.73rem", color: "#94A3B8" }}>
              Grounded Network:{" "}
              <strong style={{ color: "#10B981" }}>{graphData.stats.total_nodes}</strong> nodes •{" "}
              <strong style={{ color: "#06B6D4" }}>{graphData.stats.total_edges}</strong> edges •{" "}
              <code>v{graphData.graph_version}</code>
            </div>
          )}
        </div>

        {/* Workspace Content */}
        <div
          style={{
            flex: 1,
            display: "grid",
            gridTemplateColumns:
              layoutMode === "split" ? "1.05fr 0.95fr" : "1fr",
            overflow: "hidden",
          }}
        >
          {(layoutMode === "editor" || layoutMode === "split") && (
            <div
              style={{
                height: "100%",
                overflow: "hidden",
                borderRight:
                  layoutMode === "split" ? "1px solid var(--border-subtle)" : "none",
              }}
            >
              <NoteEditor
                vaultId={vaultId}
                note={activeNote}
                documents={documents}
                allNotes={notes}
                onNoteSaved={handleNoteSaved}
                onSelectNoteById={handleSelectNoteById}
                onCreateLinkedNote={handleCreateNote}
                onOpenDocumentCitation={onOpenDocumentCitation}
                onFilterByTag={handleTagFilter}
              />
            </div>
          )}

          {(layoutMode === "graph" || layoutMode === "split") && (
            <div style={{ height: "100%", overflow: "hidden" }}>
              <KnowledgeGraphCanvas
                graphData={graphData}
                onSelectNoteNode={handleSelectNoteById}
                onOpenDocumentCitation={onOpenDocumentCitation}
                onPinToNote={handlePinNodeToNote}
                onRefreshGraph={handleSyncGraph}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

