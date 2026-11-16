# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import json
from pathlib import Path
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings
from app.services.storage_manager import storage_manager

# Ensure storage directories exist
storage_manager.initialize_dirs()

# Database path: ~/.sovereigndoc/db/metadata.db
db_path = storage_manager.db_dir / "metadata.db"
DATABASE_URL = f"sqlite:///{db_path}"

# SQLite connection with thread safety
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables in metadata.db if they do not exist and run migrations."""
    import app.db.models  # Ensure models are registered
    Base.metadata.create_all(bind=engine)

    # Lightweight column migrations for existing SQLite databases
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(documents)")
        cols = [row[1] for row in cursor.fetchall()]
        if "file_path" not in cols:
            cursor.execute("ALTER TABLE documents ADD COLUMN file_path TEXT")
            conn.commit()

        # ChatSession document_id migration & index
        cursor.execute("PRAGMA table_info(chat_sessions)")
        cs_cols = [row[1] for row in cursor.fetchall()]
        if "document_id" not in cs_cols:
            cursor.execute("ALTER TABLE chat_sessions ADD COLUMN document_id TEXT REFERENCES documents(id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_document_id ON chat_sessions(document_id)")
            conn.commit()

            # Conservative backfill: inspect messages for evidence document_id
            cursor.execute("SELECT id FROM chat_sessions WHERE document_id IS NULL")
            sessions = cursor.fetchall()
            for (sess_id,) in sessions:
                cursor.execute("SELECT evidence_json FROM chat_messages WHERE session_id = ? AND evidence_json IS NOT NULL", (sess_id,))
                msg_evs = cursor.fetchall()
                unique_docs = set()
                for (ev_raw,) in msg_evs:
                    if ev_raw:
                        try:
                            items = json.loads(ev_raw)
                            for it in items:
                                if isinstance(it, dict) and it.get("document_id"):
                                    unique_docs.add(it["document_id"])
                        except Exception:
                            pass
                if len(unique_docs) == 1:
                    cursor.execute("UPDATE chat_sessions SET document_id = ? WHERE id = ?", (list(unique_docs)[0], sess_id))
            conn.commit()
        else:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_document_id ON chat_sessions(document_id)")
            conn.commit()

        # Milestone 5 & 6: Ensure indexes and forward-compatible GraphRAG columns on graph_nodes & graph_edges
        cursor.execute("PRAGMA table_info(graph_nodes)")
        gn_cols = [row[1] for row in cursor.fetchall()]
        if "node_embedding" not in gn_cols:
            cursor.execute("ALTER TABLE graph_nodes ADD COLUMN node_embedding TEXT")

        cursor.execute("PRAGMA table_info(graph_edges)")
        ge_cols = [row[1] for row in cursor.fetchall()]
        if "metadata_json" not in ge_cols:
            cursor.execute("ALTER TABLE graph_edges ADD COLUMN metadata_json TEXT DEFAULT '{}'")

        # Milestone 6.1: Versioned Disclaimer Acceptance on workspace_state
        cursor.execute("PRAGMA table_info(workspace_state)")
        ws_cols = [row[1] for row in cursor.fetchall()]
        if "accepted_disclaimer_version" not in ws_cols:
            cursor.execute("ALTER TABLE workspace_state ADD COLUMN accepted_disclaimer_version TEXT")
        if "disclaimer_accepted_at" not in ws_cols:
            cursor.execute("ALTER TABLE workspace_state ADD COLUMN disclaimer_accepted_at DATETIME")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_vault_doc ON notes(vault_id, document_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_vault_title ON notes(vault_id, title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_graph_nodes_vault_entity ON graph_nodes(vault_id, entity_type, entity_id)")
        conn.commit()

        conn.close()

        # Synchronize existing DOCX chunk pagination & clause header metadata
        try:
            from app.db.models import Document
            from app.services.rag.document_parser import document_parser
            from app.api.routes_documents import sync_document_chunks_metadata

            db = SessionLocal()
            try:
                docx_docs = db.query(Document).filter(Document.file_type == ".docx").all()
                for doc in docx_docs:
                    file_path = Path(doc.file_path) if doc.file_path and Path(doc.file_path).exists() else (
                        storage_manager.get_vault_path(doc.vault_id) / f"{doc.id}_{doc.filename}"
                    )
                    if file_path and file_path.exists():
                        paginated = document_parser.paginate_docx(file_path, include_html=False)
                        sync_document_chunks_metadata(
                            db=db,
                            doc=doc,
                            blocks=paginated["blocks"],
                            page_count=paginated["page_count"]
                        )
            finally:
                db.close()
        except Exception:
            pass
