// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("SovereignDoc Unhandled Render Error:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100vh",
            width: "100vw",
            backgroundColor: "#080C14",
            color: "#E2E8F0",
            fontFamily: "Inter, sans-serif",
            padding: "2rem",
            boxSizing: "border-box",
            textAlign: "center",
          }}
        >
          <div
            style={{
              maxWidth: "520px",
              padding: "2rem",
              backgroundColor: "#0D1322",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              borderRadius: "0.75rem",
              boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5)",
            }}
          >
            <div style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>⚠️</div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "0.5rem", color: "#F87171" }}>
              Workspace Render Interruption
            </h2>
            <p style={{ fontSize: "0.85rem", color: "#94A3B8", lineHeight: "1.5", marginBottom: "1.5rem" }}>
              An unexpected render issue occurred while loading workspace entities. Your underlying local vault data remains safe and unmodified.
            </p>
            {this.state.error?.message && (
              <pre
                style={{
                  fontSize: "0.75rem",
                  color: "#CBD5E1",
                  backgroundColor: "rgba(0, 0, 0, 0.4)",
                  padding: "0.75rem",
                  borderRadius: "0.375rem",
                  overflowX: "auto",
                  textAlign: "left",
                  marginBottom: "1.5rem",
                }}
              >
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={this.handleReset}
              style={{
                backgroundColor: "#10B981",
                color: "#04160E",
                fontWeight: 700,
                fontSize: "0.85rem",
                padding: "0.6rem 1.25rem",
                borderRadius: "0.375rem",
                border: "none",
                cursor: "pointer",
                transition: "background-color 0.15s ease",
              }}
            >
              Reload Workspace
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

