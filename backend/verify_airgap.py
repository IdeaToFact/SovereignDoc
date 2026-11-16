# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

r"""Standalone CLI Air-Gap Security Auditor for SovereignDoc (Milestone 6).

Usage:
    .\backend\.venv\Scripts\python.exe backend/verify_airgap.py
"""
import json
import sys
from pathlib import Path

# Ensure repo root and backend are on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent
for p in (str(REPO_ROOT), str(BACKEND_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.services.airgap_verifier import airgap_verifier  # noqa: E402


def main() -> int:
    print("=" * 72)
    print("  SovereignDoc Air-Gap Security & Zero-Egress Auditor")
    print("=" * 72)

    report = airgap_verifier.run_audit(run_synthetic_pipeline=True)

    print(f"  Audit Schema Version : v{report['audit_version']}")
    print(f"  Timestamp            : {report['last_audit_at']}")
    print(f"  Overall Status       : {'[PASS] 100% LOCAL AIR-GAP VERIFIED' if report['passed'] else '[FAIL] VIOLATION DETECTED'}")
    print("-" * 72)

    for check in report["checks"]:
        badge = "[PASS]" if check["passed"] else "[FAIL]"
        print(f"  {badge} {check['name']} ({check['id']})")

    print("-" * 72)
    print("  Intercepted Network Layers:")
    for layer in report["intercepted_layers"]:
        print(f"    - {layer}")

    print("-" * 72)
    print("  Local Sovereign Storage Layout:")
    for key, val in report["storage_paths"].items():
        print(f"    - {key:18s}: {val}")
    print("=" * 72)

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
