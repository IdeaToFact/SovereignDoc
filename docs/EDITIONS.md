# SovereignDoc Product Editions & Tier Strategy (`docs/EDITIONS.md`)

This document defines the canonical feature boundary across **SovereignDoc Community Edition (AGPLv3)** and **Commercial Editions (Pro & Enterprise)** stewarded by **Idea To Fact LLC**.

---

## 🏛️ Feature Comparison Matrix

| Capability Category | AGPLv3 Community Edition<br>*(Open-Core / Self-Hosted)* | Commercial Pro Edition<br>*(Professional & Boutique Firms)* | Commercial Enterprise Edition<br>*(Corporate Legal & Regulated Enclaves)* |
| :--- | :---: | :---: | :---: |
| **Licensing** | GNU AGPLv3 (Strict Copyleft) | Commercial EULA / Subscription | Commercial Master Services Agreement (MSA) |
| **Deployment Model** | Local Host OS / Docker BYOO | Local Workstation / Secure VM | Dedicated Appliance / Air-Gapped K8s Enclave |
| **Telemetry & Networking** | 100% Local / Zero Remote Telemetry | 100% Local / Offline-Activated License | 100% Local / Air-Gapped License Token |
| **Document Ingestion** | PDF, DOCX, TXT, Markdown | Scanned PDF OCR & Bates Stamping | Multi-format Batch Ingestion Pipelines |
| **RAG & Grounding** | Local FastEmbed ONNX (BGE-small), ChromaDB, BM25, RRF Hybrid Fusion | Cross-Document Multi-Vault Search, Multi-Model Routing | Custom Domain Vector Embeddings & Fine-Tuned Local Ensembles |
| **Canvas Citation Viewer** | Split PDF & DOCX Clause Viewer, Bounding Box Coordinates `[x0,y0,x1,y1]` | Advanced Document Canvas with Interactive Clause Navigation | Cross-Document Citation Pinning & Visual Citation Graphs |
| **Contract Intelligence** | 7 Clause Families, 9 Deterministic Risk Rules, Obligations Register, Word Diff UI | Custom Playbook Builder, Risk Scoring Rule Editor, Suggested Counter-Clauses | Multi-Agent Contract Review Orchestration & Policy Enforcement |
| **Redline & Export** | Word-Level Clause Diff Viewer, Review Package (`.ZIP`) | **Track-Changes DOCX & Redlined PDF Export** | Custom Branded Executive PDF & Audit Reports |
| **Second Brain & Memory** | Markdown Notes, `[[WikiLinks]]`, Note History, 2D Knowledge Graph (D3 Force) | **GraphRAG** (`node_embedding` portfolio synthesis), Cross-Contract Entity Memory | Organization-Wide Knowledge Base & Multi-Vault Federation |
| **Administration & Security** | CLI & UI Air-Gap Auditor (`verify_airgap.py`), 25-Page Hardware Benchmark | Priority Email Support & Automated Security Updates | SSO/SAML, Role-Based Access Control (RBAC), Audit Logging Supporting Customer SOC 2 / HIPAA Programs |

---

## 🔒 Open-Core Governance & Relicensing Guarantee

1. **Permanence of Released Community Code**: Features released under the GNU AGPLv3 in this repository will remain permanently open source under the AGPLv3 for those published versions. Idea To Fact LLC will never revoke or retroactively relicense published open-source releases, while reserving full discretion to refactor, deprecate, or evolve future architectures and develop proprietary Commercial Editions.
2. **Direction of Code Movement**: Features may be moved from Commercial editions *down* into the Community Edition over time, but published capabilities of a tagged Community Edition release will never be retroactively stripped of their AGPLv3 license for that release.
3. **Plugin Architecture & Copyleft Boundary**:
   - The SovereignDoc Plugin SDK ([`packages/contract_intelligence/plugin_sdk/`](../packages/contract_intelligence/plugin_sdk/)) defines the capability registry (`CapabilityRegistry`) and rule base classes (`RiskRule`) for internal single-organization extensibility and future Commercial Pro Plugin Modules.
   - Private internal customizations run solely within a single organization without distribution or remote network exposure remain permissible under AGPLv3 §2. Independent external applications communicating at arm's length via documented HTTP/CLI/export interfaces are separate works.
   - Any modified version of SovereignDoc, derivative work or plugin combined and distributed with SovereignDoc core, or network-hosted service providing SovereignDoc functionality remotely (AGPLv3 §13) remains strictly governed by the GNU AGPLv3 unless licensed under a separate Commercial License from Idea To Fact LLC.
4. **Commercial Code Repository**: Commercial Pro and Enterprise components are developed, packaged, and distributed from a separate, private repository (`sovereigndoc-commercial`) under proprietary commercial terms (see [`docs/commercial/COMMERCIAL_TERMS_FRAMEWORK.md`](commercial/COMMERCIAL_TERMS_FRAMEWORK.md)).

---

## 🛡️ Compliance Support Statement

SovereignDoc is local-first software. **Software itself cannot be "HIPAA certified", and SOC 2 is an independent auditor's report regarding an organization's internal controls.** Community Edition includes no compliance certifications or contractual warranties (see [`DISCLAIMER.md`](../DISCLAIMER.md)). *(SovereignDoc and Idea To Fact LLC are not a law firm, CPA firm, HIPAA assessor, or regulatory authority, and are not affiliated with, sponsored by, or endorsed by the AICPA, HHS, or any state bar.)*

The Commercial Enterprise Edition provides:
- Comprehensive immutable local audit trails
- Cryptographic provenance export packages
- Role-based access controls and authentication integration

These technical and administrative capabilities are designed to **support our customers' internal compliance programs**, enabling enterprise legal teams to satisfy their obligations under SOC 2 (Security, Availability, Confidentiality), HIPAA, and state bar data-protection guidelines. Customers remain solely responsible for independent legal and regulatory compliance (see [`docs/commercial/COMMERCIAL_TERMS_FRAMEWORK.md`](commercial/COMMERCIAL_TERMS_FRAMEWORK.md)).

---

## 📬 Commercial Licensing Inquiries

For commercial pricing, custom enterprise evaluation licenses, or bespoke playbook development:
- **Idea To Fact LLC**
- Website: `https://ideatofact.com`
- Email: `licensing@ideatofact.com`

