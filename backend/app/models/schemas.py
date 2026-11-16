# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# --- System & Hardware Schemas ---

class HardwareProfileResponse(BaseModel):
    os: str
    architecture: str
    cpu: Dict[str, int]
    ram: Dict[str, float]
    accelerator: Dict[str, Any]
    capability_profile: Dict[str, Any]


class SystemCapabilitiesResponse(BaseModel):
    cpu: bool = True
    cuda: bool
    metal: bool
    ollama: bool
    airgap: bool = True
    pdf_support: bool = True
    embeddings: bool = True


# --- Model Management Schemas ---

class ModelMetadata(BaseModel):
    name: str
    size_gb: float
    modified_at: str
    family: Optional[str] = None
    compatible: bool = True
    recommended: bool = False
    performance_class: str = "Good"


class ModelListResponse(BaseModel):
    provider: str
    status: str
    active_model: Optional[str] = None
    models: List[ModelMetadata] = []


class SelectModelRequest(BaseModel):
    model_name: str


class TestPromptRequest(BaseModel):
    prompt: str = Field(default="Hello! Verify you are running 100% locally on this machine.")


class TestPromptResponse(BaseModel):
    model: str
    response: str
    tokens_generated: int
    eval_duration_seconds: float
    tokens_per_second: float
    status: str = "success"


# --- Vault Schemas ---

class VaultCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class VaultResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    document_count: int = 0
    total_chunks: int = 0
    size_mb: float = 0.0
    created_at: datetime
    updated_at: datetime


# --- Document & Job Schemas ---

class DocumentResponse(BaseModel):
    id: str
    vault_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    file_path: Optional[str] = None
    checksum_sha256: str
    page_count: int
    chunk_count: int
    created_at: datetime


class IngestionJobResponse(BaseModel):
    id: str
    vault_id: str
    document_id: str
    filename: str
    status: str
    error_message: Optional[str] = None
    progress_pct: int
    processing_time_ms: int
    chunks_generated: int
    embeddings_generated: int
    created_at: datetime
    completed_at: Optional[datetime] = None


# --- Chunk & Query Schemas ---

class ChunkDetail(BaseModel):
    id: str
    document_id: str
    vault_id: str
    chunk_index: int
    previous_chunk_id: Optional[str] = None
    next_chunk_id: Optional[str] = None
    parent_chunk_id: Optional[str] = None
    page_number: int
    article: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    bbox: Optional[List[float]] = None
    section_title: Optional[str] = None
    text: str
    char_length: int
    token_count: int


class HybridQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    document_id: Optional[str] = Field(default=None)
    top_k: int = Field(default=5, ge=1, le=50)
    mode: str = Field(default="hybrid")  # hybrid, dense_only, keyword_only
    enable_reranker: bool = Field(default=True)
    expand_window: bool = Field(default=False)  # pulls surrounding previous/next chunks


