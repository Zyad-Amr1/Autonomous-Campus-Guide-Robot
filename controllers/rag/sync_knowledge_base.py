"""Synchronize managed database content into the persistent RAG store."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from controllers.rag.knowledge_chunker import build_knowledge_chunks
from controllers.rag.knowledge_store import (
    clear_generated_database_chunks,
    init_knowledge_store,
    set_sync_status,
    upsert_knowledge_chunks,
)
from database.connection import DB_NAME


def sync_database_to_knowledge_base(db_path: str | Path = DB_NAME) -> dict:
    """Rebuild persistent chunks from managed university database tables."""
    chunks = build_knowledge_chunks(db_path)
    init_knowledge_store(db_path)
    clear_generated_database_chunks(db_path)
    upsert_knowledge_chunks(db_path, chunks)
    set_sync_status(db_path, "last_database_sync", datetime.now(timezone.utc).isoformat(timespec="seconds"))

    sources: dict[str, int] = {}
    for chunk in chunks:
        source = str(chunk.get("source", ""))
        sources[source] = sources.get(source, 0) + 1
    return {
        "chunks_created": len(chunks),
        "sources": sources,
    }
