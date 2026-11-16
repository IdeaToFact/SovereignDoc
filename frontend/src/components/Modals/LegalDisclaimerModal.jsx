// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";

export default function LegalDisclaimerModal({
  isOpen,
  isAccepted,
  acceptedVersion,
  acceptedAt,
  currentVersion = "1.1",
  onAccept,
  onClose,
}) {
  const [checked, setChecked] = useState(Boolean(isAccepted));
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setChecked(Boolean(isAccepted));
  }, [isAccepted, isOpen]);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    if (!checked) return;
    setSubmitting(true);
    try {
      await onAccept();
    } finally {
      setSubmitting(false);
    }
  };

  return createPortal(
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(9, 13, 22, 0.86)",
        backdropFilter: "blur(5px)",
        zIndex: 100000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem 1.5rem",
        overflowY: "auto",
      }}
      onClick={() => {
        if (isAccepted && onClose) onClose();
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "680px",
          maxHeight: "calc(100vh - 4rem)",
          margin: "auto",
          backgroundColor: "#0F172A",
          border: "1px solid #1E293B",
          borderRadius: "12px",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          boxShadow: "0 24px 48px rgba(0,0,0,0.65)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Parent Entity Branding & Title */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "1.1rem 1.35rem",
            borderBottom: "1px solid #1E293B",
            backgroundColor: "rgba(15, 23, 42, 0.98)",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            {/* Idea To Fact LLC Isometric Cube Checkmark Logo */}
            <svg width="34" height="34" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 4L30 11V25L18 32L6 25V11L18 4Z" stroke="#06B6D4" strokeWidth="2" strokeLinejoin="round" />
              <path d="M18 4V32" stroke="#06B6D4" strokeWidth="1.5" strokeDasharray="2 2" />
              <path d="M6 11L18 18L30 11" stroke="#06B6D4" strokeWidth="2" strokeLinejoin="round" />
              <path
                d="M12 18L16.5 22.5L25 13.5"
                stroke="#10B981"
                strokeWidth="3.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <div>
              <div style={{ fontWeight: 700, fontSize: "1.05rem", color: "#F8FAFC", lineHeight: 1.2 }}>
                Idea To Fact LLC
              </div>
              <div style={{ fontSize: "0.75rem", color: "#94A3B8", fontFamily: "monospace", marginTop: "0.15rem" }}>
                AirGap Axis Platform • SovereignDoc Community Edition v1.1.0-community (Disclaimer v{currentVersion})
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.65rem" }}>
            <span
              style={{
                padding: "0.22rem 0.55rem",
                fontSize: "0.68rem",
                fontFamily: "monospace",
                fontWeight: 700,
                borderRadius: "4px",
                backgroundColor: "rgba(6, 78, 59, 0.85)",
                color: "#34D399",
                border: "1px solid rgba(16, 185, 129, 0.4)",
              }}
            >
              100% AIR-GAPPED
            </span>

            {isAccepted && onClose && (
              <button
                className="btn-icon"
                onClick={onClose}
                title="Close"
                style={{ fontSize: "1.1rem", color: "#94A3B8" }}
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Scrollable Legal Notice Body */}
        <div
          style={{
            padding: "1.25rem 1.35rem",
            overflowY: "auto",
            flex: 1,
            minHeight: 0,
            fontSize: "0.84rem",
            lineHeight: 1.6,
            color: "#CBD5E1",
            display: "flex",
            flexDirection: "column",
            gap: "0.95rem",
          }}
        >
          <div
            style={{
              padding: "0.85rem 1rem",
              borderRadius: "8px",
              backgroundColor: "rgba(245, 158, 11, 0.1)",
              border: "1px solid rgba(245, 158, 11, 0.35)",
              color: "#FDE68A",
              fontWeight: 500,
            }}
          >
            <strong>Important Legal Disclaimer:</strong> SovereignDoc is an automated document processing and
            intelligence tool provided by <strong>Idea To Fact LLC</strong> for informational, research, and
            productivity assistance only. SovereignDoc does <strong>not</strong> provide legal advice, legal
            representation, or formal legal opinions.
          </div>

          <div
            style={{
              backgroundColor: "rgba(2, 6, 23, 0.65)",
              border: "1px solid #1E293B",
              borderRadius: "8px",
              padding: "1rem",
              display: "flex",
              flexDirection: "column",
              gap: "0.85rem",
            }}
          >
            <div>
              <div style={{ fontWeight: 700, color: "#F8FAFC", marginBottom: "0.2rem" }}>
                1. No Legal Advice / UPL Notice
              </div>
              <p style={{ margin: 0, color: "#94A3B8" }}>
                SovereignDoc is an automated document processing and intelligence tool for informational, research, and
                productivity assistance. Use does not constitute legal advice or establish an attorney-client
                relationship with Idea To Fact LLC or any open-source contributor.
              </p>
            </div>

            <div>
              <div style={{ fontWeight: 700, color: "#F8FAFC", marginBottom: "0.2rem" }}>
                2. Human-in-the-Loop Attorney Verification
              </div>
              <p style={{ margin: 0, color: "#94A3B8" }}>
                Automated risk audits, clause classifications, obligations registers, and redlines are generated via
                static rules and local AI models. Findings may contain errors or omissions and{" "}
                <strong style={{ color: "#E2E8F0" }}>
                  must be independently verified by a qualified, licensed attorney
                </strong>{" "}
                prior to executing agreements or taking operational action.
              </p>
            </div>

            <div>
              <div style={{ fontWeight: 700, color: "#F8FAFC", marginBottom: "0.2rem" }}>
                3. Local Air-Gap &amp; Data Isolation (GNU AGPLv3)
              </div>
              <p style={{ margin: 0, color: "#94A3B8" }}>
                SovereignDoc is provided <strong>&ldquo;AS IS&rdquo;</strong> without warranty of any kind under the GNU
                Affero General Public License v3.0 (Sections 15 &amp; 16). SovereignDoc operates locally on host
                loopback (<code>127.0.0.1</code>) with zero remote telemetry. You retain full responsibility for host machine
                security and network configuration.
              </p>
            </div>

            <div>
              <div style={{ fontWeight: 700, color: "#F8FAFC", marginBottom: "0.2rem" }}>
                4. Source Code Availability (GNU AGPLv3 §13)
              </div>
              <p style={{ margin: 0, color: "#94A3B8" }}>
                Pursuant to Section 13 of the GNU Affero General Public License, the complete Corresponding Source code for
                SovereignDoc Community Edition is freely available to all users at:{" "}
                <a
                  href="https://github.com/ideatofact/sovereigndoc"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "#38BDF8", textDecoration: "underline" }}
                >
                  github.com/ideatofact/sovereigndoc
                </a>
              </p>
            </div>
          </div>
        </div>

        {/* Footer Acceptance Controls */}
        <div
          style={{
            padding: "1rem 1.35rem",
            borderTop: "1px solid #1E293B",
            backgroundColor: "#090D16",
            display: "flex",
            flexDirection: "column",
            gap: "0.85rem",
            flexShrink: 0,
          }}
        >
          <label
            htmlFor="disclaimer-checkbox"
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "0.65rem",
              cursor: isAccepted ? "default" : "pointer",
              fontSize: "0.82rem",
              color: "#E2E8F0",
              fontWeight: 500,
              lineHeight: 1.45,
            }}
          >
            <input
              id="disclaimer-checkbox"
              type="checkbox"
              checked={checked}
              disabled={isAccepted}
              onChange={(e) => setChecked(e.target.checked)}
              style={{ marginTop: "0.18rem", width: "16px", height: "16px", accentColor: "#10B981" }}
            />
            <span>
              I understand that SovereignDoc is an automated legal document analysis tool provided by Idea To Fact LLC
              and is not a substitute for professional legal counsel.
            </span>
          </label>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem" }}>
            <div style={{ fontSize: "0.73rem", color: "#94A3B8" }}>
              {isAccepted
                ? `Accepted Disclaimer Version v${acceptedVersion || currentVersion}${
                    acceptedAt ? ` on ${new Date(acceptedAt).toLocaleString()}` : ""
                  }`
                : "Acceptance is stored locally in your SQLite workspace database."}
            </div>

            {isAccepted ? (
              <button
                onClick={onClose}
                style={{
                  padding: "0.5rem 1.15rem",
                  borderRadius: "8px",
                  border: "1px solid #334155",
                  backgroundColor: "#1E293B",
                  color: "#F8FAFC",
                  fontWeight: 600,
                  fontSize: "0.82rem",
                  cursor: "pointer",
                }}
              >
                Close
              </button>
            ) : (
              <button
                onClick={handleConfirm}
                disabled={!checked || submitting}
                style={{
                  padding: "0.55rem 1.3rem",
                  borderRadius: "8px",
                  border: "none",
                  backgroundColor: checked ? "#059669" : "#1E293B",
                  color: checked ? "#FFFFFF" : "#64748B",
                  fontWeight: 600,
                  fontSize: "0.84rem",
                  cursor: checked && !submitting ? "pointer" : "not-allowed",
                  boxShadow: checked ? "0 4px 14px rgba(5, 150, 105, 0.35)" : "none",
                }}
              >
                {submitting ? "Persisting Onboarding Acceptance..." : "Accept & Proceed to Workspace"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
