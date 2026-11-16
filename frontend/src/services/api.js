// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

// SovereignDoc Local Air-Gap API Client (Zero External Network Traffic)

const BASE = "/api";

export const api = {
  // System & Hardware
  async getHealth() {
    const res = await fetch(`${BASE}/system/health`);
    return res.json();
  },

  async getHardware() {
    const res = await fetch(`${BASE}/system/hardware`);
    return res.json();
  },

  async getCapabilities() {
    const res = await fetch(`${BASE}/system/capabilities`);
    return res.json();
  },

  // Models
  async getModels() {
    const res = await fetch(`${BASE}/models`);
    return res.json();
  },

  async selectModel(modelName) {
    const res = await fetch(`${BASE}/models/select`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_name: modelName }),
    });
    return res.json();
  },

  // Workspace Persistence
  async getWorkspaceState() {
    const res = await fetch(`${BASE}/workspace/state`);
    return res.json();
  },

  async updateWorkspaceState(data) {
    const res = await fetch(`${BASE}/workspace/state`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async acceptDisclaimer() {
    const res = await fetch(`${BASE}/workspace/accept-disclaimer`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to accept legal disclaimer");
    return res.json();
  },

  // Vaults
  async listVaults() {
    try {
      const res = await fetch(`${BASE}/vaults`);
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  },

  async createVault(name, description = "") {
    const res = await fetch(`${BASE}/vaults`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to create vault (${res.status})`);
    }
    return res.json();
  },

  async deleteVault(vaultId) {
    const res = await fetch(`${BASE}/vaults/${vaultId}`, { method: "DELETE" });
    return res.json();
  },

  // Documents
  async listDocuments(vaultId) {
    if (!vaultId) return [];
    try {
      const res = await fetch(`${BASE}/vaults/${vaultId}/documents`);
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  },

  async uploadDocument(vaultId, file) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE}/vaults/${vaultId}/documents/upload`, {
      method: "POST",
      body: formData,
    });
    return res.json();
  },

  async deleteDocument(vaultId, docId) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/documents/${docId}`, {
      method: "DELETE",
    });
    return res.json();
  },

  getDocumentFileUrl(vaultId, docId) {
    return `${BASE}/vaults/${vaultId}/documents/${docId}/file`;
  },

  async getDocumentHtml(vaultId, docId) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/documents/${docId}/html`);
    if (!res.ok) throw new Error("Failed to load document HTML");
    return res.json();
  },

  // Sessions
  async listSessions(vaultId, documentId = null) {
    if (!vaultId) return [];
    try {
      const url = documentId
        ? `${BASE}/vaults/${vaultId}/documents/${documentId}/sessions`
        : `${BASE}/vaults/${vaultId}/sessions`;
      const res = await fetch(url);
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  },

  async listDocumentSessions(vaultId, documentId) {
    if (!vaultId || !documentId) return [];
    try {
      const res = await fetch(`${BASE}/vaults/${vaultId}/documents/${documentId}/sessions`);
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  },

  async createSession(vaultId, title = "New Analysis", documentId = null) {
    const url = documentId
      ? `${BASE}/vaults/${vaultId}/documents/${documentId}/sessions`
      : `${BASE}/vaults/${vaultId}/sessions`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, document_id: documentId }),
    });
    return res.json();
  },

  async getSessionMessages(vaultId, sessionId) {
    if (!vaultId || !sessionId) return [];
    try {
      const res = await fetch(`${BASE}/vaults/${vaultId}/sessions/${sessionId}/messages`);
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  },

  async deleteSession(vaultId, sessionId) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/sessions/${sessionId}`, {
      method: "DELETE",
    });
    return res.json();
  },

  // Milestone 4: Legal & Contract Intelligence API
  async createReviewRun(vaultId, docId) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/documents/${docId}/review-runs`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to execute contract review run");
    return res.json();
  },

  async listReviewRuns(vaultId, docId) {
    if (!vaultId || !docId) return [];
    try {
      const res = await fetch(`${BASE}/vaults/${vaultId}/documents/${docId}/review-runs`);
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  },

  async getReviewRun(vaultId, docId, runId) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/documents/${docId}/review-runs/${runId}`);
    return res.json();
  },

  getExportReviewPackageUrl(vaultId, docId, runId) {
    return `${BASE}/vaults/${vaultId}/documents/${docId}/review-runs/${runId}/export`;
  },

  async compareContracts(vaultId, docAId, docBId) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ doc_a_id: docAId, doc_b_id: docBId }),
    });
    if (!res.ok) throw new Error("Failed to compare contracts");
    return res.json();
  },

  // Milestone 5: Personal Second Brain & Grounded Knowledge Graph API
  async listNotes(vaultId, { q = "", tag = "", documentId = "" } = {}) {
    if (!vaultId) return [];
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (tag) params.set("tag", tag);
      if (documentId) params.set("document_id", documentId);
      const qs = params.toString();
      const res = await fetch(`${BASE}/vaults/${vaultId}/notes${qs ? `?${qs}` : ""}`);
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  },

  async createNote(vaultId, payload) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to create note");
    return res.json();
  },

  async getNote(vaultId, noteId) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/notes/${noteId}`);
    if (!res.ok) throw new Error("Failed to load note");
    return res.json();
  },

  async updateNote(vaultId, noteId, payload) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/notes/${noteId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to update note");
    return res.json();
  },

  async deleteNote(vaultId, noteId) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/notes/${noteId}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete note");
    return res.json();
  },

  async listNoteVersions(vaultId, noteId) {
    if (!vaultId || !noteId) return [];
    try {
      const res = await fetch(`${BASE}/vaults/${vaultId}/notes/${noteId}/versions`);
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  },

  async restoreNoteVersion(vaultId, noteId, versionId) {
    const res = await fetch(
      `${BASE}/vaults/${vaultId}/notes/${noteId}/versions/${versionId}/restore`,
      { method: "POST" }
    );
    if (!res.ok) throw new Error("Failed to restore note version");
    return res.json();
  },

  async quickCaptureToNote(vaultId, payload) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/notes/quick-capture`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to pin citation to note");
    return res.json();
  },

  async getVaultGraph(vaultId, q = "") {
    const qs = q ? `?q=${encodeURIComponent(q)}` : "";
    const res = await fetch(`${BASE}/vaults/${vaultId}/graph${qs}`);
    if (!res.ok) throw new Error("Failed to load knowledge graph");
    return res.json();
  },

  async syncVaultGraph(vaultId) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/graph/sync`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to sync knowledge graph");
    return res.json();
  },

  async getVaultGraphStats(vaultId) {
    const res = await fetch(`${BASE}/vaults/${vaultId}/graph/stats`);
    if (!res.ok) throw new Error("Failed to load vault graph statistics");
    return res.json();
  },

  // Milestone 6: Air-Gap Security Audit & Hardware Benchmark
  async getAirgapAudit(refresh = false) {
    const qs = refresh ? "?refresh=true" : "";
    const res = await fetch(`${BASE}/system/airgap-audit${qs}`);
    if (!res.ok) throw new Error("Failed to run air-gap security audit");
    return res.json();
  },

  async runHardwareBenchmark() {
    const res = await fetch(`${BASE}/system/benchmark`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to run hardware benchmark");
    return res.json();
  },

  // SSE Chat Stream
  async streamChat(vaultId, payload, callbacks) {
    const { onToken, onRetrievalDone, onEvidence, onDone, onError } = callbacks;

    try {
      const response = await fetch(`${BASE}/vaults/${vaultId}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Chat stream failed with status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = null;
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("event:")) {
            currentEvent = trimmed.replace("event:", "").trim();
          } else if (trimmed.startsWith("data:") && currentEvent) {
            const dataStr = trimmed.replace("data:", "").trim();
            try {
              const data = JSON.parse(dataStr);
              if (currentEvent === "retrieval_done" && onRetrievalDone) onRetrievalDone(data);
              else if (currentEvent === "token" && onToken) onToken(data.text);
              else if (currentEvent === "evidence" && onEvidence) onEvidence(data.evidence);
              else if (currentEvent === "done" && onDone) onDone(data);
            } catch (err) {
              console.error("Failed to parse SSE data chunk", err);
            }
            currentEvent = null;
          }
        }
      }
    } catch (err) {
      if (onError) onError(err);
      else console.error("Stream error:", err);
    }
  },
};
