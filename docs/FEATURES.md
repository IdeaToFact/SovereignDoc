# SovereignDoc Feature Matrix & System Capabilities

**SovereignDoc (`v1.1.0-community`)** is an air-gapped, zero-telemetry, local AI document intelligence and legal knowledge workstation built on the **AirGap Axis Platform** by **Idea To Fact LLC**.

This document outlines the core technical capabilities, legal intelligence features, and architecture boundaries of the **AGPLv3 Community Edition** alongside the upgrade path for future commercial tiers.

---

## 1. High-Level Capabilities Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SOVEREIGNDOC CORE CAPABILITIES                        │
├──────────────────────────────┬──────────────────────────────┬───────────────┤
│    LOCAL AI & RAG ENGINE     │   LEGAL AUDIT INTELLIGENCE   │ 2D SECOND BRAIN│
├──────────────────────────────┼──────────────────────────────┼───────────────┤
│ • Local FastEmbed ONNX Engine│ • 7 Core Legal Clause Classes│ • 7-Entity Graph│
│ • Cross-Encoder Reranker     │ • Rule-Based Risk Matrix     │ • Current vs  │
│ • Hybrid BM25 + Vector Search│ • Affirmative Duty Extractor │   Timeline    │
│ • Ollama GGUF Local LLM Stream│ • SLA & Parenthetical Deadlines│ • Clause Focus│
│ • Dual-Layer UPL Safety Guard│ • Side-by-Side Redline Diff  │ • Hover Cards │
│ • MultiLayer Egress Auditor  │ • Parser-Safe .ZIP Export    │ • Side Drawer │
└──────────────────────────────┴──────────────────────────────┴───────────────┘
```

---

## 2. Deep Feature Breakdown

### 2.1 Core AI & Local Retrieval-Augmented Generation (RAG)
- **100% Local Inference**: Zero calls to OpenAI, Anthropic, or external cloud endpoints. Local LLM inference executes via your host's native Ollama runtime (supporting Llama 3.2, Qwen 2.5, Mistral, and any open-weights GGUF model).
- **Two-Stage Hybrid Search**: Combines lexical keyword precision (SQLite FTS5 / BM25Okapi) with dense semantic understanding (ChromaDB + FastEmbed ONNX `BAAI/bge-small-en-v1.5`) merged via Reciprocal Rank Fusion ($k=60$).
- **Document-Level Pre-Filtering (`document_id` Scoping)**: When reviewing an active contract, the retrieval engine applies pre-filtering directly at the vector store (`where={"document_id": id}`) and BM25 candidate index levels. This eliminates multi-document candidate starvation in multi-contract vaults, ensuring the top-k evidence blocks are guaranteed to come from the contract being analyzed. When no document is focused, queries seamlessly pool across all vault documents.
- **Cross-Encoder Neural Reranking**: Re-scores top-k hybrid search results using Xenova's `ms-marco-MiniLM-L-6-v2` ONNX model running locally on ONNX Runtime for maximal context precision.
- **Flexible Natural Language Queries & Audit Recipes**: Supports both free-form, open-ended legal questions (e.g., custom queries about parties, governing law, specific dates, or section numbers) and one-click standardized audit prompt recipes (*Obligations & Deadlines*, *Liability & Indemnity*, *Termination Triggers*, and *Executive Briefing*).
- **Sequential Chunk Window Expansion**: Every chunk preserves `previous_chunk_id` and `next_chunk_id` pointers, allowing the RAG pipeline to reconstruct surrounding context without re-querying vector storage.
- **Dual-Layer Conversational UPL Guard**:
  - **Layer 1 (System Prompt Directive)**: Enforces objective legal contract analysis and factual extraction.
  - **Layer 2 (Deterministic Application Guard)**: Detects legal-advice requests (e.g. *"Should I sign this?"*, *"Am I liable?"*) with zero latency and appends mandatory non-legal-advice disclaimers to live SSE streams and database transcripts.

### 2.2 Document Processing & Contract Intelligence
- **Multi-Format Ingestion**: Ingests legal contracts in PDF and Microsoft Word (DOCX) formats with zero cloud dependencies. Defaults to clean-room `pypdfium2` (Apache-2.0 / BSD-3-Clause) powered by a 2-stage horizontal line assembly and paragraph clustering engine that extracts full paragraph-level bounding boxes `[x0, y0, x1, y1]`, ensuring citations highlight complete legal clauses rather than fractured word slivers. PyMuPDF is retained as an optional fallback in Community Edition.
- **Synthetic Multi-Format Pagination**: Synchronizes synthetic page boundaries (`3,000` characters per page) across Word documents and PDF text layers, eliminating citation drift between the chat assistant and document viewer.
- **7 Core Standardized Legal Clause Categories**:
  - Automatically identifies and classifies the essential commercial contract clause families: `INDEMNIFICATION`, `LIMITATION_OF_LIABILITY`, `TERMINATION`, `CONFIDENTIALITY`, `INTELLECTUAL_PROPERTY`, `PAYMENT_TERMS`, and `GOVERNING_LAW`.
  - Inspection, Books & Records, and Audit covenants are evaluated under `CONFIDENTIALITY` via the `AUDIT_AND_RECORDS_EXPOSURE` rule and parsed into affirmative obligations by the obligations extractor.
  - *(Commercial Pro and Enterprise editions expand this to a 30+ category custom corporate legal taxonomy).*
- **Deterministic Risk Radar**:
  - Rule-based risk audit matrix (`RiskRule` ABC) with 9 built-in deterministic rules scoring risks as `HIGH`, `MEDIUM`, or `LOW`.
  - Flags missing liability caps, unilateral indemnities, foreign dispute venues, short turnaround windows, unannounced audit obligations, and unlimited record inspection demands.
- **Affirmative Duties & SLA Extractor**:
  - Evaluates sliding 5-chunk section windows to detect contractual duties across `VENDOR`, `CUSTOMER`, and `MUTUAL` parties.
  - Parses numeric, spelled-out, and parenthetical written deadlines (e.g. *"within fifteen (15) business days"*).
- **Side-by-Side Redline Diff**:
  - Longest Common Subsequence (LCS) word-level diffing between contract versions with visual insertions, deletions, and structural alignment.
- **Deliverable Review Package (.ZIP)**:
  - Generates RFC-4180 parser-safe `.zip` export containing `contract_audit.md`, `risk_matrix.csv`, `obligations.csv`, and `DISCLAIMER.txt`.

### 2.3 Second Brain Legal Knowledge Graph
- **7-Entity Grounded Graph**:
  - Automatically maps relationships across: `DOCUMENT`, `REVIEW_RUN`, `CLAUSE_CATEGORY`, `RISK`, `OBLIGATION`, `NOTE`, and `TAG`.
- **Current State vs. Timeline Decoupling**:
  - `[ 🎯 Current State ]`: Isolates the active legal truth of the document (latest review run only), instantly eliminating 60–80% of perceived graph clutter.
  - `[ 📚 Review Timeline ]`: Allows attorneys to inspect historical audit progression across multiple runs.
- **Clause Category Isolation**:
  - Single-click clause pills (`Confidentiality (incl. Audit & Records)`, `Termination`, `Limitation of Liability`) collapse the graph into a laser-focused **3 to 5 node cluster**. *(Audit and inspection covenants are evaluated and filtered under Confidentiality).*
- **Zero-Click Hover Cards**:
  - Floating glass tooltips displaying entity badge, title, severity/party, explicit deadlines, and instant verbatim excerpts.
- **Slide-Out Inspector Drawer (`GraphInspectorDrawer.jsx`)**:
  - 420px slide-out drawer providing structured risk/obligation breakdowns, syntax-highlighted verbatim quotes with **[📋 Copy Citation]**, connected neighbor breadcrumbs, **[📄 Open in Contract Viewer]** (page-level jump), and **[📝 Pin to Active Note]**.
- **Level-of-Detail (LOD) Zoom Labels**:
  - Culls leaf labels when zoomed out and displays full text upon zoom or hover, eliminating label overlapping and font clumping.
- **Personal Matter Notes & Backlinking**:
  - Markdown note editor with immutable version history (`NoteVersion` snapshots), bi-directional `[[WikiLinks]]`, automatic `#tag` indexing, and one-click citation capture.