class HybridQueryResultItem(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    chunk_index: int
    page_number: int
    article: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    bbox: Optional[List[float]] = None
    section_title: Optional[str] = None
    snippet: str
    expanded_context: Optional[str] = None
    score: float
    retrieval_stage: str  # dense, sparse, rrf, reranked


class HybridQueryResponse(BaseModel):
    query: str
    vault_id: str
    mode: str
    reranked: bool
    results: List[HybridQueryResultItem]


# --- Milestone 3: Evidence, Chat & Persistence Schemas ---

class EvidenceObject(BaseModel):
    citation_id: str
    document_id: str
    filename: str
    page_number: int
    bbox: Optional[List[float]] = None
    article: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    clause_title: Optional[str] = None
    evidence_text: str
    surrounding_context: Optional[str] = None
    confidence: float
    rerank_score: float


class ChatStreamRequest(BaseModel):
    query: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    document_id: Optional[str] = None
    model_name: Optional[str] = None
    mode: str = Field(default="hybrid")
    enable_reranker: bool = Field(default=True)
    top_k: int = Field(default=5, ge=1, le=20)
    expand_window: bool = Field(default=True)
    recipe: Optional[str] = None  # obligations, liability, termination, executive


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    evidence: List[EvidenceObject] = []
    tokens_generated: int = 0
    tokens_per_second: float = 0.0
    created_at: datetime


class ChatSessionCreateRequest(BaseModel):
    title: Optional[str] = "New Analysis"
    document_id: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: str
    vault_id: str
    document_id: Optional[str] = None
    document_filename: Optional[str] = None
    title: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class WorkspaceStateRequest(BaseModel):
    active_vault_id: Optional[str] = None
    active_document_id: Optional[str] = None
    active_model: Optional[str] = None
    active_session_id: Optional[str] = None
    sidebar_collapsed: bool = False
    accepted_disclaimer_version: Optional[str] = None


class WorkspaceStateResponse(BaseModel):
    id: str
    active_vault_id: Optional[str] = None
    active_document_id: Optional[str] = None
    active_model: Optional[str] = None
    active_session_id: Optional[str] = None
    sidebar_collapsed: bool = False
    current_disclaimer_version: str = "1.1"
    accepted_disclaimer_version: Optional[str] = None
    disclaimer_accepted: bool = False
    disclaimer_accepted_at: Optional[datetime] = None
    updated_at: datetime


# --- Milestone 5: Personal Second Brain & Grounded Knowledge Graph Schemas ---

class NoteCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content_md: str = Field(default="")
    document_id: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    pinned: bool = False
    summary: Optional[str] = None


class NoteUpdateRequest(BaseModel):
    title: Optional[str] = None
    content_md: Optional[str] = None
    document_id: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    pinned: Optional[bool] = None
    summary: Optional[str] = None


class NoteVersionResponse(BaseModel):
    id: str
    note_id: str
    version_number: int
    title: str
    content_md: str
    summary: Optional[str] = None
    created_at: datetime


class NoteLinkItemResponse(BaseModel):
    id: str
    source_note_id: str
    source_note_title: Optional[str] = None
    target_note_id: Optional[str] = None
    target_note_title: Optional[str] = None
    target_doc_id: Optional[str] = None
    target_doc_filename: Optional[str] = None
    target_risk_id: Optional[str] = None
    target_obligation_id: Optional[str] = None
    target_page: Optional[int] = None
    link_text: str
    link_type: str
    created_at: datetime


class NoteResponse(BaseModel):
    id: str
    vault_id: str
    document_id: Optional[str] = None
    document_filename: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    title: str
    content_md: str
    tags: List[str] = []
    current_version: int = 1
    pinned: bool = False
    outgoing_links_count: int = 0
    backlinks_count: int = 0
    links_out: List[NoteLinkItemResponse] = []
    backlinks: List[NoteLinkItemResponse] = []
    created_at: datetime
    updated_at: datetime


class QuickCaptureRequest(BaseModel):
    note_id: Optional[str] = None
    note_title: Optional[str] = None
    document_id: Optional[str] = None
    filename: Optional[str] = None
    page_number: Optional[int] = 1
    section: Optional[str] = None
    clause_title: Optional[str] = None
    verbatim_text: str = Field(..., min_length=1)
    commentary: Optional[str] = None
    source_type: str = Field(default="EVIDENCE")  # EVIDENCE | RISK | OBLIGATION
    risk_id: Optional[str] = None
    risk_level: Optional[str] = None
    rule_id: Optional[str] = None
    obligation_id: Optional[str] = None
    party: Optional[str] = None
    deadline: Optional[str] = None
    tags: List[str] = []


class GraphNodeItem(BaseModel):
    id: str
    vault_id: str
    entity_type: str
    entity_id: str
    label: str
    metadata: Dict[str, Any] = {}
    graph_version: str = "1.0.0"


class GraphEdgeItem(BaseModel):
    id: str
    vault_id: str
    source_id: str
    target_id: str
    edge_type: str
    label: Optional[str] = None
    weight: float = 1.0
    graph_version: str = "1.0.0"


class GraphStats(BaseModel):
    documents: int = 0
    review_runs: int = 0
    clause_categories: int = 0
    risks: int = 0
    obligations: int = 0
    notes: int = 0
    tags: int = 0
    total_nodes: int = 0
    total_edges: int = 0


class KnowledgeGraphResponse(BaseModel):
    vault_id: str
    graph_version: str = "1.0.0"
    stats: GraphStats
    matched_node_ids: List[str] = []
    nodes: List[GraphNodeItem] = []
    edges: List[GraphEdgeItem] = []

