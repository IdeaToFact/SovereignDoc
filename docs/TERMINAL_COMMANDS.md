# SovereignDoc: Terminal Commands Reference Guide

This document lists all essential commands for setting up, running, testing, and managing the SovereignDoc backend from PowerShell or Command Prompt.

---

## 🚀 Quick Start (One-Liner)

From the project root (`sovereign_doc`):

```powershell
# Activate environment and start backend server
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

---

## 1. Virtual Environment & Setup

Navigate to the `backend` directory:
```powershell
cd "d:\workspace\AI 2nd Brain\sovereign_doc\backend"
```

### Activate the Virtual Environment:
- **PowerShell**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- **Command Prompt (CMD)**:
  ```cmd
  .\.venv\Scripts\activate.bat
  ```

### Recreate Virtual Environment (if ever needed):
```powershell
# Using Python 3.12:
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv

# Or using uv (ultra-fast):
uv venv .venv
```

---

## 2. Dependency Management

Inside `backend/` with `.venv` active:

### Install / Update Dependencies:
```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
```

### Check Installed Packages:
```powershell
.\.venv\Scripts\pip.exe list
```

---

## 3. Running the Backend Server

### Development Mode (with hot-reload):
```powershell
# Method A: Using app/run.py
.\.venv\Scripts\python.exe app\run.py

# Method B: Direct Uvicorn
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Production / Strict Localhost Mode:
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
```

Once running, access:
- **Live API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 4. Running Tests & Verifications

From `backend/`:

### Run Milestone 1 Smoke Test Suite:
```powershell
.\.venv\Scripts\python.exe test_milestone1.py
```

### Run with Pytest (Verbose):
```powershell
.\.venv\Scripts\pytest.exe test_milestone1.py -v
```

### Run Pytest with Detailed Output & No Warnings:
```powershell
.\.venv\Scripts\pytest.exe -s -p no:warnings
```

---

## 5. Testing Live Endpoints from Terminal

While the backend is running, test endpoints directly using PowerShell:

### 1. Health & Air-Gap Status:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/system/health" | ConvertTo-Json
```

### 2. Hardware Capability & Accelerator Profile:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/system/hardware" | ConvertTo-Json -Depth 4
```

### 3. System Capabilities Flag (Frontend Gating):
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/system/capabilities" | ConvertTo-Json
```

### 4. Discovered Models List:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/models" | ConvertTo-Json -Depth 4
```

### 5. Select Active Model:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/models/select" -Method Post -ContentType "application/json" -Body '{"model_name": "llama3.2:3b"}'
```

### 6. Test Local Inference:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/models/test" -Method Post -ContentType "application/json" -Body '{"prompt": "Say hello from local AI"}' | ConvertTo-Json
```

*(cURL equivalent)*:
```bash
curl -X GET "http://127.0.0.1:8000/api/system/health"
curl -X POST "http://127.0.0.1:8000/api/models/select" -H "Content-Type: application/json" -d "{\"model_name\":\"llama3.2:3b\"}"
```

---

## 6. Local Ollama Management

If Ollama is not installed or running:

### Install Ollama on Windows:
Download and run the installer from: [https://ollama.com/download](https://ollama.com/download)

### Start Ollama Service:
```powershell
ollama serve
```

### Pull Recommended Models (based on your RTX 5070 12GB VRAM):
```powershell
# Fast lightweight model (Instant response)
ollama pull llama3.2:3b

# Recommended balanced models (High reasoning)
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
ollama pull mistral:7b
```

### List Installed Models:
```powershell
ollama list
```

---

## 7. Storage & Maintenance

SovereignDoc stores all local vaults, vectors, and caches in `~/.sovereigndoc/`.

### Inspect Local Storage:
```powershell
Get-ChildItem -Path "$env:USERPROFILE\.sovereigndoc" -Recurse
```

### Wipe Cache (Safe, retains vaults & DB):
```powershell
Remove-Item -Path "$env:USERPROFILE\.sovereigndoc\cache\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### Complete Reset (Wipe all local data):
```powershell
Remove-Item -Path "$env:USERPROFILE\.sovereigndoc" -Recurse -Force -ErrorAction SilentlyContinue
```

---

## 8. Milestone 2: Vaults & Hybrid RAG Testing

### Run Milestone 2 Test Suite:
```powershell
.\.venv\Scripts\python.exe test_milestone2.py
```

### Create a Document Vault:
```powershell
$vault = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/vaults" -Method Post -ContentType "application/json" -Body '{"name": "Contracts 2026", "description": "Legal documents"}'
$vaultId = $vault.id
echo "Created Vault ID: $vaultId"
```

