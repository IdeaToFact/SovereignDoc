# Docker Deployment & Air-Gap Verification Guide

This guide provides step-by-step instructions for deploying the **SovereignDoc Community Edition (`v1.1.0-community`)** using Docker Desktop, configuring host loopback networking to connect to your host's local Ollama instance, and verifying strict air-gap operation.

---

## 1. Architectural Overview

SovereignDoc is designed around a **Bring Your Own Ollama (BYOO)** local deployment model. 

```text
Customer Workstation / Laptop (Host OS: Windows, macOS, or Linux)
┌────────────────────────────────────────────────────────┐
│  Ollama (Native Host Runtime)                          │
│  http://localhost:11434                                │
│  - Native GPU Acceleration (CUDA / Metal / ROCm)       │
│  - Frictionless Model Pulls (llama3.2, qwen2.5, mistral│
│  - Unified Host VRAM Management                        │
└───────────────────────────▲────────────────────────────┘
                            │
                            │ Internal Bridge Network
                            │ (host.docker.internal:11434)
┌───────────────────────────┴────────────────────────────┐
│  Docker Bridge Network (`sovereigndoc_net`)            │
│                                                        │
│  ┌────────────────────────┐  ┌───────────────────────┐ │
│  │ sovereigndoc-backend   │  │ sovereigndoc-frontend │ │
│  │ Port 127.0.0.1:8000    │  │ Port 127.0.0.1:5173   │ │
│  │ FastEmbed ONNX (Bake)  │◄─┼─► React 18 UI / Nginx │ │
│  │ SQLite WAL Engine      │  │ Vite Reverse Proxy    │ │
│  └────────────────────────┘  └───────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

### Why We Do Not Containerize Ollama
1. **Frictionless GPU Acceleration**: Host Ollama natively accesses NVIDIA CUDA, Apple Silicon Metal, and AMD ROCm drivers without requiring `--gpus all`, `nvidia-container-toolkit`, or Docker GPU passthrough configurations.
2. **Zero Image Bloat**: Docker images remain under 1.5 GB because LLM model weights (which range from 4 GB to 40 GB) reside exclusively in your host's Ollama model store.
3. **Independent Upgrades**: You can update models (`ollama pull qwen2.5:14b`) or update the Ollama daemon independently without rebuilding or redeploying SovereignDoc containers.

---

## 2. Prerequisites

1. **Docker Desktop** (or Docker Engine 24.0+ on Linux) with Docker Compose v2:
   - **Windows**: [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/) (requires WSL 2: `wsl --install`).
   - **macOS**: [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/) (Apple Silicon / Intel).
   - **Linux**: [Docker Engine](https://docs.docker.com/engine/install/) & `docker-compose-plugin`.
   - Verify via `docker compose version`.
2. **Ollama** installed natively on your host machine ([ollama.com](https://ollama.com)).
3. At least 16 GB of system RAM (32 GB recommended for 14B models) and 10 GB of free disk space.

---

## 3. Step-by-Step Deployment

### Step 1: Install & Configure Ollama on the Host

1. Install Ollama from [ollama.com/download](https://ollama.com/download).
2. Configure Ollama host networking so Docker containers can communicate with it:
   > [!IMPORTANT]
   > **LAN Security Notice**: To satisfy the zero-LAN-exposure model in [`SECURITY.md`](../SECURITY.md), never leave port 11434 accessible to an untrusted local area network. Restrict access to local container bridge interfaces or enforce host firewall rules.
   - **Linux (`systemd`) [Recommended Secure Pattern]**:
     Bind specifically to your Docker bridge gateway IP (`172.17.0.1:11434`), preventing any external LAN interface exposure:
     ```bash
     sudo systemctl edit ollama.service
     ```
     Add:
     ```ini
     [Unit]
     After=docker.service

     [Service]
     Environment="OLLAMA_HOST=172.17.0.1:11434"
     ```
     *(Note: `After=docker.service` ensures the `docker0` bridge interface exists when Ollama starts. Alternatively, bind to `127.0.0.1` and use local `iptables` / `ufw` rules to restrict port 11434).*
     Save and restart:
     ```bash
     sudo systemctl daemon-reload
     sudo systemctl restart ollama
     ```
   - **Windows (Docker Desktop)**:
     Docker Desktop routes `host.docker.internal` to the host. If your Docker Desktop setup can connect to `127.0.0.1` on the host, no environment change is needed. Otherwise, set `OLLAMA_HOST=0.0.0.0:11434` in PowerShell:
     ```powershell
     [System.Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', [System.EnvironmentVariableTarget]::User)
     ```
     Restart Ollama from the Windows taskbar tray.
     > [!TIP]
     > On Windows, when binding to `0.0.0.0`, configure Windows Defender Firewall to block inbound connections to port 11434 from Public and Private network adapters, allowing only `vEthernet (WSL / Docker)` or local loopback.
   - **macOS (Docker Desktop)**:
     Like Windows, Docker Desktop on macOS can route `host.docker.internal` to the host's loopback interface (`127.0.0.1`). Test with Ollama bound to `127.0.0.1` first. If your macOS Docker networking requires binding to all interfaces to reach the host, run:
     ```bash
     launchctl setenv OLLAMA_HOST "0.0.0.0:11434"
     ```
     Restart the Ollama desktop application, ensuring port 11434 is restricted via the macOS Application Firewall when connected to public networks.

3. Pull one or more recommended models:
   ```bash
   ollama pull qwen2.5:14b   # Recommended for enterprise legal review
   ollama pull llama3.2:3b   # Ultra-fast lightweight review
   ollama pull mistral:7b    # High accuracy reasoning
   ```

4. Verify Ollama is responding on your host:
   ```bash
   curl http://localhost:11434/api/tags
   ```

---

### Step 2: Configure & Launch SovereignDoc

You have three streamlined deployment options depending on your workflow:

#### Option A: Automated 1-Click Launchers (Recommended)
SovereignDoc includes automated helper scripts that handle image verification, stale container cleanup, volume persistence, and automatic browser launching:

- **On Windows (PowerShell)**:
  ```powershell
  # Launch in background and automatically open browser:
  .\docker-run.ps1

  # Or customize port and data directory:
  .\docker-run.ps1 -Port 8080 -NoBrowser
  ```

- **On Linux / macOS (Bash)**:
  ```bash
  chmod +x docker-run.sh
  ./docker-run.sh
  ```

---

#### Option B: Docker Compose

- **End-User / Production Deployment (`docker-compose.yml`)**:
  Pulls the verified immutable release image from Docker Hub:
  ```yaml
  services:
    sovereigndoc:
      image: airgapaxis/sovereigndoc:1.1.0-community
      container_name: sovereigndoc
      ports:
        - "127.0.0.1:8000:8000"
      environment:
        OLLAMA_BASE_URL: http://host.docker.internal:11434
        SOVEREIGNDOC_OLLAMA_URL: http://host.docker.internal:11434
        SOVEREIGNDOC_HOST: 0.0.0.0
        SOVEREIGNDOC_PORT: 8000
        ANONYMIZED_TELEMETRY: "False"
        CHROMA_TELEMETRY_IMPL: "none"
        DO_NOT_TRACK: "1"
        HF_HUB_DISABLE_TELEMETRY: "1"
        HF_HUB_OFFLINE: "1"
      volumes:
        - sovereigndoc_data:/root/.sovereigndoc
      extra_hosts:
        - "host.docker.internal:host-gateway"
      restart: unless-stopped

  volumes:
    sovereigndoc_data:
  ```
  Launch with:
  ```bash
  docker compose up -d
  ```

- **Contributor / Local Build (`docker-compose.dev.yml`)**:
  Builds from local git source tree:
  ```bash
  docker compose -f docker-compose.dev.yml up --build
  ```

---

#### Option C: Standard 1-Line Docker Command
Run directly in your terminal against Docker Hub:

```powershell
# Windows PowerShell:
docker run -d `
  --name sovereigndoc `
  -p 127.0.0.1:8000:8000 `
  -v sovereigndoc_data:/root/.sovereigndoc `
  -e OLLAMA_BASE_URL="http://host.docker.internal:11434" `
  --add-host host.docker.internal:host-gateway `
  --restart unless-stopped `
  airgapaxis/sovereigndoc:latest
```

```bash
# Linux / macOS (Bash):
docker run -d \
  --name sovereigndoc \
  -p 127.0.0.1:8000:8000 \
  -v sovereigndoc_data:/root/.sovereigndoc \
  -e OLLAMA_BASE_URL="http://host.docker.internal:11434" \
  --add-host host.docker.internal:host-gateway \
  --restart unless-stopped \
  airgapaxis/sovereigndoc:latest
```

---

### Step 3: Access the Workstation & Docker Desktop GUI

Open your local browser to:
- **Workstation UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/system/health](http://127.0.0.1:8000/api/system/health)

#### Viewing in Docker Desktop GUI:
1. **Containers Tab**:
   - The container **`sovereigndoc`** displays a green **HEALTHY** indicator once the background healthcheck passes.
   - **Port**: `8000:8000` is mapped and clickable.
   - View live logs, inspect volumes, restart, or stop with a single click.
2. **Images Tab**:
   - `airgapaxis/sovereigndoc:1.1.0-community` is listed with pre-baked ONNX models (~534 MB compressed).

On your first launch, the **Legal & UPL Disclaimer Modal** will appear. Review the terms, check the mandatory acknowledgement, and click **[ Accept & Proceed ]** to initialize your workspace state.

---

## 4. Verifiable Air-Gap Operation

SovereignDoc is engineered with defense-in-depth isolation guarantees:

### 1. Host Loopback Binding (`127.0.0.1`)
Ports are bound explicitly to `127.0.0.1:8000` and `127.0.0.1:5173`. They are not bound to `0.0.0.0`, meaning other devices on your local network (LAN) or the public internet cannot access SovereignDoc.

### 2. Pre-Baked ONNX Models (`HF_HUB_OFFLINE=1`)
`Dockerfile.backend` downloads and compiles both FastEmbed embedding models (`BAAI/bge-small-en-v1.5`) and Cross-Encoder reranker models (`Xenova/ms-marco-MiniLM-L-6-v2`) into the image layer during `docker build`.
At runtime, `HF_HUB_OFFLINE=1` prevents the backend from contacting Hugging Face or any remote repository.

### 3. Automated Zero-Socket Egress Verification
You can execute the built-in air-gap verification script inside the backend container or locally:

```bash
docker exec -it sovereigndoc-backend python /app/backend/verify_airgap.py
```

This audit executes:
- **Socket Interception**: Probes outgoing socket connections via `MultiLayerEgressGuard`, verifying that external connection attempts are blocked.
- **HTTP Client Inspection**: Audits `urllib`, `requests`, `httpx`, and `aiohttp` to ensure zero third-party telemetry calls.
- **Environment Telemetry Checks**: Confirms `ANONYMIZED_TELEMETRY=False`, `DO_NOT_TRACK=1`, and `HF_HUB_DISABLE_TELEMETRY=1`.
- **Loopback Socket Verification**: Confirms that communication occurs exclusively with approved loopback endpoints (`127.0.0.1`, `localhost`) and local container host aliases (`host.docker.internal`, `ollama`).

### 4. Running with `--network none` (Maximum Air-Gap Mode)
To verify strict air-gap compliance, you can run the built-in air-gap auditor and offline regression tests with all network adapters disabled:
```bash
docker run --rm --network none airgapaxis/sovereigndoc:1.1.0-community python backend/verify_airgap.py --strict-guard
docker run --rm --network none airgapaxis/sovereigndoc:1.1.0-community python -m pytest backend/tests/test_airgap.py backend/tests/test_license_guardrails.py
```
Pre-baked ONNX embeddings and offline unit tests execute cleanly with zero network connectivity. (End-to-end LLM inference requires bridging to your host's Ollama instance).

---

## 5. Multi-Architecture Builds & Air-Gapped Offline Operation

### 1. Building Multi-Architecture Images (`docker buildx`)
To build and publish across both `linux/amd64` (Intel/AMD) and `linux/arm64` (Apple Silicon M-Series):

```bash
# Initialize Docker Buildx builder
docker buildx create --name sovereigndoc-builder --use

# Build and push to Docker Hub
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t airgapaxis/sovereigndoc:1.1.0-community \
  -t airgapaxis/sovereigndoc:1.1.0 \
  -t airgapaxis/sovereigndoc:1.1 \
  -t airgapaxis/sovereigndoc:latest \
  -f Dockerfile \
  --push .
```

### 2. Air-Gapped / Classified Offline Deployment (`docker save` / `docker load`)
In classified or disconnected environments with zero internet access:

1. **Export Image on an Internet-Connected Machine**:
   ```bash
   docker save airgapaxis/sovereigndoc:1.1.0-community | gzip > sovereigndoc-1.1.0-community.tar.gz
   ```
2. **Transfer Archive via Secure Media**:
   Transfer `sovereigndoc-1.1.0-community.tar.gz` to the isolated workstation or server.
3. **Load Image on Air-Gapped Workstation**:
   ```bash
   docker load < sovereigndoc-1.1.0-community.tar.gz
   ```
4. **Launch with Strict Loopback Binding**:
   ```bash
   docker run -d \
     --name sovereigndoc \
     -p 127.0.0.1:8000:8000 \
     -v sovereigndoc_data:/root/.sovereigndoc \
     airgapaxis/sovereigndoc:1.1.0-community
   ```

---

## 6. Troubleshooting & FAQ

### Issue: `host.docker.internal:11434` connection refused
- **Cause**: Ollama is bound only to host loopback `127.0.0.1` rather than the Docker bridge gateway interface.
- **Fix**: 
  - On Linux, bind Ollama to the Docker bridge gateway IP: `OLLAMA_HOST=172.17.0.1:11434`.
  - On Windows and macOS, test if `host.docker.internal` connects to host loopback `127.0.0.1` first without modifying `OLLAMA_HOST`. If connection is refused, set `OLLAMA_HOST=0.0.0.0:11434` and configure host firewall rules to restrict port 11434 to local loopback / virtual network adapters, preventing unwanted LAN exposure.
- **Verification**: Run `curl http://host.docker.internal:11434/api/tags` from inside the backend container:
  ```bash
  docker exec -it sovereigndoc-backend curl http://host.docker.internal:11434/api/tags
  ```

### Issue: Linux host networking resolution
- **Cause**: Older Linux Docker engines may not resolve `host.docker.internal` automatically.
- **Fix**: In `docker-compose.yml`, ensure `extra_hosts` includes `"host.docker.internal:host-gateway"`. Alternatively, substitute your host's Docker bridge IP (typically `172.17.0.1:11434`).

### Issue: Port 5173 or 8000 already in use
- **Fix**: Modify the host port in `docker-compose.yml` (e.g. `"127.0.0.1:5174:5173"` or `"127.0.0.1:8001:8000"`).

### Issue: Applying Updates & Re-Indexing Documents
When pulling updates or rebuilding containers:
```bash
docker compose build backend
docker compose up -d
```
If an existing document was uploaded on an earlier version and shows narrow word-level highlights, re-uploading the document in the Web UI will re-index it into full paragraph blocks using the latest 2-stage clustering engine.

### Issue: Data Persistence
All uploaded agreements, parsed chunks, SQLite databases, review runs, notes, and graph nodes persist in the Docker volume `sovereigndoc_data`.
To back up your data:
```bash
docker run --rm -v sovereigndoc_data:/data -v $(pwd):/backup alpine tar czf /backup/sovereigndoc_backup.tar.gz -C /data .
```
To restore:
```bash
docker run --rm -v sovereigndoc_data:/data -v $(pwd):/backup alpine tar xzf /backup/sovereigndoc_backup.tar.gz -C /data
```

