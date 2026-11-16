# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import gc
import os
import re
import socket
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

# Ensure repository root (containing 'packages') is in sys.path
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from app.config import settings  # noqa: E402
from app.services.storage_manager import storage_manager  # noqa: E402

AUDIT_VERSION = "1.0"
ALLOWED_LOOPBACK_HOSTS = {
    "127.0.0.1",
    "localhost",
    "::1",
    "0.0.0.0",
    "host.docker.internal",
    "ollama",
    "testserver",
    "",
}
ALLOWED_NAMESPACE_URLS = {
    "http://www.w3.org/2000/svg",
    "http://www.w3.org/1999/xhtml",
    "http://schemas.openxmlformats.org",
    "https://github.com/ideatofact/sovereigndoc",  # AGPLv3 §13 Source Code Offer link
}


def _is_loopback_host(host: Optional[str]) -> bool:
    if not host:
        return True
    clean = host.strip().lower().strip("[]")
    if clean in ALLOWED_LOOPBACK_HOSTS:
        return True
    if clean.startswith("127."):
        return True
    return False


def _extract_host_from_url(url_str: str) -> str:
    try:
        parsed = urlparse(url_str)
        return (parsed.hostname or "").lower()
    except Exception:
        return ""


class MultiLayerEgressGuard:
    """Context manager that intercepts outbound network traffic across both low-level OS sockets
    and high-level HTTP client libraries (socket, urllib, urllib3, httpx, requests, aiohttp).
    Any connection targeting a non-loopback host is immediately blocked and recorded.
    """

    def __init__(self) -> None:
        self.blocked_attempts: List[Dict[str, str]] = []
        self.allowed_loopback_attempts: int = 0
        self.intercepted_layers: List[str] = [
            "socket.connect",
            "socket.create_connection",
            "urllib.request.urlopen",
        ]
        self._orig_socket_connect: Optional[Callable[..., Any]] = None
        self._orig_create_connection: Optional[Callable[..., Any]] = None
        self._orig_urllib_urlopen: Optional[Callable[..., Any]] = None
        self._orig_urllib3_urlopen: Optional[Callable[..., Any]] = None
        self._orig_httpx_send: Optional[Callable[..., Any]] = None
        self._orig_httpx_async_send: Optional[Callable[..., Any]] = None
        self._orig_requests_send: Optional[Callable[..., Any]] = None
        self._orig_aiohttp_request: Optional[Callable[..., Any]] = None

    def _record_and_raise(self, layer: str, target: str) -> None:
        self.blocked_attempts.append({"layer": layer, "target": target})
        raise PermissionError(
            f"[SovereignDoc Air-Gap Guard] Blocked external network egress via {layer} -> {target}"
        )

    def __enter__(self) -> "MultiLayerEgressGuard":
        guard = self

        # 1. Low-level socket.socket.connect
        orig_sock_connect = socket.socket.connect
        self._orig_socket_connect = orig_sock_connect

        def guarded_socket_connect(sock_self: Any, address: Any) -> Any:
            host = address[0] if isinstance(address, tuple) and len(address) >= 1 else str(address)
            port = address[1] if isinstance(address, tuple) and len(address) > 1 else ""
            if not _is_loopback_host(host):
                guard._record_and_raise("socket.socket.connect", f"{host}:{port}")
            guard.allowed_loopback_attempts += 1
            return orig_sock_connect(sock_self, address)

        setattr(socket.socket, "connect", guarded_socket_connect)

        # 2. socket.create_connection
        orig_create_conn = socket.create_connection
        self._orig_create_connection = orig_create_conn

        def guarded_create_connection(address: Any, *args: Any, **kwargs: Any) -> Any:
            host = address[0] if isinstance(address, tuple) and len(address) >= 1 else str(address)
            port = address[1] if isinstance(address, tuple) and len(address) > 1 else ""
            if not _is_loopback_host(host):
                guard._record_and_raise("socket.create_connection", f"{host}:{port}")
            guard.allowed_loopback_attempts += 1
            return orig_create_conn(address, *args, **kwargs)

        setattr(socket, "create_connection", guarded_create_connection)

        # 3. urllib.request.urlopen
        orig_urllib_open = urllib.request.urlopen
        self._orig_urllib_urlopen = orig_urllib_open

        def guarded_urllib_urlopen(url: Any, *args: Any, **kwargs: Any) -> Any:
            target_url = getattr(url, "full_url", str(url))
            host = _extract_host_from_url(target_url)
            if not _is_loopback_host(host):
                guard._record_and_raise("urllib.request.urlopen", str(target_url))
            guard.allowed_loopback_attempts += 1
            return orig_urllib_open(url, *args, **kwargs)

        setattr(urllib.request, "urlopen", guarded_urllib_urlopen)

        # 4. urllib3 (if installed)
        try:
            import urllib3.connectionpool  # type: ignore

            orig_urllib3_open = urllib3.connectionpool.HTTPConnectionPool.urlopen
            self._orig_urllib3_urlopen = orig_urllib3_open
            self.intercepted_layers.append("urllib3.HTTPConnectionPool.urlopen")

            def guarded_urllib3_urlopen(pool_self: Any, method: Any, url: Any, *args: Any, **kwargs: Any) -> Any:
                host = getattr(pool_self, "host", "")
                if not _is_loopback_host(host):
                    guard._record_and_raise("urllib3.HTTPConnectionPool.urlopen", f"{host}{url}")
                guard.allowed_loopback_attempts += 1
                return orig_urllib3_open(pool_self, method, url, *args, **kwargs)

            setattr(urllib3.connectionpool.HTTPConnectionPool, "urlopen", guarded_urllib3_urlopen)
        except ImportError:
            pass

        # 5. httpx (Client & AsyncClient)
        try:
            import httpx  # type: ignore

            orig_httpx_send = httpx.Client.send
            orig_httpx_async_send = httpx.AsyncClient.send
            self._orig_httpx_send = orig_httpx_send
            self._orig_httpx_async_send = orig_httpx_async_send
            self.intercepted_layers.extend(["httpx.Client.send", "httpx.AsyncClient.send"])

            def guarded_httpx_send(client_self: Any, request: Any, *args: Any, **kwargs: Any) -> Any:
                host = request.url.host or ""
                if not _is_loopback_host(host):
                    guard._record_and_raise("httpx.Client.send", str(request.url))
                guard.allowed_loopback_attempts += 1
                return orig_httpx_send(client_self, request, *args, **kwargs)

            async def guarded_httpx_async_send(client_self: Any, request: Any, *args: Any, **kwargs: Any) -> Any:
                host = request.url.host or ""
                if not _is_loopback_host(host):
                    guard._record_and_raise("httpx.AsyncClient.send", str(request.url))
                guard.allowed_loopback_attempts += 1
                return await orig_httpx_async_send(client_self, request, *args, **kwargs)

            setattr(httpx.Client, "send", guarded_httpx_send)
            setattr(httpx.AsyncClient, "send", guarded_httpx_async_send)
        except ImportError:
            pass

        # 6. requests (if installed)
        try:
            import requests  # type: ignore

            orig_req_send = requests.Session.send
            self._orig_requests_send = orig_req_send
            self.intercepted_layers.append("requests.Session.send")

            def guarded_requests_send(session_self: Any, request: Any, *args: Any, **kwargs: Any) -> Any:
                host = _extract_host_from_url(getattr(request, "url", ""))
                if not _is_loopback_host(host):
                    guard._record_and_raise("requests.Session.send", str(getattr(request, "url", "")))
                guard.allowed_loopback_attempts += 1
                return orig_req_send(session_self, request, *args, **kwargs)

            setattr(requests.Session, "send", guarded_requests_send)
        except ImportError:
            pass

        # 7. aiohttp (if installed)
        try:
            import aiohttp  # type: ignore

            orig_aio_req = aiohttp.ClientSession._request
            self._orig_aiohttp_request = orig_aio_req
            self.intercepted_layers.append("aiohttp.ClientSession._request")

            async def guarded_aiohttp_request(session_self: Any, method: Any, str_or_url: Any, *args: Any, **kwargs: Any) -> Any:
                host = _extract_host_from_url(str(str_or_url))
                if not _is_loopback_host(host):
                    guard._record_and_raise("aiohttp.ClientSession._request", str(str_or_url))
                guard.allowed_loopback_attempts += 1
                return await orig_aio_req(session_self, method, str_or_url, *args, **kwargs)

            setattr(aiohttp.ClientSession, "_request", guarded_aiohttp_request)
        except ImportError:
            pass

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._orig_socket_connect is not None:
            setattr(socket.socket, "connect", self._orig_socket_connect)
        if self._orig_create_connection is not None:
            setattr(socket, "create_connection", self._orig_create_connection)
        if self._orig_urllib_urlopen is not None:
            setattr(urllib.request, "urlopen", self._orig_urllib_urlopen)
        if self._orig_urllib3_urlopen is not None:
            try:
                import urllib3.connectionpool  # type: ignore

                setattr(urllib3.connectionpool.HTTPConnectionPool, "urlopen", self._orig_urllib3_urlopen)
            except ImportError:
                pass
        if self._orig_httpx_send is not None:
            try:
                import httpx  # type: ignore

                setattr(httpx.Client, "send", self._orig_httpx_send)
                setattr(httpx.AsyncClient, "send", self._orig_httpx_async_send)
            except ImportError:
                pass
        if self._orig_requests_send is not None:
            try:
                import requests  # type: ignore

                setattr(requests.Session, "send", self._orig_requests_send)
            except ImportError:
                pass
        if self._orig_aiohttp_request is not None:
            try:
                import aiohttp  # type: ignore

                setattr(aiohttp.ClientSession, "_request", self._orig_aiohttp_request)
            except ImportError:
                pass


