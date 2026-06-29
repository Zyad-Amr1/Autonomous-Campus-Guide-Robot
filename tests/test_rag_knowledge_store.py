"""Tests for the persistent RAG knowledge store."""

from __future__ import annotations

import sqlite3

from controllers.rag.knowledge_store import (
    clear_knowledge_dirty,
    get_knowledge_status_summary,
    get_sync_status,
    init_knowledge_store,
    is_knowledge_dirty,
    load_knowledge_chunks,
    mark_knowledge_dirty,
    search_knowledge_chunks,
    set_sync_status,
    upsert_knowledge_chunks,
)


def _chunk(chunk_id: str = "rooms:1", title: str = "Cafeteria") -> dict:
    return {
        "id": chunk_id,
        "source": "rooms",
        "title": title,
        "content": "Food court in the Student Center.",
        "keywords": ["cafeteria", "food", "student"],
        "language": "en",
        "metadata": {"row_id": 1},
    }


def test_init_creates_knowledge_chunks_table(tmp_path) -> None:
    db_path = tmp_path / "knowledge.db"

    init_knowledge_store(db_path)

    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'knowledge_chunks'"
        ).fetchone()
    finally:
        connection.close()
    assert row is not None


def test_init_creates_sync_status_table(tmp_path) -> None:
    db_path = tmp_path / "knowledge.db"

    init_knowledge_store(db_path)

    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'rag_sync_status'"
        ).fetchone()
    finally:
        connection.close()
    assert row is not None


def test_upsert_inserts_chunks(tmp_path) -> None:
    db_path = tmp_path / "knowledge.db"

    count = upsert_knowledge_chunks(db_path, [_chunk()])

    assert count == 1
    assert load_knowledge_chunks(db_path)[0]["title"] == "Cafeteria"


def test_upsert_updates_existing_chunks(tmp_path) -> None:
    db_path = tmp_path / "knowledge.db"
    upsert_knowledge_chunks(db_path, [_chunk()])
    updated = _chunk(title="Main Cafeteria")
    updated["content"] = "Updated food court near Building B."

    upsert_knowledge_chunks(db_path, [updated])

    chunks = load_knowledge_chunks(db_path)
    assert len(chunks) == 1
    assert chunks[0]["title"] == "Main Cafeteria"
    assert "Updated food court" in chunks[0]["content"]


def test_load_returns_chunks(tmp_path) -> None:
    db_path = tmp_path / "knowledge.db"
    upsert_knowledge_chunks(db_path, [_chunk(), _chunk("faculties:1", "Engineering")])

    chunks = load_knowledge_chunks(db_path)

    assert len(chunks) == 2
    assert {chunk["id"] for chunk in chunks} == {"rooms:1", "faculties:1"}


def test_search_returns_relevant_chunks(tmp_path) -> None:
    db_path = tmp_path / "knowledge.db"
    upsert_knowledge_chunks(db_path, [_chunk(), _chunk("faculties:1", "Engineering")])

    results = search_knowledge_chunks("Where is cafeteria?", db_path)

    assert results
    assert results[0]["id"] == "rooms:1"


def test_search_returns_empty_for_unrelated_query(tmp_path) -> None:
    db_path = tmp_path / "knowledge.db"
    upsert_knowledge_chunks(db_path, [_chunk()])

    assert search_knowledge_chunks("parking permits on Mars", db_path) == []


def test_invalid_optional_metadata_does_not_crash(tmp_path) -> None:
    db_path = tmp_path / "knowledge.db"
    chunk = _chunk()
    chunk["keywords"] = None
    chunk["metadata"] = None

    upsert_knowledge_chunks(db_path, [chunk])

    loaded = load_knowledge_chunks(db_path)[0]
    assert loaded["keywords"] == []
    assert loaded["metadata"] == {}


def test_sync_status_round_trips(tmp_path) -> None:
    db_path = tmp_path / "knowledge.db"

    set_sync_status(db_path, "last_database_sync", "2026-06-29T10:00:00+00:00")

    assert get_sync_status(db_path, "last_database_sync") == "2026-06-29T10:00:00+00:00"
    assert get_sync_status(db_path, "missing", "default") == "default"


def test_mark_and_clear_dirty(tmp_path) -> None:
    db_path = tmp_path / "knowledge.db"

    mark_knowledge_dirty(db_path, "Courses data changed")

    assert is_knowledge_dirty(db_path) is True
    assert get_sync_status(db_path, "dirty_reason") == "Courses data changed"

    clear_knowledge_dirty(db_path)

    assert is_knowledge_dirty(db_path) is False
    assert get_sync_status(db_path, "dirty_reason") == ""


def test_status_summary_includes_chunks_sources_and_metadata(tmp_path) -> None:
    db_path = tmp_path / "knowledge.db"
    faq_chunk = _chunk("faq:1", "Admissions")
    faq_chunk["source"] = "faq"
    upsert_knowledge_chunks(db_path, [_chunk(), faq_chunk])
    mark_knowledge_dirty(db_path, "FAQ data changed")
    set_sync_status(db_path, "last_database_sync", "2026-06-29T10:00:00+00:00")

    summary = get_knowledge_status_summary(db_path)

    assert summary["dirty"] is True
    assert summary["dirty_reason"] == "FAQ data changed"
    assert summary["last_database_sync"] == "2026-06-29T10:00:00+00:00"
    assert summary["chunk_count"] == 2
    assert summary["sources"] == {"faq": 1, "rooms": 1}


def test_status_summary_without_metadata_does_not_crash(tmp_path) -> None:
    summary = get_knowledge_status_summary(tmp_path / "empty.db")

    assert summary["dirty"] is False
    assert summary["dirty_reason"] == ""
    assert summary["chunk_count"] == 0
    assert summary["sources"] == {}
