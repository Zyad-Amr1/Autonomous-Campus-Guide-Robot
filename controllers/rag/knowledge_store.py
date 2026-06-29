"""Persistent SQLite store for generated RAG knowledge chunks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from database.connection import DB_NAME, get_connection


_WORD_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
_STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "available",
    "can",
    "do",
    "does",
    "find",
    "for",
    "how",
    "i",
    "in",
    "is",
    "me",
    "of",
    "on",
    "tell",
    "the",
    "there",
    "to",
    "what",
    "where",
    "who",
    "\u0639\u0646",
    "\u0641\u064a",
    "\u0645\u0627",
    "\u0645\u0646",
    "\u0647\u064a",
    "\u0647\u0648",
    "\u0627\u064a\u0646",
    "\u0623\u064a\u0646",
}
_SOURCE_ALIASES = {
    "faculties": {"faculty", "faculties", "college", "colleges", "\u0643\u0644\u064a\u0629", "\u0627\u0644\u0643\u0644\u064a\u0627\u062a", "\u0643\u0644\u064a\u0627\u062a"},
    "professors": {"professor", "professors", "doctor", "doctors", "staff", "\u062f\u0643\u062a\u0648\u0631", "\u062f\u0643\u0627\u062a\u0631\u0629", "\u0627\u0633\u062a\u0627\u0630", "\u0623\u0633\u0627\u062a\u0630\u0629"},
    "rooms": {"room", "rooms", "hall", "halls", "\u0642\u0627\u0639\u0629", "\u0642\u0627\u0639\u0627\u062a"},
    "courses": {"course", "courses", "schedule", "class", "classes", "\u062c\u062f\u0648\u0644", "\u062c\u062f\u0627\u0648\u0644", "\u0645\u0642\u0631\u0631", "\u0645\u0642\u0631\u0631\u0627\u062a"},
    "events": {"event", "events", "news", "activity", "activities", "\u0641\u0639\u0627\u0644\u064a\u0629", "\u0641\u0639\u0627\u0644\u064a\u0627\u062a", "\u0627\u062e\u0628\u0627\u0631", "\u0623\u062e\u0628\u0627\u0631"},
    "faq": {"faq", "question", "questions", "help", "\u0633\u0624\u0627\u0644", "\u0627\u0633\u0626\u0644\u0629", "\u0623\u0633\u0626\u0644\u0629"},
    "website": {"website", "web", "page", "pages", "site", "admission", "admissions", "\u0645\u0648\u0642\u0639", "\u0642\u0628\u0648\u0644"},
    "document": {"document", "documents", "file", "files", "pdf", "csv", "manual", "\u0645\u0644\u0641", "\u0645\u0633\u062a\u0646\u062f"},
}
_SOURCE_PRIORITY = {
    "faq": 0,
    "rooms": 1,
    "faculties": 2,
    "professors": 3,
    "courses": 4,
    "events": 5,
    "website": 6,
    "document": 7,
}


def init_knowledge_store(db_path: str | Path = DB_NAME) -> None:
    """Create the persistent knowledge chunk table if it is missing."""
    connection = get_connection(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id TEXT PRIMARY KEY,
                source TEXT,
                title TEXT,
                content TEXT,
                keywords TEXT,
                language TEXT,
                metadata TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def clear_knowledge_chunks(db_path: str | Path = DB_NAME) -> None:
    """Remove all stored knowledge chunks."""
    init_knowledge_store(db_path)
    connection = get_connection(db_path)
    try:
        connection.execute("DELETE FROM knowledge_chunks")
        connection.commit()
    finally:
        connection.close()


def clear_generated_database_chunks(db_path: str | Path = DB_NAME) -> None:
    """Remove chunks generated from managed database sources."""
    init_knowledge_store(db_path)
    connection = get_connection(db_path)
    try:
        connection.execute(
            """
            DELETE FROM knowledge_chunks
            WHERE source IN ('faculties', 'professors', 'rooms', 'courses', 'events', 'faq')
            """
        )
        connection.commit()
    finally:
        connection.close()


def clear_external_chunks(db_path: str | Path = DB_NAME) -> None:
    """Remove website and document chunks without touching database-generated chunks."""
    init_knowledge_store(db_path)
    connection = get_connection(db_path)
    try:
        connection.execute("DELETE FROM knowledge_chunks WHERE source IN ('website', 'document')")
        connection.commit()
    finally:
        connection.close()


def upsert_knowledge_chunks(db_path: str | Path, chunks: list[dict[str, Any]]) -> int:
    """Insert or update knowledge chunks and return the number processed."""
    init_knowledge_store(db_path)
    connection = get_connection(db_path)
    try:
        for chunk in chunks:
            connection.execute(
                """
                INSERT INTO knowledge_chunks (
                    id, source, title, content, keywords, language, metadata, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    source = excluded.source,
                    title = excluded.title,
                    content = excluded.content,
                    keywords = excluded.keywords,
                    language = excluded.language,
                    metadata = excluded.metadata,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    str(chunk.get("id", "")),
                    str(chunk.get("source", "")),
                    str(chunk.get("title", "")),
                    str(chunk.get("content", "")),
                    json.dumps(_safe_list(chunk.get("keywords")), ensure_ascii=False),
                    str(chunk.get("language") or "en"),
                    json.dumps(_safe_dict(chunk.get("metadata")), ensure_ascii=False),
                ),
            )
        connection.commit()
        return len(chunks)
    finally:
        connection.close()


