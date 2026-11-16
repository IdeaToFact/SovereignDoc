// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState, useRef, useEffect } from "react";
import { api } from "../../services/api";
import MultiCitationGroup from "./MultiCitationGroup";
import SourceHoverPopover from "./SourceHoverPopover";
import ExportFindingsButton from "./ExportFindingsButton";

const RECIPES = [
  { id: "obligations", label: "📋 Obligations & Deadlines", query: "Summarize all affirmative obligations, required notices, and calendar deadlines in this document." },
  { id: "liability", label: "⚠️ Liability & Indemnity", query: "Audit all indemnification provisions, liability caps, warranties, and carve-outs in this document." },
  { id: "termination", label: "🔍 Termination Triggers", query: "Detail the termination provisions, notice periods, cure conditions, and survival terms." },
  { id: "executive", label: "💡 Executive Briefing", query: "Provide an executive summary of the key terms, economic risks, and rights in bullet points." },
];


function renderGroundedContent(content, evidenceList, onCitationClick) {
  if (!content) return null;
  // Match patterns like [Source 1 | Doc: ...] or [Source 1]
  const sourceRegex = /(\[Source\s+(\d+)[^\]]*\])/g;
  const parts = content.split(sourceRegex);

  return parts.map((part, index) => {
    const match = part.match(/\[Source\s+(\d+)([^\]]*)\]/);
    if (match) {
      const sourceNum = parseInt(match[1], 10);
      const evItem = evidenceList && evidenceList[sourceNum - 1];
      const extraInfo = match[2] ? match[2].trim() : "";
      return (
        <span
          key={index}
          className="clickable-source-badge"
          onClick={() => {
            if (evItem && onCitationClick) {
              onCitationClick(evItem);
            } else if (evidenceList && evidenceList[0] && onCitationClick) {
              onCitationClick(evidenceList[0]);
            }
          }}
          title={evItem ? `Jump to ${evItem.filename} (Page ${evItem.page_number})` : "Jump to referenced paragraph"}
        >
          📄 Source {sourceNum} {extraInfo ? `(${extraInfo.replace(/^\|\s*/, "")})` : ""} ↗
        </span>
      );
    }
    return part;
  });
}

