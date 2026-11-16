# Privacy Notice & Data Boundaries (`PRIVACY.md`)

SovereignDoc is built with a **local-first, privacy-by-design architecture**. All document processing, vector search, contract intelligence analysis, research notes, and knowledge graphs run on your own infrastructure with zero remote telemetry by default.

---

## 1. Local-First Data Storage

All data processed by SovereignDoc is stored exclusively on your local filesystem inside a dedicated workspace directory (`~/.sovereigndoc` on Linux/macOS or `C:\Users\<username>\.sovereigndoc` on Windows, customizable via `SOVEREIGNDOC_BASE_DATA_DIR`):

| Data Category | Local Storage Location | Content & Purpose |
| :--- | :--- | :--- |
| **Ingested Documents** | `~/.sovereigndoc/vaults/<vault_id>/` | Original `.pdf`, `.docx`, `.txt`, and `.md` files organized by Vault |
| **SQLite Metadata & Second Brain** | `~/.sovereigndoc/db/metadata.db` | Vault records, document chunks, chat messages, contract `ReviewRun` findings, Markdown notes, `[[WikiLinks]]`, and 2D Knowledge Graph nodes/edges |
| **Dense Vector Embeddings** | `~/.sovereigndoc/db/chroma/` | Embedded local vector database (`BAAI/bge-small-en-v1.5` dense vectors) |
| **Temporary Cache** | `~/.sovereigndoc/cache/` | Ephemeral parsing artifacts generated during document processing |

---

## 2. Telemetry & Remote Transmission Policy

In its standard configuration, SovereignDoc:
- **Does NOT transmit** document text, prompts, model outputs, contract findings, or notes to any cloud server or third-party API.
- **Does NOT collect** usage analytics, crash telemetry, user identifiers, or telemetry beacons.
- **User-Configured LLM Endpoints (`OLLAMA_BASE_URL`)**: By default, SovereignDoc communicates only with your local Ollama daemon (`http://127.0.0.1:11434`). If you explicitly reconfigure `OLLAMA_BASE_URL` (or deploy custom plugins) to point to a remote server or external inference provider, document excerpts will be transmitted to that destination at your sole risk and responsibility (see [`DISCLAIMER.md`](DISCLAIMER.md)).

At backend startup ([`backend/app/config.py`](backend/app/config.py) and [`run_app.bat`](run_app.bat)), SovereignDoc explicitly sets telemetry-suppression environment variables:
```text
ANONYMIZED_TELEMETRY=False
CHROMA_TELEMETRY_IMPL=none
DO_NOT_TRACK=1
HF_HUB_DISABLE_TELEMETRY=1
```

---

## 3. Data Protection & Security Responsibilities

To ensure the security of confidential legal and commercial materials, users must note the following operational realities:

### A. Data at Rest (Full-Disk Encryption Recommended)
- SovereignDoc stores files in standard SQLite and plaintext/binary formats. SovereignDoc **does not encrypt local database files or documents at rest at the application level**.
- For sensitive, privileged, or regulated matters, users are strongly advised to run SovereignDoc on devices with **operating-system-level Full-Disk Encryption (FDE)** enabled:
  - **Windows**: BitLocker Drive Encryption
  - **macOS**: FileVault
  - **Linux**: LUKS (Linux Unified Key Setup)

### B. Chat & Cache Excerpts
- Conversational queries, document summaries, and grounded citations stored in `metadata.db` and the local cache may contain unredacted text excerpts from ingested documents.
- Restricting physical and local user account access to the host machine is the user's responsibility.

### C. Data Removal & SSD Sanitization Limitations
- To remove SovereignDoc data from your machine, stop the server and delete the data directory:
  - **Windows (PowerShell)**: `Remove-Item -Recurse -Force "$HOME\.sovereigndoc"`
  - **macOS / Linux**: `rm -rf ~/.sovereigndoc`
- **Notice on SSD Deletion**: Standard operating system file deletion does not guarantee forensic-grade sanitization on Solid State Drives (SSDs) due to wear-leveling algorithms and controller-level over-provisioning. If forensic erasure is required for compliance, use cryptographically erased containers or secure ATA/NVMe sanitize utilities.

---

## 4. Commercial Tiers Privacy Notice

The terms in this document govern the open-source **Community Edition**. Commercial Pro and Enterprise deployments are governed by separate, signed Commercial Master Services Agreements (MSAs) and Business Associate Agreements (BAAs) where applicable.

For questions regarding data processing or compliance support, contact:  
**Idea To Fact LLC**  
Email: `privacy@ideatofact.com`
