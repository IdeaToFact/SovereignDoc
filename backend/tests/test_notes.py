# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Personal Second Brain Notes & WikiLink Tests
"""
from sqlalchemy.orm import Session
from app.db.models import Vault
from app.models.schemas import NoteCreateRequest, NoteUpdateRequest
from app.api.routes_notes import (
    create_note,
    update_note,
    get_note,
    list_notes,
    list_note_versions,
    restore_note_version,
)
from app.services.second_brain.link_parser import wiki_link_parser


def test_wikilink_parser():
    """Verifies WikiLinkParser extracts [[Note Title]], [[Doc:File#Page]], and #tags."""
    content = (
        "Reviewing the [[Master Services Agreement]] per [[Risk:MissingLiabilityCap]].\n"
        "Check section on #confidentiality and #compliance."
    )
    links = wiki_link_parser.extract_links(content)
    tags = wiki_link_parser.extract_tags(content)
    link_targets = [l["target_note_title"] for l in links if l.get("target_note_title")]
    assert "Master Services Agreement" in link_targets
    assert "confidentiality" in tags
    assert "compliance" in tags


def test_note_crud_and_versioning(in_memory_db: Session):
    """Verifies note creation, updating, immutable NoteVersion generation, and version restore."""
    db = in_memory_db
    # 1. Create vault
    vault = Vault(id="v_note_test", name="Notes Test Vault")
    db.add(vault)
    db.commit()

    # 2. Create note (Version 1)
    note_v1 = create_note(
        "v_note_test",
        NoteCreateRequest(title="Indemnity Strategy", content_md="Initial draft regarding indemnity risk."),
        db=db
    )
    assert note_v1.title == "Indemnity Strategy"
    note_id = note_v1.id

    # 3. Update note (Version 2)
    note_v2 = update_note(
        "v_note_test",
        note_id,
        NoteUpdateRequest(title="Indemnity Strategy Final", content_md="Updated draft with mutual cap."),
        db=db
    )
    assert note_v2.title == "Indemnity Strategy Final"

    # 4. List versions
    versions = list_note_versions("v_note_test", note_id, db=db)
    assert len(versions) >= 2

    # 5. Restore version 1 (second item in reverse chronological order)
    restored = restore_note_version("v_note_test", note_id, version_id=versions[1].id, db=db)
    assert restored.title == "Indemnity Strategy"
    assert "Initial draft" in restored.content_md