### List Vaults:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/vaults" | ConvertTo-Json -Depth 4
```

### Upload a Document to Vault:
```powershell
$form = @{ file = Get-Item "path\to\document.pdf" }
$job = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/vaults/$vaultId/documents/upload" -Method Post -Form $form
$job | ConvertTo-Json
```

### Execute Two-Stage Hybrid Query with Reranking:
```powershell
$queryBody = @{
    query = "What are the indemnification limits and notice requirements?"
    top_k = 5
    mode = "hybrid"
    enable_reranker = $true
    expand_window = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/vaults/$vaultId/query" -Method Post -ContentType "application/json" -Body $queryBody | ConvertTo-Json -Depth 5
```

---

## 9. Milestones 3, 4 & 4.1: Grounded Chat, Contract Intelligence & Unified Pagination

### Run All Verification Suites:
```powershell
.\.venv\Scripts\python.exe test_milestone3_backend.py
.\.venv\Scripts\python.exe test_milestone4.py
.\.venv\Scripts\python.exe test_milestone4_1.py
```

### Fetch Paginated Document HTML (DOCX / MD / CSV):
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/vaults/$vaultId/documents/$docId/html" | ConvertTo-Json -Depth 4
```

### List Document-Scoped Chat Sessions:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/vaults/$vaultId/documents/$docId/sessions" | ConvertTo-Json -Depth 4
```

### Execute Versioned Contract Review Run (Risks & Obligations):
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/vaults/$vaultId/documents/$docId/review-runs" -Method Post | ConvertTo-Json -Depth 5
```

---

## 10. Milestone 5: Personal Second Brain & Grounded Knowledge Graph

### Run Milestone 5 Verification Suite:
```powershell
.\.venv\Scripts\python.exe test_milestone5.py
```

### Create a Markdown Second Brain Note (with `[[WikiLinks]]` & `#tags`):
```powershell
$noteBody = @{
    title = "Indemnification Strategy"
    content_md = "Review [[Doc:Contract.docx#Page 6]] for cap exceptions #indemnity #high-risk"
    document_id = $docId
    page_number = 6
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/vaults/$vaultId/notes" -Method Post -ContentType "application/json" -Body $noteBody | ConvertTo-Json -Depth 4
```

### Query 7-Entity Grounded Knowledge Graph & Statistics (with Search):
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/vaults/$vaultId/graph?q=Indemnification" | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/vaults/$vaultId/graph/stats" | ConvertTo-Json -Depth 4
```

---

## 11. Milestone 6: Air-Gap Security Auditor, 25-Page E2E Benchmark & Full Suite

### Run Standalone Multi-Layer Air-Gap Auditor (`audit_version = "1.0"`):
```powershell
.\backend\.venv\Scripts\python.exe backend/verify_airgap.py
```

### Run Standalone 25-Page End-to-End Document & Hardware Benchmark:
```powershell
.\backend\.venv\Scripts\python.exe backend/benchmark_hardware.py
```

### Run Milestone 6 Verification Suite:
```powershell
.\backend\.venv\Scripts\python.exe backend/test_milestone6.py
```

### Query Live Air-Gap Audit & Trigger Benchmark via REST API:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/system/airgap-audit?refresh=true" | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/system/benchmark" -Method Post | ConvertTo-Json -Depth 5
```

---

## 12. Milestone 6.1: Legal Disclaimer Acceptance & Air-Gapped Docker Commands

### Accept Legal Disclaimer (`v1.0`) via REST API:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/workspace/accept-disclaimer" -Method Post | ConvertTo-Json -Depth 4
```

### Build & Run Pre-Baked Air-Gapped Docker Stack (Recommended BYOO Mode):
> **Recommended Deployment — Bring Your Own Ollama (BYOO)**:
> 1. Install Docker Desktop & Host Ollama
> 2. Pull a model on your host (`ollama pull qwen3`, `ollama pull llama3.3`, or `ollama pull mistral`)
> 3. Run `docker compose up -d` (`backend` connects to host Ollama via `OLLAMA_BASE_URL=http://host.docker.internal:11434`)
> 4. Open [http://127.0.0.1:5173](http://127.0.0.1:5173)
>
> **Networking Note**: `docker-compose.yml` binds host ports strictly to `127.0.0.1:8000:8000` and `127.0.0.1:5173:5173` (preventing LAN/WAN exposure on the host) while using `sovereigndoc_net` (`driver: bridge`) for isolated internal container networking.

```powershell
# Build pre-baked images (caches BGE-small & MS-MARCO ONNX models inside the image)
docker compose build

# Start air-gapped containers bound to 127.0.0.1
docker compose up -d

# Run offline verification inside the container with zero network access (--network none)
docker run --rm --network none airgapaxis/sovereigndoc-backend:1.0.0 python backend/verify_airgap.py --strict-guard
docker run --rm --network none airgapaxis/sovereigndoc-backend:1.0.0 python backend/benchmark_hardware.py
docker run --rm --network none airgapaxis/sovereigndoc-backend:1.0.0 python backend/test_milestone6.py
```
