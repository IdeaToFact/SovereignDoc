# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import datetime, timezone

from typing import List, Optional

from sqlalchemy import (

    String,

    Integer,

    Float,

    Boolean,

    Text,

    DateTime,

    ForeignKey,

    Index

)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base





def utc_now() -> datetime:

    return datetime.now(timezone.utc)





class Vault(Base):

    __tablename__ = 'vaults'



    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)



    documents: Mapped[List['Document']] = relationship('Document', back_populates='vault', cascade='all, delete-orphan')

    jobs: Mapped[List['IngestionJob']] = relationship('IngestionJob', back_populates='vault', cascade='all, delete-orphan')

    chunks: Mapped[List['Chunk']] = relationship('Chunk', back_populates='vault', cascade='all, delete-orphan')

    chat_sessions: Mapped[List['ChatSession']] = relationship('ChatSession', back_populates='vault', cascade='all, delete-orphan')





class Document(Base):

    __tablename__ = 'documents'



    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)

    vault_id: Mapped[str] = mapped_column(String, ForeignKey('vaults.id', ondelete='CASCADE'), nullable=False, index=True)

    filename: Mapped[str] = mapped_column(String, nullable=False)

    file_type: Mapped[str] = mapped_column(String, nullable=False)

    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    checksum_sha256: Mapped[str] = mapped_column(String, nullable=False, index=True)

    page_count: Mapped[int] = mapped_column(Integer, default=1)

    chunk_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)



    vault: Mapped['Vault'] = relationship('Vault', back_populates='documents')

    jobs: Mapped[List['IngestionJob']] = relationship('IngestionJob', back_populates='document', cascade='all, delete-orphan')

    chunks: Mapped[List['Chunk']] = relationship('Chunk', back_populates='document', cascade='all, delete-orphan')

    review_runs: Mapped[List['ReviewRun']] = relationship('ReviewRun', back_populates='document', cascade='all, delete-orphan')
    chat_sessions: Mapped[List['ChatSession']] = relationship('ChatSession', back_populates='document')



    __table_args__ = (

        Index('idx_doc_vault_checksum', 'vault_id', 'checksum_sha256'),

    )





class IngestionJob(Base):

    __tablename__ = 'ingestion_jobs'



    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)

    vault_id: Mapped[str] = mapped_column(String, ForeignKey('vaults.id', ondelete='CASCADE'), nullable=False, index=True)

    document_id: Mapped[str] = mapped_column(String, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)

    filename: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[str] = mapped_column(String, nullable=False, default='PENDING')

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    progress_pct: Mapped[int] = mapped_column(Integer, default=0)

    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0)

    chunks_generated: Mapped[int] = mapped_column(Integer, default=0)

    embeddings_generated: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)



    vault: Mapped['Vault'] = relationship('Vault', back_populates='jobs')

    document: Mapped['Document'] = relationship('Document', back_populates='jobs')





class Chunk(Base):

    __tablename__ = 'chunks'



    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)

    document_id: Mapped[str] = mapped_column(String, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)

    vault_id: Mapped[str] = mapped_column(String, ForeignKey('vaults.id', ondelete='CASCADE'), nullable=False, index=True)

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    previous_chunk_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    next_chunk_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    parent_chunk_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    page_number: Mapped[int] = mapped_column(Integer, nullable=False)

    article: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    section: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    subsection: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    bbox_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    section_title: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    char_length: Mapped[int] = mapped_column(Integer, nullable=False)

    token_count: Mapped[int] = mapped_column(Integer, nullable=False)



    vault: Mapped['Vault'] = relationship('Vault', back_populates='chunks')

    document: Mapped['Document'] = relationship('Document', back_populates='chunks')



    __table_args__ = (

        Index('idx_chunks_doc_idx', 'document_id', 'chunk_index'),

    )





class ChatSession(Base):

    __tablename__ = 'chat_sessions'



    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)

    vault_id: Mapped[str] = mapped_column(String, ForeignKey('vaults.id', ondelete='CASCADE'), nullable=False, index=True)

    document_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('documents.id', ondelete='SET NULL'), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String, nullable=False, default='New Analysis')

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)



    vault: Mapped['Vault'] = relationship('Vault', back_populates='chat_sessions')

    document: Mapped[Optional['Document']] = relationship('Document', back_populates='chat_sessions')

    messages: Mapped[List['ChatMessage']] = relationship('ChatMessage', back_populates='session', cascade='all, delete-orphan')



    __table_args__ = (

        Index('idx_chat_sessions_document_id', 'document_id'),

    )





class ChatMessage(Base):

    __tablename__ = 'chat_messages'



    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)

    session_id: Mapped[str] = mapped_column(String, ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False, index=True)

    role: Mapped[str] = mapped_column(String, nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    evidence_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tokens_generated: Mapped[int] = mapped_column(Integer, default=0)

    tokens_per_second: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)



    session: Mapped['ChatSession'] = relationship('ChatSession', back_populates='messages')





class WorkspaceState(Base):

    __tablename__ = 'workspace_state'



    id: Mapped[str] = mapped_column(String, primary_key=True, default='current_workspace')

    active_vault_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    active_document_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    active_model: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    active_session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    sidebar_collapsed: Mapped[bool] = mapped_column(Boolean, default=False)

    accepted_disclaimer_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    disclaimer_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)





# =============================================================================

# Milestone 4: Contract Intelligence & Legal Audit Models

# =============================================================================