### 2.4 Security & Air-Gap Compliance
- **Zero External Sockets**: No external network requests during document analysis, chat, RAG, or note editing. (Initial repo setup or container build requires internet access unless using pre-packaged offline bundles).
- **Pre-Baked ONNX Models (`HF_HUB_OFFLINE=1`)**: Embedding and cross-encoder models are pre-compiled into the image layer during build; no runtime downloads from Hugging Face.
- **Multi-Layer Egress Guard**: Automated verification script (`verify_airgap.py`) intercepting Python socket calls, HTTP clients (`urllib`, `requests`, `httpx`, `aiohttp`), and telemetry variables (`ANONYMIZED_TELEMETRY=False`, `DO_NOT_TRACK=1`).
- **Host Loopback Binding**: Containers bind strictly to `127.0.0.1:8000` and `127.0.0.1:5173`, preventing unauthorized LAN/WAN access.
- **Single Source of Truth**: All metadata, chunk content, chat history, and notes reside in a local SQLite database file (`~/.sovereigndoc/db/metadata.db`). Data is stored plaintext at rest; operating-system Full-Disk Encryption (BitLocker, FileVault, or LUKS) is strongly recommended for confidential matters.

---

## 3. Feature Matrix: Community vs. Commercial Pro vs. Enterprise

