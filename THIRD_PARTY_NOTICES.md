# Third-Party Software & Model Notices (`THIRD_PARTY_NOTICES.md`)

SovereignDoc incorporates or depends upon third-party open-source libraries and machine learning models. This document lists the primary dependencies, their respective licenses, and important commercial licensing considerations.

---

## 1. Backend Python Dependencies

| Package | License | Purpose in SovereignDoc | Commercial Consideration |
| :--- | :--- | :--- | :--- |
| **FastAPI** | MIT | Core HTTP API & WebSocket server | Permissive |
| **Uvicorn** | BSD-3-Clause | ASGI web server implementation | Permissive |
| **HTTPX** | BSD-3-Clause | Async HTTP client for local Ollama communication | Permissive |
| **Pydantic & Pydantic-Settings** | MIT | Data parsing, schema validation, and settings | Permissive |
| **SQLAlchemy** | MIT | SQLite ORM & metadata persistence | Permissive |
| **pypdfium2** | Apache-2.0 / BSD-3-Clause | Permissive PDF parsing & coordinate extraction engine | **Fully Permissive:** Default clean-room PDF engine across Community and Commercial Pro/Enterprise editions. Uses 2-stage line and paragraph clustering to extract exact PDF bounding-box coordinates `[x0, y0, x1, y1]` for full-clause web canvas highlighting. |
| **PyMuPDF (`fitz`)** | **GNU AGPLv3** | Optional alternative PDF parser (Community fallback) | **Copyleft:** Optional alternative in Community Edition only (`SOVEREIGNDOC_PDF_ENGINE=mupdf`). Not used by default; omitted entirely from commercial distribution builds. |
| **python-docx** | MIT | Microsoft Word (.docx) document parser | Permissive |
| **mammoth** | BSD-2-Clause | HTML/DOCX conversion for clause inspection | Permissive |
| **python-multipart** | Apache-2.0 | Multipart form data and document upload parsing | Permissive |
| **ChromaDB** | Apache-2.0 | Embedded local vector database | Permissive |
| **FastEmbed** | Apache-2.0 | 100% local ONNX embedding & cross-encoder runtime | Permissive |
| **rank-bm25** | Apache-2.0 | BM25 sparse keyword retrieval for hybrid search | Permissive |
| **psutil** | BSD-3-Clause | Local hardware monitoring & CPU/RAM discovery | Permissive |
| **pytest** | MIT | Unit and integration test runner | Test-only |

### Transitive Backend Dependencies Note
Direct backend dependencies listed in [`backend/requirements.txt`](backend/requirements.txt) pull standard permissive transitive packages (`numpy`, `onnxruntime`, `tokenizers`, `huggingface-hub`, `starlette`, `anyio`, `pydantic-core`, etc.) as well as weak file-level copyleft / dual-licensed utilities (`certifi` under `MPL-2.0`, `tqdm` under `MPL-2.0 AND MIT`, and `orjson` under `MPL-2.0 AND (Apache-2.0 OR MIT)`). Under `MPL-2.0`, unmodified third-party library files remain compatible with proprietary Commercial Editions without triggering whole-work copyleft obligations. SovereignDoc defaults to `pypdfium2` (Apache-2.0 / BSD-3-Clause) as its clean-room PDF engine across all editions; `PyMuPDF` is retained solely as an optional alternative fallback in Community Edition, and commercial release builds omit `PyMuPDF` entirely from runtime dependencies. All transitive packages should be audited in a clean environment prior to commercial distribution.

---

## 2. Frontend Dependencies (`frontend/package.json`)

| Package | License | Purpose in SovereignDoc | Commercial Consideration |
| :--- | :--- | :--- | :--- |
| **React & React-DOM** | MIT | UI framework | Permissive |
| **pdfjs-dist** | Apache-2.0 | Client-side PDF rendering and canvas highlight overlay | Permissive |
| **mammoth** | BSD-2-Clause | Client-side DOCX inspection rendering | Permissive |
| **Vite & `@vitejs/plugin-react`** | MIT | Frontend build tool and development server (dev/build-time) | Permissive |
| **oxlint** | MIT | Frontend static linter (dev-only) | Dev-only |

---

## 3. Local Machine Learning Models & Weights

By default, SovereignDoc runs FastEmbed in **fail-closed offline mode** (`local_files_only=True` and `HF_HUB_OFFLINE=1` unless `SOVEREIGNDOC_ALLOW_MODEL_DOWNLOADS=1` or `python -m app.services.rag.model_loader --download` is explicitly invoked for staging).

| Model Identifier | Provider / Author | Stated License | Pinned Source & Snapshot Commit | Commercial Considerations |
| :--- | :--- | :--- | :--- | :--- |
| **`BAAI/bge-small-en-v1.5`** | Beijing Academy of AI (BAAI) | **MIT** | `Qdrant/bge-small-en-v1.5-onnx-Q` (FastEmbed ONNX export)<br>Commit: `aa8f8b060edb00e03bfdd08813a2949946c8ba55` | Fully unencumbered dense vector embeddings (384-d). Permissible for both open-source and commercial distributions. |
| **`Xenova/ms-marco-MiniLM-L-6-v2`** | Xenova / Microsoft | **Apache-2.0** (ONNX export) | `Xenova/ms-marco-MiniLM-L-6-v2`<br>Commit: `a09144355adeed5f58c8ed011d209bf8ee5a1fec` | Pre-trained on Microsoft's MS MARCO dataset (historically research-oriented data terms). Used for Community Edition local testing; commercial builds should configure `BAAI/bge-reranker-base`. |
| **`BAAI/bge-reranker-base`** | Beijing Academy of AI (BAAI) | **MIT** | `https://huggingface.co/BAAI/bge-reranker-base`<br>*(Pin full 40-char snapshot SHA when pre-staging)* | Recommended cross-encoder reranker for commercial deployments (`SOVEREIGNDOC_RERANKER_MODEL=BAAI/bge-reranker-base`). |
| **Host LLM Models (Ollama)** | Meta, Alibaba, Mistral AI, etc. | **Vendor-Specific** | Brought by user via local Ollama (`http://127.0.0.1:11434`) | SovereignDoc executes inference via standard local HTTP endpoints and does not bundle or redistribute proprietary LLM weights. |

---

## 4. Container Base Images

- **Backend Container:** Built from `python:3.12-slim` (Debian Linux base). Debian base packages are licensed under various open-source licenses (GPL, LGPL, BSD, MIT).
- **Frontend Container:** Built from `node:22-alpine` (Alpine Linux base).

In accordance with Section 6 of the GNU AGPLv3, complete build scripts and container recipes are provided in [`Dockerfile.backend`](Dockerfile.backend), [`Dockerfile.frontend`](Dockerfile.frontend), and [`docker-compose.yml`](docker-compose.yml). Base OS packages remain governed by their upstream open-source licenses and source-offer terms.

