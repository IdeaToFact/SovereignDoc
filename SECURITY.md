# Security Architecture & Vulnerability Reporting (`SECURITY.md`)

SovereignDoc is designed for high-assurance legal, corporate, and privacy-sensitive workflows where sensitive documents and queries must remain under the user's direct physical and operational control.

---

## 1. Supported Versions

Security updates and patches are provided on a best-effort basis for the Community Edition (guaranteed security SLAs are provided exclusively under Commercial Pro and Enterprise agreements):

| Version | Supported | Notes |
| :--- | :---: | :--- |
| `1.1.x-community` | Yes | Current Community Edition release |
| `1.0.x-community` | No | Superseded by `v1.1.0-community` |
| `< 1.0.0` | No | Pre-release milestone iterations |

---

## 2. Network Boundary Architecture

SovereignDoc is architected as a **local-first, offline-capable application** with zero remote telemetry.

```text
Local Machine / Isolated Enclave Boundary
┌────────────────────────────────────────────────────────────────────────┐
│ Host OS & Container Network Boundary                                   │
│                                                                        │
│  Browser / Client UI   ───▶   Frontend Server (:5173)                  │
│                                      │                                 │
│                                      ▼                                 │
│                               Backend API Server (:8000)               │
│                                      │                                 │
│                     ┌────────────────┴───────────────┐                 │
│                     ▼                                ▼                 │
│         Local FastEmbed ONNX Engine        Local Ollama Server         │
│         (In-Process Vectors & Rerank)      (Host OS: 127.0.0.1:11434   │
│                                            or host.docker.internal)    │
└────────────────────────────────────────────────────────────────────────┘
                       No External WAN Calls
```

### Host Loopback vs. Container Isolation
- **Host Process Execution (`run_app.bat` / manual launch)**: The FastAPI backend binds strictly to `127.0.0.1:8000` and the Vite/Nginx frontend binds to `127.0.0.1:5173`.
- **Docker Container Execution (`docker-compose.yml`)**: Inside the Docker container, processes listen on internal container interfaces (`0.0.0.0`), but Docker port mappings explicitly bind the published ports to the host's loopback interface (`127.0.0.1:8000:8000` and `127.0.0.1:5173:5173`). This prevents unwanted exposure to the local area network (LAN) or wide area network (WAN).
- **Linux Host Deployment Notice**: When deploying on Linux hosts where containers reach the host's Ollama instance, configure Ollama to bind to the Docker bridge gateway interface (typically `172.17.0.1:11434`) rather than `0.0.0.0`, ensuring Ollama is not accessible from external network adapters. Note that `172.17.0.1` requires the `docker0` bridge interface to exist before Ollama starts; if running Ollama as a systemd service, configure systemd ordering (`After=docker.service`) or bind Ollama to `127.0.0.1` and enforce host firewall rules (`ufw` or `iptables`) to restrict access.

---

## 3. Multi-Layer Zero-Egress Guard (`AirGapVerifier`)

SovereignDoc includes an egress audit module (`backend/app/services/airgap_verifier.py`) that implements `MultiLayerEgressGuard`. **Please note that `MultiLayerEgressGuard` is an active automated verification and test harness tool, not an in-kernel runtime firewall.** During automated verification and synthetic pipeline execution, `MultiLayerEgressGuard` intercepts and monitors Python outbound networking entrypoints:

1. `socket.socket.connect`
2. `socket.create_connection`
3. `urllib.request.urlopen`
4. `urllib3.connectionpool.HTTPConnectionPool.urlopen`
5. `httpx.Client.send` & `httpx.AsyncClient.send`
6. `requests.Session.send`
7. `aiohttp.ClientSession._request`

The verification guard explicitly allowlists only approved local loopback endpoints (`127.0.0.1`, `::1`, `localhost`) and local container host aliases (`host.docker.internal` and the internal container bridge alias `ollama` for Docker internal service routing). Any attempt by backend code during verification to initiate a network connection to any other hostname, public IP address, or external WAN destination immediately raises a `PermissionError` and logs the security violation.

### What This Guard Covers and What It Does Not Cover

> [!IMPORTANT]
> - **What It Covers**: The guard verifies that SovereignDoc's Python backend application code, vector database, chunkers, and local HTTP clients do not make unauthorized external calls during document processing and inference.
> - **What It Does Not Cover**: The Python-level guard is a verification tool; it cannot monitor external host processes, OS-level background services, native C/C++ compiled binaries, the Docker daemon itself, or network traffic during initial package installation (`docker pull`, `pip install`, `ollama pull`).
> - **True Air-Gap Requirement**: In true classified or air-gapped enclaves, organizations must run SovereignDoc on hardware physically disconnected from external networks or enforce network isolation via host-level firewall policies (e.g., Windows Defender Firewall rules or Linux `iptables`).

---

## 4. Running the Security Audit via CLI

You can run the egress auditor directly from your terminal:

```powershell
# Run the multi-layer zero-egress audit
.\backend\.venv\Scripts\python.exe backend/verify_airgap.py

# Run in strict mode with JSON report output
.\backend\.venv\Scripts\python.exe backend/verify_airgap.py --strict-guard --json
```

In addition, running Docker in `--network none` mode confirms the backend's verification and offline parsing suite runs with zero network egress:
```powershell
docker run --rm --network none airgapaxis/sovereigndoc-backend:1.1.0-community python backend/verify_airgap.py --strict-guard
```

---

## 5. Coordinated Vulnerability Disclosure Policy

We take security and data privacy seriously. **Please do not report security vulnerabilities or potential air-gap bypasses via public GitHub issues.**

### Reporting Process
1. Email your findings directly to **`security@ideatofact.com`** or submit a confidential advisory via **GitHub Private Security Advisories**.
2. Include:
   - A description of the vulnerability and affected versions.
   - Proof-of-concept steps or the JSON output of `python backend/verify_airgap.py --json`.
   - Your name and affiliation for attribution (optional).

### Target Response & Coordinated Disclosure
- **Initial Acknowledgment**: Target within **48 business hours** of receiving your report.
- **Triage & Assessment**: Target within **5 business days**, detailing reproduction status and planned remediation.
- **Coordinated Disclosure**: We request a **90-day** coordinated disclosure period to allow our team to release a verified security patch before details are published. Timelines for Community Edition are best-effort targets and do not create contractual SLA obligations.

### Safe Harbor
Idea To Fact LLC will not pursue legal action or report to law enforcement any security researchers who discover and report vulnerabilities in good faith, provided that they make a good-faith effort to avoid privacy violations, data destruction, and service interruption, give us reasonable time to remediate prior to public disclosure, and do not exploit vulnerabilities beyond the minimum necessary proof of concept.
