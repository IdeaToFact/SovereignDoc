# SovereignDoc Community Roadmap & Product Scope Boundaries

## 1. Guiding Strategic Framework

> [!NOTE]
> This roadmap reflects current Community Edition product direction and is provided for informational planning only. It is not a binding commitment; **Idea To Fact LLC** reserves full discretion to reprioritize, modify, defer, or allocate capabilities across Community and Commercial Editions.

SovereignDoc is developed under an **Open-Core** governance model by **Idea To Fact LLC**. To ensure complete transparency with our community contributors, enterprise users, and legal tech partners, we evaluate every prospective feature through a strict two-part lens:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       COMMUNITY VS. COMMERCIAL LENS                         │
├──────────────────────────────────────────────┬──────────────────────────────┤
│        COMMUNITY EDITION (GNU AGPLv3)        │    COMMERCIAL PRO / ENT      │
├──────────────────────────────────────────────┼──────────────────────────────┤
│ "Does this improve understanding, legibility,│ "Does this generate new      │
│  or navigation of information already owned  │  intelligence, cross-matter  │
│  by the user within a single agreement?"     │  synthesis, or portfolio-wide│
│                                              │  insights across contracts?" │
│                                              │                              │
│ 🎯 Single-contract legal workstation         │ 🏢 Multi-contract portfolio  │
│ 🎯 Zero-cost, locally air-gapped forever     │ 🏢 Enterprise intelligence   │
└──────────────────────────────────────────────┴──────────────────────────────┘
```

- **Community Rule**: Core usability, graph hygiene, clutter reduction, local air-gap security, deterministic parsing, single-contract review, and note-taking belong strictly in the **Community Edition**. The free edition must never feel intentionally hobbled or broken.
- **Commercial Boundary**: Multi-contract portfolio intelligence, GraphRAG across hundreds of agreements, automated entity deduplication, cross-document precedent matching, and organizational team governance form the commercial tiers.

---

## 2. Current Release Status (`v1.1.0-community`)

| Capability Area | Status | Feature Summary |
| :--- | :---: | :--- |
| **Local RAG & Inference** | ✅ Live | 100% offline FastEmbed ONNX (`bge-small-en-v1.5`), Cross-Encoder reranking (`ms-marco-MiniLM-L-6-v2`), SQLite FTS5 BM25, and local Ollama GGUF inference. |
| **Clause Classification** | ✅ Live | 7 Core Legal Clause Categories (Indemnification, Limitation of Liability, Termination, Confidentiality, Intellectual Property, Payment Terms, Governing Law) with integrated Books & Records / Audit covenant analysis. |
| **Deterministic Risk Engine** | ✅ Live | Rule-based risk audit matrix (`RiskRule` ABC) with confidence scoring, legal justification, and issue explainability. |
| **Affirmative Duties & SLAs** | ✅ Live | Multi-chunk stitched extractor parsing Vendor, Customer, and Mutual duties with parenthetical written deadlines (`fifteen (15) business days`). |
| **Dual-Layer UPL Guard** | ✅ Live | Layer 1 System Directive + Layer 2 deterministic application-layer notice preventing unauthorized practice of law. |
| **Second Brain Knowledge Graph** | ✅ Live | 7-Entity grounded graph, `[🎯 Current State]` vs `[📚 Timeline]` toggle, Clause Category Isolation, hover cards, slide-out drawer, and zoom LOD labels. |
| **Personal Matter Notes** | ✅ Live | Markdown editor with immutable version history (`NoteVersion`), bi-directional `[[WikiLinks]]`, and one-click citation pinning. |
| **Air-Gap Verification** | ✅ Live | `MultiLayerEgressGuard` zero-socket audit, pre-baked ONNX Docker packaging, and loopback binding (`127.0.0.1`). |

---

## 3. Community Edition Roadmap (v1.2 – v2.0)

The Community Edition focuses on deepening the single-contract legal intelligence workstation:

### Next Release (v1.2): Advanced Single-Document Legal Rules & Export
- **Expanded Heuristic Risk Rule Pack**:
  - `AntiAssignmentRule`: Flags restrictions on assigning rights during corporate restructuring, financing, or M&A.
  - `DataBreachNotificationRule`: Detects and flags aggressive 24-hour or 48-hour incident reporting SLAs.
  - `SourceCodeEscrowRule`: Flags absence of software escrow release triggers in enterprise licensing agreements.
  - `MostFavoredNationRule`: Highlights pricing commitments and benchmarking obligations.
- **Client-Side PDF Redline & Report Generation**:
  - Export audit summaries and redlines directly to styled PDF with table of contents and severity heatmaps.
- **Enhanced Clause Isolation**:
  - Direct deep-linking from chat citations into isolated clause micro-graphs.

### Future Capabilities (v1.3): Interactive Clause Scratchpad & Prompt Templates
- **Interactive Clause Scratchpad**:
  - In-viewer draft revision area for testing proposed counter-language against single-document context.
- **Single-Matter Prompt Library**:
  - Pre-packaged prompt buttons tailored for specific legal matters (e.g., *"Summarize Indemnity Carve-Outs"*, *"List All Termination for Convenience Triggers"*, *"Audit Insurance Endorsements"*).
- **Semantic UPL Intent Classification**:
  - Secondary classification pass for ambiguous legal advice queries without adding runtime latency to streaming tokens.

### Long-Term Vision (v2.0): Community Plugin Ecosystem
- **Community Risk Rule Plugin SDK**:
  - Formalized Python plugin specification allowing community legal engineers to publish custom `RiskRule` and `ClauseClassifier` modules.
- **Custom Theme Engine**:
  - User-configurable high-contrast and light terminal themes for legal readability.

---

## 4. Product Scope Boundary (Community vs. Commercial)

SovereignDoc Community Edition is intentionally designed and optimized as a **single-document legal workstation**. All single-contract analysis, risk auditing, affirmative SLA extraction, and knowledge graph navigation are 100% free, open-source under GNU AGPLv3, and locally air-gapped forever.

Capabilities that operate **across multi-contract enterprise portfolios**—such as cross-agreement semantic search, portfolio-wide conflict detection, and enterprise organization governance—are part of our commercial offerings via **AirGap Axis**.

For enterprise inquiries, custom legal rulesets, or commercial licensing, please visit [airgapaxis.com](https://airgapaxis.com).

---

## 5. Contributing to the Roadmap

We welcome pull requests and feature proposals that advance the **Community Edition** goals!
- To propose a new single-document rule or parser improvement, open an issue labeled `enhancement:community`.
- Read [`CONTRIBUTING.md`](../CONTRIBUTING.md) for code formatting, testing standards, and pull request procedures.

