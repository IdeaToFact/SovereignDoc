# SovereignDoc Community Edition (`v1.1.0-community`)
### Local-First AI Document Intelligence & Second Brain
**Idea To Fact LLC** → **AirGap Axis Platform** → **SovereignDoc Community Edition**

**SovereignDoc** is an open-core, local-first AI Document Intelligence and Second Brain workstation built on the **AirGap Axis Platform** by **Idea To Fact LLC**. All document indexing, vector retrieval, deterministic contract review, obligations tracking, research note-taking, and interactive knowledge graphs run directly on your own machine with zero remote cloud dependencies and zero telemetry by default.

---

## 🔒 Core Guarantees
- **Local Compute**: Powered by your local Ollama instance or local open-weights LLMs (Llama 3.2, Qwen 2.5, Mistral).
- **Hardware-Aware Acceleration**: Auto-detects NVIDIA CUDA GPUs (8GB+ VRAM recommended), Apple Silicon Metal, or multi-core CPU inference.
- **Offline-First Network Boundary**: Binds to host loopback (`127.0.0.1`) with zero remote telemetry by default, verified via our built-in multi-layer socket & HTTP client auditor (`verify_airgap.py`).
- **Deterministic Provenance & Citations**: Every finding, risk score, obligation item, or knowledge graph node links to an SQLite entity and exact bounding-box coordinates `[x0, y0, x1, y1]` or unified DOCX clause anchors.

> [!NOTE]
> **Operational Scope & Air-Gap Scope**: The zero-egress guarantee applies to application runtime behavior during document parsing, vector indexing, contract auditing, and local LLM inference. Initial setup (cloning the repo, installing Python packages, or pulling Docker images and Ollama model weights) requires standard network access unless deploying pre-packaged offline bundles. In classified or high-security regulatory enclaves, physical or OS-level network isolation (such as hardware disconnection or host firewall rules) must be enforced independently.

---

## 🏛️ Product Editions & Strategy

SovereignDoc follows a dual-licensing open-core architecture. For detailed feature specifications, see **[`docs/EDITIONS.md`](docs/EDITIONS.md)**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SOVEREIGNDOC PRODUCT TIERS                            │
├──────────────────────────────┬──────────────────────────────┬───────────────┤
│    AGPL COMMUNITY EDITION    │    COMMERCIAL PRO EDITION    │  ENTERPRISE   │
│       (Milestones 1-6)       │          (Tier 2)            │   (Tier 3)    │
├──────────────────────────────┼──────────────────────────────┼───────────────┤
│ ✓ Plugin SDK & Registry     │ 🔒 Custom Firm Playbooks     │ 🔒 Multi-Agent│
│ ✓ 7 Core Clause Classes     │ 🔒 Saved Review Templates    │    Review     │
│ ✓ 9 Built-in Risk Rules     │ 🔒 Custom Risk Rule Editor   │ 🔒 Multi-Agent│
│ ✓ Obligations Extractor     │ 🔒 Dynamic Dollar Thresholds │    Graph      │
│ ✓ Versioned ReviewRuns      │ 🔒 Negotiation Intelligence  │ 🔒 Org Vaults │
│ ✓ Split PDF & DOCX Viewer   │ 🔒 Suggested Counter-Clauses │ 🔒 SSO & RBAC │
│ ✓ Review Package (.ZIP)     │ 🔒 Market Standard Benchmark │ 🔒 Compliance │
│ ✓ Basic Redline (Word Diff) │ 🔒 Firm Clause Library       │    Audit Logs │
│ ✓ Personal Second Brain     │ 🔒 Cross-Contract Analytics  │ 🔒 Air-Gapped │
│ ✓ 2D Knowledge Graph Canvas │ 🔒 Multi-Contract Portfolio  │    License    │
│ ✓ Air-Gap Verification      │ 🔒 Redline Export (PDF/DOCX) │               │
│ ✓ 25-Page E2E Benchmark     │ 🔒 GraphRAG (node_embedding) │               │
│                             │ 🔒 Pro Plugin Modules        │               │
└──────────────────────────────┴──────────────────────────────┴───────────────┘
```

---

## ⚡ Quick Start

### 1. One-Click Full Stack Launch
On Windows, run the automated launcher script to verify preflight checks and start both the FastAPI backend (`:8000`) and React frontend (`:5173`):
```powershell
.\run_app.bat
```
*(On macOS and Linux, launch the stack via Docker: `docker compose up -d`, or start the backend and frontend services using standard shell commands).*

- **Web UI**: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Run Automated Verification Tests
Run the comprehensive test suite across all domain verification suites:
```powershell
.\test_backend.bat
```

### 3. Run Standalone Air-Gap Auditor & 25-Page Hardware Benchmark
```powershell
# Multi-layer Zero-Egress Air-Gap Audit (audit_version = "1.0")
.\backend\.venv\Scripts\python.exe backend/verify_airgap.py

