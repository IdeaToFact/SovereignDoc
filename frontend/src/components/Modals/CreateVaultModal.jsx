// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState } from "react";
import { api } from "../../services/api";

export default function CreateVaultModal({ isOpen, onClose, onVaultCreated }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    try {
      const created = await api.createVault(name.trim(), description.trim());
      onVaultCreated(created);
      onClose();
      setName("");
      setDescription("");
    } catch (err) {
      console.error("Failed to create vault", err);
      alert("Error creating vault");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)" }}>
            Create New Document Vault
          </h3>
          <button className="btn-icon" onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-secondary)", marginBottom: "0.3rem" }}>
              Vault Name
            </label>
            <input
              type="text"
              className="chat-input"
              style={{ width: "100%" }}
              placeholder="e.g. M&A Target Audit, Q3 Research Vault"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-secondary)", marginBottom: "0.3rem" }}>
              Description (Optional)
            </label>
            <textarea
              className="chat-input"
              style={{ width: "100%" }}
              placeholder="Private matter notes, client ID, or compliance tags"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.5rem" }}>
            <button
              type="button"
              className="btn-icon"
              style={{ padding: "0.5rem 1rem", background: "rgba(255,255,255,0.06)", borderRadius: "var(--radius-md)" }}
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-send"
              disabled={loading || !name.trim()}
            >
              {loading ? "Creating..." : "Create Vault"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}