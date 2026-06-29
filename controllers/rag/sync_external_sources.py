"""Synchronize external website and document sources into the RAG store."""

from __future__ import annotations

from pathlib import Path

from controllers.rag.document_ingestor import ingest_folder
from controllers.rag.knowledge_store import (
    clear_external_chunks,
    init_knowledge_store,
    upsert_knowledge_chunks,
)
from controllers.rag.web_ingestor import ingest_web_sources_config
from database.connection import DB_NAME


def sync_external_sources_to_knowledge_base(
    db_path=DB_NAME,
    sources_root: str | Path = "knowledge_sources",
) -> dict:
    """Ingest configured websites and local documents into knowledge_chunks."""
    root = Path(sources_root)
    errors: list[str] = []
    init_knowledge_store(db_path)
    clear_external_chunks(db_path)

    website_chunks = []
    web_config = root / "web_sources.json"
    if web_config.exists():
        try:
            website_chunks = ingest_web_sources_config(web_config)
        except Exception as error:
            errors.append(f"web_sources.json: {error}")

    document_chunks = []
    documents_folder = root / "documents"
    if documents_folder.exists():
        try:
            document_chunks = ingest_folder(documents_folder)
        except Exception as error:
            errors.append(f"documents: {error}")

    upsert_knowledge_chunks(db_path, website_chunks + document_chunks)
    return {
        "website_chunks": len(website_chunks),
        "document_chunks": len(document_chunks),
        "errors": errors,
    }

