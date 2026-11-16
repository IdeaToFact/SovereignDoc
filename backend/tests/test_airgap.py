# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Air-Gap Verification & Egress Guard Tests
"""
import socket
import urllib.request
import pytest
from app.services.airgap_verifier import MultiLayerEgressGuard, airgap_verifier


def test_egress_guard_blocks_external_sockets():
    """Verifies MultiLayerEgressGuard blocks external TCP sockets."""
    guard = MultiLayerEgressGuard()
    with guard:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            with pytest.raises(PermissionError):
                s.connect(("1.1.1.1", 443))
        finally:
            s.close()


def test_egress_guard_blocks_urllib_external():
    """Verifies MultiLayerEgressGuard blocks standard library HTTP calls."""
    guard = MultiLayerEgressGuard()
    with guard:
        with pytest.raises(PermissionError):
            urllib.request.urlopen("https://example.com", timeout=0.2)


def test_airgap_verifier_audit():
    """Verifies the system airgap verifier passes audit with zero external egress."""
    report = airgap_verifier.run_audit(run_synthetic_pipeline=False)
    assert report["audit_version"] == "1.0"
    assert report["passed"] is True

