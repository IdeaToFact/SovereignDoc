# Changelog

All notable changes to **SovereignDoc (AGPLv3 Community Edition)** by **Idea To Fact LLC** are documented in this file. Commercial Pro and Enterprise capabilities are maintained and versioned separately under commercial license agreements.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0-community] — 2026-11-15 — Initial Open-Source Release

This is the initial open-source release of **SovereignDoc Community Edition**, a 100% locally air-gapped legal AI second brain and contract intelligence workstation developed by **Idea To Fact LLC**.

### Core Platform & Local Air-Gap Architecture
- **Bring Your Own Ollama (BYOO) Architecture**: Connects to the host's native Ollama runtime (`http://host.docker.internal:11434` in Docker, `http://localhost:11434` locally) for frictionless GPU acceleration (CUDA, Metal, ROCm) and open-weights model selection (Llama 3.2, Qwen 2.5, Mistral).
- **Strict Host Loopback Isolation**: Network bindings are restricted to `127.0.0.1:8000` (FastAPI backend) and `127.0.0.1:5173` (React frontend), with zero exposure to external LAN or WAN networks.
- **Multi-Layer Egress Guard & Air-Gap Auditor (`verify_airgap.py`)**: Intercepts socket calls (`socket.connect`, `socket.create_connection`) and HTTP client requests (`httpx`, `aiohttp`, `requests`, `urllib`), enforcing zero external network requests and verifying telemetry lockdown (`ANONYMIZED_TELEMETRY=False`, `DO_NOT_TRACK=1`, `HF_HUB_DISABLE_TELEMETRY=1`).
- **Fail-Closed Offline Defaults**: Configured with `HF_HUB_OFFLINE=1` and `local_files_only=True` to guarantee zero calls to Hugging Face or third-party cloud services at runtime.
- **Local Isolated Storage Layout**: All metadata, document chunks, chat history, and notes reside in local isolated storage (`~/.sovereigndoc/db/metadata.db` SQLite database and `~/.sovereigndoc/db/chroma/` vector store). Data is stored plaintext at rest with recommendations for OS-level Full-Disk Encryption (BitLocker, FileVault, LUKS).

### Clean-Room Document Ingestion & Geometry
- **Clean-Room PDF Engine (`pypdfium2` as Default)**: Pluggable PDF parser defaulting to Apache-2.0 / BSD-3-Clause `pypdfium2` across all editions, with PyMuPDF retained as an optional fallback in Community Edition and prohibited in commercial builds.
- **2-Stage Line & Paragraph Clustering**: Converts PDF geometry into clean canvas bounding boxes: Stage 1 groups intra-line character runs and styled spans horizontally; Stage 2 clusters lines into cohesive paragraph-level clause blocks to ensure citation highlights encompass entire legal provisions.
- **Synthetic Multi-Format Pagination & Clause Detection**: Synchronizes synthetic page boundaries (3,000 characters per page) across Microsoft Word (DOCX) and PDF text layers, preventing citation drift between chat responses and the document viewer.

### Local Hybrid RAG Retrieval Engine
- **Dense & Sparse Hybrid Search**: Merges lexical keyword precision (SQLite FTS5 / BM25Okapi) with dense semantic understanding (ChromaDB + FastEmbed ONNX `BAAI/bge-small-en-v1.5`) via Reciprocal Rank Fusion (RRF $k=60$).
- **Cross-Encoder Neural Reranking**: Locally reranks top candidates using Xenova's `ms-marco-MiniLM-L-6-v2` ONNX model for high precision.
- **Document-Level Pre-Filtering (`document_id` Scoping)**: Pre-filters retrieval candidates at both the ChromaDB vector level (`where={"document_id": doc_id}`) and BM25 candidate index level, eliminating candidate starvation in multi-document vaults and guaranteeing top-k evidence extraction from the active document.
- **Sequential Chunk Context Window Expansion**: Links chunks sequentially (`previous_chunk_id`, `next_chunk_id`) to reconstruct surrounding contractual context on demand.

### Contract Intelligence & Deterministic Risk Radar
- **7 Core Standardized Legal Clause Categories**: Classifies clauses into essential commercial contract families: `INDEMNIFICATION`, `LIMITATION_OF_LIABILITY`, `TERMINATION`, `CONFIDENTIALITY`, `INTELLECTUAL_PROPERTY`, `PAYMENT_TERMS`, and `GOVERNING_LAW`.
- **9 Deterministic Risk Rules**: Rule-based contract risk analysis engine detecting `UNCAPPED_LIABILITY`, `ONE_SIDED_INDEMNITY`, `MISSING_CAP`, `SHORT_NOTICE`, `EVERGREEN`, `FOREIGN_JURISDICTION`, `AUDIT_AND_RECORDS_EXPOSURE`, `RESTRICTIVE_COVENANT_AND_IP`, and `OPERATIONAL_COVENANTS`.
- **Affirmative Duties & SLA Extractor**: Multi-chunk stitched extractor parsing Vendor, Customer, and Mutual duties with parenthetical written deadlines (`fifteen (15) business days`).
- **Versioned Review Runs**: Non-destructive `ReviewRun` history records (`Review 1`, `Review 2`, `Review 3`) preserving audit trails across successive contract revisions.

### Grounded Conversational Reviewer
- **Free-Form Manual Inquiries & Preset Audit Recipes**: Supports custom open-ended questions alongside 4 pre-built legal audit recipes (*Obligations & Deadlines*, *Liability & Indemnity*, *Termination Triggers*, *Executive Briefing*).
- **Sub-Pixel Canvas Navigation**: Interactive `[📄 Source X]` citation tags jump directly to the referenced page and highlight exact paragraph coordinates in the document viewer.
- **Dual-Layer UPL Guard**: Combines Layer 1 system prompt grounding with Layer 2 deterministic application-level detection to append non-legal-advice notices whenever users seek subjective legal opinions.

### Second Brain Legal Knowledge Graph & Notes
- **7-Entity Grounded Knowledge Graph**: Interactive SVG graph mapping `Document`, `ReviewRun`, `ClauseCategory`, `Risk`, `Obligation`, `Note`, and `Tag` with 100% provenance back to SQLite records.
- **Current State vs. Timeline View**: Default `🎯 Current State` isolates the latest review run to eliminate graph clutter while preserving `📚 Review Timeline` for complete audit history.
- **Clause Category Isolation & Zoom LOD**: Dynamic filtering by clause family, interactive slide-out inspector drawer, and camera zoom level-of-detail label culling.
- **Personal Matter Notes**: Local Markdown workspace with bi-directional `[[WikiLinks]]`, automatic immutable version snapshots (`NoteVersion`), and one-click `[📌 Save to Note]` citation capture.

### Governance, Security & Licensing
- **Open-Source License**: Released under GNU Affero General Public License v3.0 (AGPL-3.0-only).
- **Contributor License Agreement**: CLA v1.0 designating the State of Arizona, United States, as governing law and venue.
- **Comprehensive Verification Suite**: 44 modular domain test suites under `backend/tests/` covering air-gap security, PDF parity, RAG retrieval, clause classification, risk engine, and hardware profiling.
- **Air-Gap Verification CLI & Diagnostics**: Integrated `verify_airgap.py` and `benchmark_hardware.py` CLI tools with in-UI diagnostic modals.