# 25-Page End-to-End Document & Local Hardware Benchmark
.\backend\.venv\Scripts\python.exe backend/benchmark_hardware.py
```

### 4. Docker Deployment Guide (`v1.1.0-community`)

#### ⭐ Recommended: Official All-in-One Workstation (`airgapaxis/sovereigndoc`)
Launch the complete SovereignDoc workstation (React Web UI, FastAPI backend, and pre-baked ONNX embeddings):

```powershell
# 1-Click Launchers (auto-cleans stale containers, verifies Docker, and opens browser):
.\docker-run.ps1          # Windows (PowerShell)
./docker-run.sh           # Linux / macOS (Bash)
```

Or run directly via standard Docker CLI:
```powershell
docker run -d `
  --name sovereigndoc `
  -p 127.0.0.1:8000:8000 `
  -v sovereigndoc_data:/root/.sovereigndoc `
  -e OLLAMA_BASE_URL="http://host.docker.internal:11434" `
  --add-host host.docker.internal:host-gateway `
  --restart unless-stopped `
  airgapaxis/sovereigndoc:latest
```

- **Workstation UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/system/health](http://127.0.0.1:8000/api/system/health)

Alternatively, start via Docker Compose:
```powershell
docker compose up -d
```

#### 🛠️ Advanced / Split Microservices Deployment
For contributors or independent frontend/backend development:
```powershell
docker compose -f docker-compose.dev.yml up -d
```
- **Web UI (Vite Dev Server)**: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)

```powershell
# Verify strict offline container operation (--network none)
docker run --rm --network none airgapaxis/sovereigndoc:1.1.0-community python backend/verify_airgap.py --strict-guard
```

---

## ⚖️ Legal & Regulatory Notice

**SovereignDoc is an automated document processing and intelligence tool provided by Idea To Fact LLC for informational, research, and productivity assistance only. SovereignDoc does not provide legal advice, legal representation, or formal legal opinions.**

All outputs, risk scores, clause classifications, and redlines must be reviewed and verified by a licensed attorney prior to executing any legal agreement. Use of SovereignDoc does not create an attorney-client relationship. See **[`DISCLAIMER.md`](DISCLAIMER.md)** for the complete legal disclaimer.

---

## 📚 Documentation & Governance Reference

- **Product Editions Matrix**: [docs/EDITIONS.md](docs/EDITIONS.md)
- **Commercial Terms Framework**: [docs/commercial/COMMERCIAL_TERMS_FRAMEWORK.md](docs/commercial/COMMERCIAL_TERMS_FRAMEWORK.md)
- **Trademark Policy**: [docs/TRADEMARKS.md](docs/TRADEMARKS.md)
- **Third-Party Software & Model Notices**: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- **Copyright & Ownership Notice**: [NOTICE](NOTICE)
- **Feature Matrix & Capabilities**: [docs/FEATURES.md](docs/FEATURES.md)
- **End-User Guide & Manual**: [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- **Frequently Asked Questions (FAQ)**: [docs/FAQ.md](docs/FAQ.md)
- **System Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Docker Deployment**: [docs/DEPLOYMENT_DOCKER.md](docs/DEPLOYMENT_DOCKER.md)
- **Air-Gap Security Architecture**: [SECURITY.md](SECURITY.md)
- **Privacy Notice**: [PRIVACY.md](PRIVACY.md)
- **Legal Disclaimer**: [DISCLAIMER.md](DISCLAIMER.md)
- **Contributor Guide & CLA**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Code of Conduct**: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- **Open-Source License**: [LICENSE (GNU AGPLv3)](LICENSE)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

For commercial licensing (exempting organizations from AGPLv3 copyleft obligations), Pro/Enterprise evaluations, or custom playbooks, contact **Idea To Fact LLC** at [licensing@ideatofact.com](mailto:licensing@ideatofact.com) or visit [https://ideatofact.com](https://ideatofact.com).