| Capability | **Community Edition (AGPLv3)** | **Commercial Pro Edition** | **Commercial Enterprise Edition** |
| :--- | :---: | :---: | :---: |
| **Deployment Model** | 100% Local (Docker / Python) | 100% Local / Workstation Pro | Local Air-Gapped / Private Cloud |
| **License** | GNU AGPLv3 | Commercial Proprietary | Commercial Enterprise |
| **Pricing** | Free & Open-Core | Annual Subscription per Seat | Custom Enterprise Agreement |
| **Contract Ingestion** | PDF & DOCX (Single Matter) | PDF, DOCX, Scanned OCR | Bulk Multi-Format Ingestion |
| **Clause Classification** | 7 Core Clause Families | 30+ Advanced Classes | Custom Firm Taxonomy |
| **Risk Scoring Engine** | 9 Built-In Deterministic Rules | Custom Rule Editor & Scoring | Firm-Wide Rule Governance |
| **Obligations Extractor** | Vendor / Customer / Mutual | Advanced Penalty & SLA Parser | Multi-Agreement Milestone Sync |
| **Review Runs** | Versioned Review History | Comparative Audit Benchmarks | Enterprise Portfolio Audit |
| **Knowledge Graph** | Single-Contract 7-Entity Graph | **Portfolio Knowledge Graph (500+)**| **Tenant-Wide Knowledge Graph** |
| **GraphRAG Capabilities** | Single-Document Context | **Cross-Contract GraphRAG Queries** | **Cross-Matter Intelligence Swarms** |
| **Entity Disambiguation** | Manual / Exact Name | **Automated AI Entity Merging** | **Enterprise Vendor Deduplication** |
| **Matter Notes** | Personal Second Brain (Local) | Playbook Sharing & Export | Team Collaborative Notes |
| **Redline Diffing** | Side-by-Side Word Diff | Suggested Counter-Clauses | AI Multi-Pass Redline Negotiation |
| **Team Management** | Single User | Single User Pro License | Multi-User RBAC & Org Vaults |
| **Security & Compliance** | Air-Gap Verified, Loopback | Air-Gap Verified, Export Logs | SAML 2.0 / SSO, Audit Logging for Customer SOC 2 Programs |