class ReviewRun(Base):

    """Stores a versioned contract analysis execution."""

    __tablename__ = "review_runs"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    classifier_version: Mapped[str] = mapped_column(String(20), default="1.0.0")

    ruleset_version: Mapped[str] = mapped_column(String(20), default="1.0.0")

    total_risks: Mapped[int] = mapped_column(Integer, default=0)

    total_obligations: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(20), default="COMPLETED")  # PROCESSING, COMPLETED, FAILED



    document: Mapped["Document"] = relationship("Document", back_populates="review_runs")

    risks: Mapped[List["RiskAuditItem"]] = relationship("RiskAuditItem", back_populates="review_run", cascade="all, delete-orphan")

    obligations: Mapped[List["ObligationItem"]] = relationship("ObligationItem", back_populates="review_run", cascade="all, delete-orphan")





class ClauseClassification(Base):

    """Stores classified clauses for a document."""

    __tablename__ = "clause_classifications"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    chunk_id: Mapped[str] = mapped_column(String(36), ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False, index=True)

    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ClauseCategory enum value

    confidence: Mapped[float] = mapped_column(Float, default=0.90)

    detection_method: Mapped[str] = mapped_column(String(50), default="CLASSIFIER")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)





class RiskAuditItem(Base):

    """Stores identified risks for a document linked to a versioned ReviewRun."""

    __tablename__ = "risk_audits"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)

    review_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("review_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    rule_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    category: Mapped[str] = mapped_column(String(50), nullable=False)  # ClauseCategory enum value

    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # RiskLevel enum value

    issue_title: Mapped[str] = mapped_column(String(255), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    page_number: Mapped[int] = mapped_column(Integer, nullable=False)

    section: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    bbox_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    verbatim_text: Mapped[str] = mapped_column(Text, nullable=False)

    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    detection_method: Mapped[str] = mapped_column(String(50), default="RULE")  # DetectionMethod enum value

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)



    review_run: Mapped["ReviewRun"] = relationship("ReviewRun", back_populates="risks")





class ObligationItem(Base):

    """Stores extracted affirmative duties linked to a versioned ReviewRun."""

    __tablename__ = "obligations"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)

    review_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("review_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    party: Mapped[str] = mapped_column(String(50), nullable=False)  # ObligationParty enum value

    action_required: Mapped[str] = mapped_column(Text, nullable=False)

    trigger_or_condition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    deadline_or_cadence: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    page_number: Mapped[int] = mapped_column(Integer, nullable=False)

    section: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    bbox_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    verbatim_text: Mapped[str] = mapped_column(Text, nullable=False)

    confidence: Mapped[float] = mapped_column(Float, default=0.90)

    detection_method: Mapped[str] = mapped_column(String(50), default="HEURISTIC")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)



    review_run: Mapped["ReviewRun"] = relationship("ReviewRun", back_populates="obligations")





class ContractComparison(Base):

    """Stores comparison between two documents."""

    __tablename__ = "contract_comparisons"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)

    vault_id: Mapped[str] = mapped_column(String(36), ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False, index=True)

    doc_a_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    doc_b_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="COMPLETED")

    summary_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    diff_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


# =============================================================================
# Milestone 5: Personal Second Brain & Grounded Legal Knowledge Graph Models
# =============================================================================

class NoteRecord(Base):
    """Stores a local Markdown Second Brain note in SQLite."""
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    vault_id: Mapped[str] = mapped_column(String(36), ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    versions: Mapped[List["NoteVersion"]] = relationship("NoteVersion", back_populates="note", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_notes_vault_doc", "vault_id", "document_id"),
        Index("idx_notes_vault_title", "vault_id", "title"),
    )


class NoteVersion(Base):
    """Stores immutable historical snapshots of a NoteRecord for version history & non-destructive restore."""
    __tablename__ = "note_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    note_id: Mapped[str] = mapped_column(String(36), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    note: Mapped["NoteRecord"] = relationship("NoteRecord", back_populates="versions")


class NoteLink(Base):
    """Stores extracted bi-directional [[WikiLinks]] and pinned Risk/Obligation citations."""
    __tablename__ = "note_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    vault_id: Mapped[str] = mapped_column(String(36), ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False, index=True)
    source_note_id: Mapped[str] = mapped_column(String(36), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_note_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("notes.id", ondelete="SET NULL"), nullable=True, index=True)
    target_doc_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    target_risk_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("risk_audits.id", ondelete="SET NULL"), nullable=True, index=True)
    target_obligation_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("obligations.id", ondelete="SET NULL"), nullable=True, index=True)
    target_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    link_text: Mapped[str] = mapped_column(String(255), nullable=False)
    link_type: Mapped[str] = mapped_column(String(30), nullable=False, default="NOTE")  # GraphNodeType value: NOTE | DOCUMENT | RISK | OBLIGATION
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class GraphNode(Base):
    """Persisted Knowledge Graph Node in SQLite with stable (entity_type, entity_id) provenance."""
    __tablename__ = "graph_nodes"

    id: Mapped[str] = mapped_column(String(140), primary_key=True, index=True)
    vault_id: Mapped[str] = mapped_column(String(36), ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)  # GraphNodeType enum value
    entity_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)   # Source SQLite primary key / canonical ID
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    node_embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)       # Pro/Enterprise GraphRAG forward-compatibility hook (NULL in Community)
    graph_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("idx_graph_nodes_vault_entity", "vault_id", "entity_type", "entity_id"),
    )


class GraphEdge(Base):
    """Persisted Knowledge Graph Edge in SQLite typed with GraphEdgeType."""
    __tablename__ = "graph_edges"

    id: Mapped[str] = mapped_column(String(180), primary_key=True, index=True)
    vault_id: Mapped[str] = mapped_column(String(36), ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    edge_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # GraphEdgeType enum value
    label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # Pro/Enterprise GraphRAG edge context hook
    graph_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


