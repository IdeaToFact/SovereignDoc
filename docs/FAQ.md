# SovereignDoc Frequently Asked Questions (FAQ)

This FAQ answers common operational, architectural, and security questions regarding the **SovereignDoc Community Edition (`v1.1.0-community`)** by **Idea To Fact LLC**.

---

## 1. Privacy & Air-Gap Compliance

### Does SovereignDoc send any data outside my computer?
**No. SovereignDoc is local-first and zero-telemetry by design.**
- The application runtime makes zero remote network calls and contains zero telemetry trackers, analytics SDKs, pingbacks, or usage beacons.
- All machine learning components—including text embedding (`bge-small-en-v1.5`), neural reranking (`ms-marco-MiniLM-L-6-v2`), and local LLM inference—execute on your local workstation CPU or GPU.
- Inbound access is strictly limited: Docker containers bind published ports exclusively to host loopback (`127.0.0.1`), preventing access from your local network (LAN) or the public Internet.
- An automated zero-egress auditor (`MultiLayerEgressGuard`) intercepts outbound Python sockets, HTTP requests, and telemetry variables. *(Note: As detailed in [`SECURITY.md`](../SECURITY.md), while application code enforces zero egress, true classified air-gap isolation requires running on hardware with physical or OS-level network disconnection).*

### Can SovereignDoc run completely offline without an Internet connection?
**Yes (after initial setup and model pulling).** Once the initial Docker images are built (or Python dependencies installed) and your Ollama model is downloaded, SovereignDoc never requires Internet access. All ONNX tokenizers and model weights are pre-baked into the container image.

---

## 2. Artificial Intelligence & Models

### Why does SovereignDoc use host Ollama instead of containerizing Ollama inside Docker?
We deliberately utilize a **Bring Your Own Ollama (BYOO)** model for three critical engineering reasons:
1. **Frictionless GPU Acceleration**: Host-native Ollama directly accesses your GPU hardware (NVIDIA CUDA, Apple Silicon Metal, AMD ROCm) without needing complex Docker GPU passthrough configurations or proprietary container toolkits (`--gpus all`).
2. **Zero Image Bloat**: Docker images stay lightweight (~1.3 GB) because massive LLM weights (4 GB to 40 GB) reside exclusively in your host's native Ollama model store.
3. **Independent Upgrades**: You can update Ollama models (`ollama pull qwen2.5:14b`) or upgrade the Ollama engine without rebuilding or restarting your SovereignDoc containers.

### Can I use cloud LLMs like OpenAI (GPT-4o) or Anthropic (Claude)?
**No.** The Community Edition does not accept external API keys or route queries to third-party cloud APIs. Permitting external API calls introduces the risk of confidential contract text leaking to third-party cloud servers. SovereignDoc exists specifically to provide a sovereign, locally controlled environment for sensitive documents.

### What models do you recommend?
We recommend models based on your hardware specifications:
- **General Legal Review (High Quality)**: `qwen2.5:14b` or `mistral-small` (requires 16 GB+ VRAM or unified memory on Apple Silicon).
- **Fast / Standard Review**: `qwen2.5:7b` or `llama3.1:8b` (requires 8 GB to 12 GB VRAM).
- **Lightweight / Laptop Mode**: `llama3.2:3b` (runs smoothly on CPU or 8 GB laptops).

---

## 3. Legal & Regulatory Practice

### Does SovereignDoc provide legal advice?
**No.** SovereignDoc is an automated document analysis and contract intelligence productivity tool. It does not provide legal advice, does not establish an attorney-client relationship, and is not a substitute for qualified legal counsel.

To enforce this standard, SovereignDoc features a **Dual-Layer UPL (Unauthorized Practice of Law) Guard**:
- **Layer 1**: System prompt directives instruct the local LLM to remain an objective legal analyst.
- **Layer 2**: An application-layer guard monitors incoming queries for legal advice prompts (e.g., *"Should I sign this?"*, *"Am I liable?"*) and automatically injects mandatory regulatory disclaimers into streaming responses and transcripts.

---

## 4. Document Processing & Sizing

### How large a document can SovereignDoc analyze?
SovereignDoc can process agreements ranging from 1-page NDAs to **100+ page master service agreements**:
- It uses a **synthetic pagination engine** that divides documents into standardized 3,000-character page windows, synchronizing page numbers across PDFs and Microsoft Word (.docx) files.
- Retrieval relies on a **sequential chunk expansion window**, retrieving target clauses alongside their preceding and succeeding paragraphs to maintain complete contextual integrity for the LLM.

### What document file formats are supported?
The Community Edition natively supports:
- **PDF Documents** (`.pdf`): Digital PDFs with text layers.
- **Microsoft Word** (`.docx`): Contracts and draft amendments with structural heading preservation.

---

## 5. Deployment & System Operation

### Can I deploy SovereignDoc with Docker Desktop?
**Yes.** Running SovereignDoc via Docker Desktop is our recommended method:
```bash
docker compose up -d
```
The application will be accessible locally at `http://127.0.0.1:5173`. Detailed setup instructions are available in [DEPLOYMENT_DOCKER.md](DEPLOYMENT_DOCKER.md).

### Where are my uploaded contracts and notes stored?
All data is stored locally on your machine in the `~/.sovereigndoc` directory (or inside the persistent Docker named volume `sovereigndoc_data`):
- Ingested Contract files: `~/.sovereigndoc/vaults/<vault_id>/`
- SQLite Metadata & Second Brain: `~/.sovereigndoc/db/metadata.db`
- ChromaDB Dense Vector Store: `~/.sovereigndoc/db/chroma/`
- Ephemeral Cache: `~/.sovereigndoc/cache/`

No data is ever uploaded to external cloud storage or remote servers.

