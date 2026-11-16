# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Full Pipeline Integration Smoke Test (E2E)
Mimics: Upload -> Parse -> Embed -> Index -> Review -> Graph -> Note -> Export
"""
import io
from fastapi.testclient import TestClient


def test_full_pipeline_e2e(client: TestClient, sample_pdf_bytes: bytes):
    """Verifies end-to-end legal document intelligence lifecycle in an isolated vault."""
    # 1. Create Vault
    vault_res = client.post("/api/vaults", json={"name": "E2E Pipeline Vault", "description": "Synthetic audit"})
    assert vault_res.status_code == 200
    vault_id = vault_res.json()["id"]

    try:
        # 2. Upload & Parse & Embed
        files = {"file": ("commercial_agreement.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        upload_res = client.post(f"/api/vaults/{vault_id}/documents/upload", files=files)
        assert upload_res.status_code == 200
        job = upload_res.json()
        assert job["status"] == "READY"
        assert job["chunks_generated"] > 0
        doc_id = job["document_id"]

        # 3. Two-Stage Retrieval Query
        query_res = client.post(
            f"/api/vaults/{vault_id}/query",
            json={"query": "What are the termination conditions?", "top_k": 2, "mode": "hybrid"}
        )
        assert query_res.status_code == 200
        search_data = query_res.json()
        assert len(search_data["results"]) > 0

        # 4. Review Audit Run
        review_res = client.post(f"/api/vaults/{vault_id}/documents/{doc_id}/review-runs")
        assert review_res.status_code == 200
        review = review_res.json()
        assert "id" in review
        run_id = review["id"]
        assert review["total_risks"] >= 0
        assert review["total_obligations"] >= 0

        # 5. Knowledge Graph Sync & Verification
        graph_res = client.get(f"/api/vaults/{vault_id}/graph")
        assert graph_res.status_code == 200
        graph = graph_res.json()
        assert len(graph["nodes"]) > 0
        assert len(graph["edges"]) >= 0

        # 6. Personal Note Creation with Citation
        note_res = client.post(
            f"/api/vaults/{vault_id}/notes",
            json={
                "title": "E2E Summary Note",
                "content_md": f"Audited [[commercial_agreement.pdf]]. Discovered {review['total_risks']} risks. #e2e #test"
            }
        )
        assert note_res.status_code == 200
        note = note_res.json()
        assert note["title"] == "E2E Summary Note"

        # 7. Deliverable Package Export (.ZIP)
        export_res = client.get(f"/api/vaults/{vault_id}/documents/{doc_id}/review-runs/{run_id}/export")
        assert export_res.status_code == 200
        assert export_res.headers.get("content-type") == "application/zip"
        assert len(export_res.content) > 100

    finally:
        # Cleanup
        client.delete(f"/api/vaults/{vault_id}")

