"""Compatibility helpers for searchable university context."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from controllers.rag.knowledge_chunker import build_knowledge_chunks
from controllers.rag.retriever import retrieve_relevant_chunks
from database.connection import DB_NAME


def get_university_context(db_path: str | Path = DB_NAME) -> dict[str, list[dict[str, Any]]]:
    """Return chunks grouped by source for legacy callers."""
    context: dict[str, list[dict[str, Any]]] = {
        "faculties": [],
        "professors": [],
        "rooms": [],
        "courses": [],
        "events": [],
        "faq": [],
    }
    for chunk in build_knowledge_chunks(db_path):
        context.setdefault(str(chunk["source"]), []).append(chunk)
    return context


def search_university_context(
    question: str,
    db_path: str | Path = DB_NAME,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Return best matching context snippets for a visitor question."""
    results: list[dict[str, Any]] = []
    for chunk in retrieve_relevant_chunks(question, build_knowledge_chunks(db_path), limit=limit):
        results.append(
            {
                "source_type": chunk["source"],
                "id": chunk["id"],
                "title": chunk["title"],
                "snippet": chunk["content"],
                "score": chunk.get("score", 0),
            }
        )
    return results