def load_knowledge_chunks(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    """Load all persisted knowledge chunks."""
    init_knowledge_store(db_path)
    connection = get_connection(db_path)
    try:
        rows = connection.execute(
            """
            SELECT id, source, title, content, keywords, language, metadata, updated_at
            FROM knowledge_chunks
            ORDER BY source, title, id
            """
        ).fetchall()
    finally:
        connection.close()
    return [_row_to_chunk(row) for row in rows]


def search_knowledge_chunks(
    query: str,
    db_path: str | Path = DB_NAME,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Search persisted chunks by source, title, content, and keywords."""
    chunks = load_knowledge_chunks(db_path)
    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    results: list[dict[str, Any]] = []
    for chunk in chunks:
        chunk_tokens = _tokens(
            f"{chunk['source']} {chunk['title']} {chunk['content']} {' '.join(chunk['keywords'])}"
        )
        title_tokens = _tokens(chunk["title"])
        source_aliases = _SOURCE_ALIASES.get(chunk["source"], set())
        overlap = query_tokens & chunk_tokens
        title_overlap = query_tokens & title_tokens
        alias_overlap = query_tokens & source_aliases
        score = (len(overlap) * 4) + (len(title_overlap) * 4) + (len(alias_overlap) * 2)
        if score <= 0:
            continue
        result = dict(chunk)
        result["score"] = score
        results.append(result)

    results.sort(
        key=lambda chunk: (
            -int(chunk["score"]),
            _SOURCE_PRIORITY.get(chunk["source"], 99),
            chunk["title"],
        )
    )
    return results[: max(1, int(limit))]


def _row_to_chunk(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "source": row["source"] or "",
        "title": row["title"] or "",
        "content": row["content"] or "",
        "keywords": _safe_json_list(row["keywords"]),
        "language": row["language"] or "en",
        "metadata": _safe_json_dict(row["metadata"]),
        "updated_at": row["updated_at"],
    }


def _safe_json_list(value: Any) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def _safe_json_dict(value: Any) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw_token in _WORD_RE.findall(text.casefold()):
        token = raw_token.strip("_?؟.,،:;!()[]{}")
        if not token or token in _STOPWORDS:
            continue
        tokens.add(token)
        if token.startswith("\u0627\u0644") and len(token) > 2:
            tokens.add(token[2:])
    return tokens