export default function ChatPane({
  vaultId,
  activeDocument,
  activeVault,
  activeModel,
  activeSession,
  onCitationClick,
  onSessionUpdated,
}) {
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState("");
  const [hoveredEvidence, setHoveredEvidence] = useState(null);
  const [hoverPosition, setHoverPosition] = useState(null);
  const [pinnedEvidenceIds, setPinnedEvidenceIds] = useState({});

  const handlePinEvidence = async (ev) => {
    if (!vaultId || !ev) return;
    try {
      await api.quickCaptureToNote(vaultId, {
        document_id: ev.document_id || activeDocument?.id,
        filename: ev.filename || activeDocument?.filename,
        page_number: ev.page_number || 1,
        section: ev.section || null,
        clause_title: ev.clause_title || `Page ${ev.page_number} Evidence`,
        verbatim_text: ev.evidence_text || ev.surrounding_context || "",
        source_type: "EVIDENCE",
      });
      setPinnedEvidenceIds((prev) => ({ ...prev, [ev.citation_id]: true }));
    } catch (err) {
      console.error("Failed to pin evidence to note:", err);
    }
  };

  const messagesEndRef = useRef(null);

  // Load session messages when activeSession changes
  useEffect(() => {
    if (!vaultId || !activeSession) {
      setMessages([]);
      return;
    }

    const loadMessages = async () => {
      try {
        const msgs = await api.getSessionMessages(vaultId, activeSession.id);
        setMessages(Array.isArray(msgs) ? msgs : []);
      } catch (err) {
        console.error("Failed to load session messages", err);
        setMessages([]);
      }
    };

    loadMessages();
  }, [vaultId, activeSession]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamedText]);

  const handleHoverEvidence = (e, ev) => {
    if (!ev || !e) {
      setHoveredEvidence(null);
      setHoverPosition(null);
      return;
    }
    const rect = e.currentTarget.getBoundingClientRect();
    setHoverPosition({
      x: Math.max(rect.left - 330, 20),
      y: Math.max(rect.top - 80, 70),
    });
    setHoveredEvidence(ev);
  };

  const handleSend = async (queryText = inputQuery, recipeId = null) => {
    const q = queryText.trim();
    if (!q || isStreaming || !vaultId) return;

    setInputQuery("");
    setIsStreaming(true);
    setStreamedText("");

    // Optimistically show user message
    const userMsg = {
      id: "temp_user_" + Date.now(),
      role: "user",
      content: q,
      evidence: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    let accumulatedText = "";
    let finalEvidence = [];

    const payload = {
      query: q,
      session_id: activeSession?.id || null,
      document_id: activeDocument?.id || null,
      model_name: activeModel,
      mode: "hybrid",
      enable_reranker: true,
      top_k: 5,
      expand_window: true,
      recipe: recipeId,
    };

    await api.streamChat(vaultId, payload, {
      onRetrievalDone: (data) => {
        // Can display subtle telemetry chip if desired
      },
      onToken: (token) => {
        accumulatedText += token;
        setStreamedText(accumulatedText);
      },
      onEvidence: (evList) => {
        finalEvidence = evList || [];
      },
      onDone: (metrics) => {
        const asstMsg = {
          id: metrics.message_id || "asst_" + Date.now(),
          role: "assistant",
          content: accumulatedText,
          evidence: finalEvidence,
          tokens_generated: metrics.tokens_generated,
          tokens_per_second: metrics.tokens_per_second,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, asstMsg]);
        setStreamedText("");
        setIsStreaming(false);

        if (onSessionUpdated && metrics?.session_id) {
          onSessionUpdated(metrics.session_id);
        }
      },
      onError: (err) => {
        console.error("Stream error", err);
        setIsStreaming(false);
      },
    });
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <section className="chat-pane">
      {/* Header */}
      <div className="chat-header">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ fontSize: "0.84rem", fontWeight: 700, color: "var(--text-primary)" }}>
            Grounded Reviewer
          </span>
          <span className="badge" style={{ background: "rgba(255,255,255,0.05)", fontSize: "0.68rem" }}>
            Hybrid RAG + Cross-Encoder
          </span>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="chat-messages">
        {(!Array.isArray(messages) || messages.length === 0) && !isStreaming && (
          <div style={{ textAlign: "center", color: "var(--text-muted)", marginTop: "2rem" }}>
            <p style={{ fontSize: "0.85rem", fontWeight: 500, color: "var(--text-secondary)" }}>
              Zero-Cloud Legal & Research Intelligence
            </p>
            <p style={{ fontSize: "0.78rem", marginTop: "0.4rem" }}>
              Ask a question below or trigger a specialized prompt recipe.
            </p>
          </div>
        )}

        {(Array.isArray(messages) ? messages : []).map((m, idx) => (
          <div
            key={m.id || idx}
            className={`message-bubble ${m.role === "user" ? "message-user" : "message-assistant"}`}
          >
            <div style={{ whiteSpace: "pre-wrap" }}>
              {m.role === "assistant" && m.evidence && m.evidence.length > 0
                ? renderGroundedContent(m.content, m.evidence, onCitationClick)
                : m.content}
            </div>

            {/* Citations Accordion & Export for Assistant */}
            {m.role === "assistant" && (
              <>
                {m.evidence && m.evidence.length > 0 && (
                  <MultiCitationGroup
                    evidenceList={m.evidence}
                    onCitationClick={onCitationClick}
                    onHoverEvidence={handleHoverEvidence}
                    onPinEvidence={handlePinEvidence}
                    pinnedIds={pinnedEvidenceIds}
                  />
                )}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "0.6rem" }}>
                  <ExportFindingsButton
                    query={messages[idx - 1]?.content || "Document Analysis"}
                    response={m.content}
                    evidenceList={m.evidence}
                    activeDocument={activeDocument}
                    activeVault={activeVault}
                    activeModel={activeModel}
                  />
                  {m.tokens_per_second > 0 && (
                    <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                      {m.tokens_per_second} tokens/sec
                    </span>
                  )}
                </div>
              </>
            )}
          </div>
        ))}

        {/* Real-time Streaming Bubble */}
        {isStreaming && (
          <div className="message-bubble message-assistant">
            <div style={{ whiteSpace: "pre-wrap" }}>
              {streamedText || <span style={{ color: "var(--emerald-primary)" }}>Reasoning...</span>}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Hover Popover */}
      {hoveredEvidence && <SourceHoverPopover evidence={hoveredEvidence} position={hoverPosition} onCitationClick={onCitationClick} />}

      {/* Prompt Recipe Bar */}
      <div className="recipe-bar">
        {RECIPES.map((r) => (
          <button
            key={r.id}
            className="recipe-chip"
            disabled={isStreaming}
            onClick={() => handleSend(r.query, r.id)}
          >
            {r.label}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <div className="chat-input-area">
        <textarea
          className="chat-input"
          placeholder="Ask a question about the document... (Press Enter to send)"
          rows={2}
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
        />
        <button
          className="btn-send"
          disabled={!inputQuery.trim() || isStreaming}
          onClick={() => handleSend()}
        >
          {isStreaming ? "Streaming..." : "Send"}
        </button>
      </div>
    </section>
  );
}