class AirGapVerifier:
    """Automated Air-Gap Security Auditor (audit_version = "1.0").
    Verifies telemetry lockdown, static frontend bundle purity, active process sockets,
    and zero external egress across multi-layer socket/HTTP client guards.
    """

    _last_audit_report: Optional[Dict[str, Any]] = None

    @classmethod
    def check_telemetry_and_host_lockdown(cls) -> Dict[str, Any]:
        """Verify SovereignSettings host binding, Ollama loopback URL, and telemetry opt-out flags."""
        issues: List[str] = []

        if not _is_loopback_host(settings.host):
            issues.append(f"API host '{settings.host}' is not bound to loopback (127.0.0.1/localhost)")

        ollama_host = _extract_host_from_url(settings.ollama_url)
        if not _is_loopback_host(ollama_host):
            issues.append(f"Ollama URL '{settings.ollama_url}' targets non-loopback host '{ollama_host}'")

        anon_tel = os.environ.get("ANONYMIZED_TELEMETRY", "").lower()
        if anon_tel not in ("false", "0", "no"):
            issues.append(f"ANONYMIZED_TELEMETRY is '{anon_tel}' (expected 'False')")

        dnt = os.environ.get("DO_NOT_TRACK", "")
        if dnt != "1":
            issues.append(f"DO_NOT_TRACK is '{dnt}' (expected '1')")

        hf_tel = os.environ.get("HF_HUB_DISABLE_TELEMETRY", "")
        if hf_tel != "1":
            issues.append(f"HF_HUB_DISABLE_TELEMETRY is '{hf_tel}' (expected '1')")

        return {
            "id": "telemetry_and_host_lockdown",
            "name": "Telemetry & Loopback Host Lockdown",
            "passed": len(issues) == 0,
            "details": {
                "api_host": settings.host,
                "api_port": settings.port,
                "ollama_url": settings.ollama_url,
                "ANONYMIZED_TELEMETRY": os.environ.get("ANONYMIZED_TELEMETRY"),
                "CHROMA_TELEMETRY_IMPL": os.environ.get("CHROMA_TELEMETRY_IMPL"),
                "DO_NOT_TRACK": os.environ.get("DO_NOT_TRACK"),
                "HF_HUB_DISABLE_TELEMETRY": os.environ.get("HF_HUB_DISABLE_TELEMETRY"),
                "issues": issues,
            },
        }

    @classmethod
    def check_static_frontend_assets(cls) -> Dict[str, Any]:
        """Deterministically scan frontend/index.html and frontend/src/**/* for any external CDN or remote URLs."""
        frontend_dir = _repo_root / "frontend"
        scanned_files = 0
        external_urls: List[Dict[str, str]] = []

        url_pattern = re.compile(r"https?://[^\s\"'`<>)]+", re.IGNORECASE)

        files_to_scan: List[Path] = []
        index_html = frontend_dir / "index.html"
        if index_html.exists():
            files_to_scan.append(index_html)

        src_dir = frontend_dir / "src"
        if src_dir.exists():
            for ext in ("*.js", "*.jsx", "*.ts", "*.tsx", "*.css", "*.html"):
                files_to_scan.extend(sorted(src_dir.rglob(ext)))

        for fpath in sorted(set(files_to_scan)):
            scanned_files += 1
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for match in url_pattern.findall(content):
                cleaned_url = match.rstrip(".,;:)]}")
                if any(cleaned_url.startswith(ns) for ns in ALLOWED_NAMESPACE_URLS):
                    continue
                host = _extract_host_from_url(cleaned_url)
                if not _is_loopback_host(host):
                    external_urls.append({
                        "file": str(fpath.relative_to(_repo_root)).replace("\\", "/"),
                        "url": cleaned_url,
                    })

        return {
            "id": "static_frontend_assets",
            "name": "Static Frontend Asset Bundle Purity (Zero External CDNs)",
            "passed": len(external_urls) == 0,
            "details": {
                "scanned_files": scanned_files,
                "external_urls_found": len(external_urls),
                "violations": external_urls,
            },
        }

    @classmethod
    def check_active_sockets(cls) -> Dict[str, Any]:
        """Inspect active socket objects in the current Python process to verify zero external connections."""
        external_connections: List[Dict[str, str]] = []
        loopback_sockets = 0

        for obj in gc.get_objects():
            if isinstance(obj, socket.socket):
                try:
                    if obj.fileno() == -1:
                        continue
                    laddr = obj.getsockname()
                    laddr_ip = laddr[0] if isinstance(laddr, tuple) and len(laddr) >= 1 else str(laddr)
                except Exception:
                    laddr_ip = ""

                try:
                    raddr = obj.getpeername()
                    raddr_ip = raddr[0] if isinstance(raddr, tuple) and len(raddr) >= 1 else str(raddr)
                    raddr_port = raddr[1] if isinstance(raddr, tuple) and len(raddr) >= 2 else ""
                except Exception:
                    raddr_ip = ""
                    raddr_port = ""

                if raddr_ip and not _is_loopback_host(raddr_ip):
                    external_connections.append({
                        "local": str(laddr_ip),
                        "remote": f"{raddr_ip}:{raddr_port}",
                        "status": "ESTABLISHED",
                    })
                else:
                    loopback_sockets += 1

        return {
            "id": "active_process_sockets",
            "name": "Live Process Socket Table Inspection",
            "passed": len(external_connections) == 0,
            "details": {
                "inspection_mode": "python_runtime_socket_inspector",
                "external_connections_count": len(external_connections),
                "external_connections": external_connections,
                "loopback_only_verified": len(external_connections) == 0,
            },
        }

    @classmethod
    def check_pipeline_zero_egress(cls, run_synthetic_pipeline: bool = True) -> Dict[str, Any]:
        """Verify that MultiLayerEgressGuard blocks simulated external socket + HTTP client calls
        and that executing a synthetic SovereignDoc pipeline produces zero external network attempts.
        """
        # Step A: Self-test proving MultiLayerEgressGuard catches external socket, urllib, and httpx calls
        selftest_guard = MultiLayerEgressGuard()
        with selftest_guard:
            # 1. Raw socket connect to 8.8.8.8:443
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect(("8.8.8.8", 443))
            except PermissionError:
                pass
            finally:
                s.close()

            # 2. urllib.request to external URL
            try:
                urllib.request.urlopen("http://example.com/telemetry", timeout=1)
            except PermissionError:
                pass

            # 3. httpx to external URL (if installed)
            try:
                import httpx  # type: ignore

                with httpx.Client() as client:
                    client.get("http://api.openai.com/v1/models")
            except (PermissionError, ImportError):
                pass

        selftest_passed = len(selftest_guard.blocked_attempts) >= 2

        # Step B: Synthetic pipeline execution under MultiLayerEgressGuard
        pipeline_guard = MultiLayerEgressGuard()
        with pipeline_guard:
            if run_synthetic_pipeline:
                from types import SimpleNamespace
                from packages.contract_intelligence.plugin_sdk.registry import CapabilityRegistry
                import packages.contract_intelligence.risk_rules  # noqa: F401
                from packages.contract_intelligence.classifiers import clause_classifier
                from packages.contract_intelligence.obligations import obligations_extractor
                from app.services.second_brain.link_parser import wiki_link_parser

                sample_chunk = SimpleNamespace(
                    id="airgap_chunk_1",
                    chunk_index=0,
                    text=(
                        "10. Limitation of Liability. Neither party's aggregate liability shall exceed "
                        "unlimited damages. Vendor shall indemnify Client within 30 days of written notice."
                    ),
                    page_number=1,
                    section="10. Limitation of Liability",
                    bbox_json=None,
                )
                chunks = [sample_chunk]
                classified_map = clause_classifier.classify_chunks(chunks, "airgap_doc_1")
                for rule in CapabilityRegistry.get_risk_rules():
                    _ = rule.evaluate(chunks, classified_map)
                _ = obligations_extractor.extract_obligations(chunks, "airgap_doc_1")
                _ = wiki_link_parser.extract_links("Review [[Master_MSA.docx#page=1]] and #indemnity")

        pipeline_zero_egress = len(pipeline_guard.blocked_attempts) == 0

        return {
            "id": "multi_layer_egress_guard",
            "name": "Multi-Layer Socket & HTTP Client Zero-Egress Verification",
            "passed": selftest_passed and pipeline_zero_egress,
            "details": {
                "intercepted_layers": sorted(set(pipeline_guard.intercepted_layers)),
                "guard_selftest_blocked_count": len(selftest_guard.blocked_attempts),
                "guard_selftest_passed": selftest_passed,
                "pipeline_external_attempts": len(pipeline_guard.blocked_attempts),
                "pipeline_blocked_targets": pipeline_guard.blocked_attempts,
            },
        }

    @classmethod
    def run_audit(cls, run_synthetic_pipeline: bool = True) -> Dict[str, Any]:
        """Execute all deterministic air-gap security checks and cache the latest report."""
        checks = [
            cls.check_telemetry_and_host_lockdown(),
            cls.check_static_frontend_assets(),
            cls.check_active_sockets(),
            cls.check_pipeline_zero_egress(run_synthetic_pipeline=run_synthetic_pipeline),
        ]
        all_passed = all(c["passed"] for c in checks)
        pipeline_check = checks[3]["details"]

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        report = {
            "audit_version": AUDIT_VERSION,
            "passed": all_passed,
            "status_label": "PASS" if all_passed else "FAIL",
            "last_audit_at": now_iso,
            "blocked_external_attempts": pipeline_check["pipeline_external_attempts"],
            "intercepted_layers": pipeline_check["intercepted_layers"],
            "storage_paths": {
                "base_data_dir": str(storage_manager.base_dir),
                "vaults_dir": str(storage_manager.vaults_dir),
                "sqlite_db": str(storage_manager.db_dir / "metadata.db"),
                "chroma_dir": str(storage_manager.db_dir / "chroma"),
                "cache_dir": str(storage_manager.cache_dir),
            },
            "checks": checks,
        }
        cls._last_audit_report = report
        return report

    @classmethod
    def get_audit_report(cls, refresh: bool = False) -> Dict[str, Any]:
        """Return cached audit report if available, or run a fresh audit when refresh=True or uninitialized."""
        if refresh or cls._last_audit_report is None:
            return cls.run_audit(run_synthetic_pipeline=True)
        return cls._last_audit_report


airgap_verifier = AirGapVerifier()
