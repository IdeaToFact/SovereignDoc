// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState, useEffect } from "react";
import { api } from "./services/api";
import Header from "./components/Header";
import VaultSidebar from "./components/VaultSidebar";
import DocumentViewer from "./components/SplitView/DocumentViewer";
import ChatPane from "./components/Chat/ChatPane";
import RiskAuditView from "./components/Legal/RiskAuditView";
import RedlineDiffView from "./components/Legal/RedlineDiffView";
import SecondBrainView from "./components/SecondBrain/SecondBrainView";
import CreateVaultModal from "./components/Modals/CreateVaultModal";
import LegalDisclaimerModal from "./components/Modals/LegalDisclaimerModal";

export default function App() {
  const [hardware, setHardware] = useState(null);
  const [activeModel, setActiveModel] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeMode, setActiveMode] = useState("reviewer"); // "reviewer" | "audit" | "redline"

  const [vaults, setVaults] = useState([]);
  const [activeVault, setActiveVault] = useState(null);

  const [documents, setDocuments] = useState([]);
  const [activeDocument, setActiveDocument] = useState(null);

  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);

  const [activeCitation, setActiveCitation] = useState(null);

  const handleCitationClick = (ev) => {
    if (!ev) return;
    setActiveCitation({ ...ev, _timestamp: Date.now() });

    // Switch active document if the citation belongs to another document in the vault
    if (ev.document_id && (!activeDocument || activeDocument.id !== ev.document_id)) {
      const match = documents.find((d) => d.id === ev.document_id || d.filename === ev.filename);
      if (match) {
        setActiveDocument(match);
      }
    } else if (ev.filename && (!activeDocument || activeDocument.filename !== ev.filename)) {
      const match = documents.find((d) => d.filename === ev.filename);
      if (match) {
        setActiveDocument(match);
      }
    }
  };

  const [isCreateVaultOpen, setIsCreateVaultOpen] = useState(false);
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(true);
  const [acceptedDisclaimerVersion, setAcceptedDisclaimerVersion] = useState("1.1");
  const [disclaimerAcceptedAt, setDisclaimerAcceptedAt] = useState(null);
  const [currentDisclaimerVersion, setCurrentDisclaimerVersion] = useState("1.1");
  const [isDisclaimerModalOpen, setIsDisclaimerModalOpen] = useState(false);

  // 1. Initial Load: Hardware, Workspace Persistence, Vaults
  useEffect(() => {
    const initApp = async () => {
      try {
        // Fetch hardware info
        const hw = await api.getHardware();
        setHardware(hw);

        // Fetch persisted workspace state from SQLite
        const savedState = await api.getWorkspaceState();
        if (savedState) {
          if (savedState.sidebar_collapsed !== undefined) {
            setSidebarCollapsed(savedState.sidebar_collapsed);
          }
          if (savedState.active_model) {
            setActiveModel(savedState.active_model);
          }
          const isAcc = Boolean(savedState.disclaimer_accepted);
          setDisclaimerAccepted(isAcc);
          setAcceptedDisclaimerVersion(savedState.accepted_disclaimer_version || null);
          setDisclaimerAcceptedAt(savedState.disclaimer_accepted_at || null);
          setCurrentDisclaimerVersion(savedState.current_disclaimer_version || "1.1");
          if (!isAcc) {
            setIsDisclaimerModalOpen(true);
          }
        }

        // Fetch Vaults
        let vaultList = await api.listVaults();
        if (vaultList.length === 0) {
          const defaultVault = await api.createVault("Primary Matter Vault", "Default workspace vault");
          vaultList = [defaultVault];
        }
        setVaults(vaultList);

        // Resolve active vault
        let currentVault = vaultList[0];
        if (savedState?.active_vault_id) {
          const found = vaultList.find((v) => v.id === savedState.active_vault_id);
          if (found) currentVault = found;
        }
        setActiveVault(currentVault);
      } catch (err) {
        console.error("Initialization error", err);
      }
    };

    initApp();
  }, []);

  // Handle Vault Selection or Creation with clean state isolation
  const handleSelectVault = (vault) => {
    if (!vault) return;
    setActiveDocument(null);
    setDocuments([]);
    setActiveSession(null);
    setSessions([]);
    setActiveVault(vault);
  };

  // 2. Load Documents & Sessions when Active Vault changes
  useEffect(() => {
    if (!activeVault) return;

    // Immediately isolate state to prevent cross-vault id bleeding
    setActiveDocument(null);
    setDocuments([]);
    setActiveSession(null);
    setSessions([]);

    const loadVaultData = async () => {
      try {
        const [docs, sessList] = await Promise.all([
          api.listDocuments(activeVault.id),
          api.listSessions(activeVault.id),
        ]);

        const validDocs = Array.isArray(docs) ? docs : [];
        const validSessions = Array.isArray(sessList) ? sessList : [];

        setDocuments(validDocs);
        setActiveDocument(validDocs.length > 0 ? validDocs[0] : null);

        setSessions(validSessions);
        setActiveSession(validSessions.length > 0 ? validSessions[0] : null);

        // Persist active vault selection
        api.updateWorkspaceState({ active_vault_id: activeVault.id });
      } catch (err) {
        console.error("Failed to load vault data", err);
      }
    };

    loadVaultData();
  }, [activeVault]);

  // Handle Model Selection
  const handleSelectModel = async (modelName) => {
    try {
      await api.selectModel(modelName);
      setActiveModel(modelName);
      api.updateWorkspaceState({ active_model: modelName });
    } catch (err) {
      console.error("Failed to select model", err);
    }
  };

  // Handle Sidebar Toggle
  const handleToggleSidebar = () => {
    const nextState = !sidebarCollapsed;
    setSidebarCollapsed(nextState);
    api.updateWorkspaceState({ sidebar_collapsed: nextState });
  };

  // Handle Document Uploaded
  const handleDocumentUploaded = async () => {
    if (!activeVault) return;
    const docs = await api.listDocuments(activeVault.id);
    setDocuments(docs || []);
    if (docs && docs.length > 0) {
      setActiveDocument(docs[0]);
    }
  };

  // Handle Document Deleted
  const handleDocumentDeleted = async (deletedDocId) => {
    if (!activeVault) return;
    const docs = await api.listDocuments(activeVault.id);
    setDocuments(docs || []);
    if (activeDocument?.id === deletedDocId) {
      setActiveDocument(docs && docs.length > 0 ? docs[0] : null);
    }
  };

  // Handle Session Updated / Created (Refresh sessions list dynamically)
  const handleSessionUpdated = async (sessionId) => {
    if (!activeVault) return;
    try {
      const updatedList = await api.listSessions(activeVault.id);
      setSessions(updatedList || []);
      if (sessionId) {
        const found = (updatedList || []).find((s) => s.id === sessionId);
        if (found) {
          setActiveSession(found);
        }
      }
    } catch (err) {
      console.error("Failed to refresh sessions", err);
    }
  };

  // Handle Document Selected (Auto-switch chat window to latest session for that document)
  const handleSelectDocument = (doc) => {
    setActiveDocument(doc);
    if (doc) {
      const docSessions = sessions.filter((s) => s.document_id === doc.id);
      if (docSessions.length > 0) {
        setActiveSession(docSessions[0]);
      } else {
        setActiveSession(null);
      }
    }
  };

  // Handle Session Created (Tag with active document)
  const handleCreateSession = async (documentId = null) => {
    if (!activeVault) return;
    try {
      const docId = documentId || activeDocument?.id || null;
      const newSess = await api.createSession(activeVault.id, `Analysis ${sessions.length + 1}`, docId);
      setSessions((prev) => [newSess, ...prev]);
      setActiveSession(newSess);
    } catch (err) {
      console.error("Failed to create session", err);
    }
  };

  // Handle Session Selected (Auto-switch document if session belongs to another contract)
  const handleSelectSession = (session) => {
    setActiveSession(session);
    if (session?.document_id && (!activeDocument || activeDocument.id !== session.document_id)) {
      const matchingDoc = documents.find((d) => d.id === session.document_id);
      if (matchingDoc) {
        setActiveDocument(matchingDoc);
      }
    }
  };

  return (
    <div className="app-container">
      {/* Top Header with Mode Tabs */}
      <Header
        hardware={hardware}
        activeModel={activeModel}
        onSelectModel={handleSelectModel}
        sidebarCollapsed={sidebarCollapsed}
        onToggleSidebar={handleToggleSidebar}
        activeMode={activeMode}
        onSelectMode={setActiveMode}
        activeVault={activeVault}
      />

      {/* Main Workspace Layout */}
      <div className={`workspace-grid ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
        {/* Left Pane: Vault, Document & Session Explorer */}
        <VaultSidebar
          vaults={vaults}
          activeVault={activeVault}
          onSelectVault={handleSelectVault}
          onCreateVaultClick={() => setIsCreateVaultOpen(true)}
          documents={documents}
          activeDocument={activeDocument}
          onSelectDocument={handleSelectDocument}
          onDocumentUploaded={handleDocumentUploaded}
          onDocumentDeleted={handleDocumentDeleted}
          sessions={sessions}
          activeSession={activeSession}
          onSelectSession={handleSelectSession}
          onCreateSession={handleCreateSession}
          onSessionDeleted={(deletedId) => {
            setSessions((prev) => prev.filter((s) => s.id !== deletedId));
            if (activeSession?.id === deletedId) {
              setActiveSession(null);
            }
          }}
          collapsed={sidebarCollapsed}
        />

        {/* Mode 1: Reviewer (Split-Screen Document Viewer + Grounded Chat) */}
        {activeMode === "reviewer" && (
          <>
            <DocumentViewer
              vaultId={activeVault?.id}
              activeDocument={activeDocument}
              activeCitation={activeCitation}
            />
            <ChatPane
              vaultId={activeVault?.id}
              activeDocument={activeDocument}
              activeVault={activeVault}
              activeModel={activeModel}
              activeSession={activeSession}
              onCitationClick={handleCitationClick}
              onSessionUpdated={handleSessionUpdated}
            />
          </>
        )}

        {/* Mode 2: Risk & Obligations Audit (Split-Screen PDF Viewer + Interactive Risk Matrix) */}
        {activeMode === "audit" && (
          <>
            <DocumentViewer
              vaultId={activeVault?.id}
              activeDocument={activeDocument}
              activeCitation={activeCitation}
            />
            <RiskAuditView
              vaultId={activeVault?.id}
              activeDocument={activeDocument}
              onJumpToEvidence={handleCitationClick}
            />
          </>
        )}

        {/* Mode 3: Redline Diff Viewer (Side-by-Side Clause Alignment & Word Diff) */}
        {activeMode === "redline" && (
          <div style={{ gridColumn: "span 2", height: "100%", overflow: "hidden" }}>
            <RedlineDiffView
              vaultId={activeVault?.id}
              documents={documents}
            />
          </div>
        )}

        {/* Mode 4: Personal Second Brain & Grounded Legal Knowledge Graph */}
        {activeMode === "second_brain" && (
          <SecondBrainView
            vaultId={activeVault?.id}
            activeDocument={activeDocument}
            documents={documents}
            onOpenDocumentCitation={(ev) => {
              setActiveMode("reviewer");
              handleCitationClick(ev);
            }}
          />
        )}
      </div>

      {/* Permanent Legal Disclaimer Footer Bar */}
      <footer
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.35rem 1rem",
          backgroundColor: "#090D16",
          borderTop: "1px solid var(--border-subtle, rgba(255,255,255,0.07))",
          fontSize: "0.73rem",
          color: "#94A3B8",
          flexShrink: 0,
        }}
      >
        <span>
          ⚖️ SovereignDoc is an automated legal workstation tool and does not provide legal advice. Always consult a licensed attorney.
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <a
            href="https://github.com/ideatofact/sovereigndoc"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: "#64748B",
              fontSize: "0.73rem",
              textDecoration: "underline",
            }}
          >
            Source Code (AGPLv3)
          </a>
          <button
            onClick={() => setIsDisclaimerModalOpen(true)}
            style={{
              background: "none",
              border: "none",
              color: "#10B981",
              fontSize: "0.73rem",
              fontWeight: 600,
              cursor: "pointer",
              textDecoration: "underline",
            }}
          >
            Legal Disclaimer &amp; License (v{currentDisclaimerVersion})
          </button>
        </div>
      </footer>

      {/* Create Vault Dialog */}
      <CreateVaultModal
        isOpen={isCreateVaultOpen}
        onClose={() => setIsCreateVaultOpen(false)}
        onVaultCreated={(newVault) => {
          setVaults((prev) => [...prev, newVault]);
          handleSelectVault(newVault);
        }}
      />

      {/* First-Run & On-Demand Legal Disclaimer Modal */}
      <LegalDisclaimerModal
        isOpen={isDisclaimerModalOpen}
        isAccepted={disclaimerAccepted}
        acceptedVersion={acceptedDisclaimerVersion}
        acceptedAt={disclaimerAcceptedAt}
        currentVersion={currentDisclaimerVersion}
        onAccept={async () => {
          const updated = await api.acceptDisclaimer();
          setDisclaimerAccepted(Boolean(updated.disclaimer_accepted));
          setAcceptedDisclaimerVersion(updated.accepted_disclaimer_version);
          setDisclaimerAcceptedAt(updated.disclaimer_accepted_at);
          setIsDisclaimerModalOpen(false);
        }}
        onClose={() => {
          if (disclaimerAccepted) {
            setIsDisclaimerModalOpen(false);
          }
        }}
      />
    </div>
  );
}
