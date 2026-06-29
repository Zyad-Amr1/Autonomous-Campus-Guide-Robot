"""Tests for syncing managed database rows into persistent RAG chunks."""

from __future__ import annotations

import sqlite3

from controllers.rag.knowledge_store import get_sync_status, load_knowledge_chunks, search_knowledge_chunks
from controllers.rag.sync_external_sources import sync_external_sources_to_knowledge_base
from controllers.rag.sync_knowledge_base import sync_database_to_knowledge_base
from database.init_db import initialize_database


def _db(tmp_path):
    db_path = tmp_path / "sync.db"
    initialize_database(db_path)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            INSERT INTO faculties (name, description, building, dean_name)
            VALUES (?, ?, ?, ?)
            """,
            ("Engineering", "Engineering and robotics programs.", "Building A", "Dr. Adel"),
        )
        connection.execute(
            """
            INSERT INTO rooms (room_name, room_number, building, floor, category, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("Cafeteria", "C-01", "Student Center", 1, "Service", "Food court and student break area."),
        )
        connection.execute(
            """
            INSERT INTO faq (question, answer, keywords, category)
            VALUES (?, ?, ?, ?)
            """,
            ("Where is student affairs?", "Student affairs is in Building B.", "student affairs services", "services"),
        )
        connection.commit()
    finally:
        connection.close()
    return db_path


def test_fake_sqlite_database_creates_chunks(tmp_path) -> None:
    db_path = _db(tmp_path)

    summary = sync_database_to_knowledge_base(db_path)

    chunks = load_knowledge_chunks(db_path)
    assert summary["chunks_created"] == len(chunks)
    assert summary["sources"]["faculties"] == 1
    assert summary["sources"]["rooms"] == 1
    assert summary["sources"]["faq"] == 1


def test_sync_returns_chunk_count(tmp_path) -> None:
    summary = sync_database_to_knowledge_base(_db(tmp_path))

    assert summary["chunks_created"] >= 3
    assert sum(summary["sources"].values()) == summary["chunks_created"]


def test_synced_chunks_are_searchable(tmp_path) -> None:
    db_path = _db(tmp_path)
    sync_database_to_knowledge_base(db_path)

    results = search_knowledge_chunks("Where is cafeteria?", db_path)

    assert results
    assert results[0]["source"] == "rooms"
    assert "Cafeteria" in results[0]["title"]


def test_database_sync_updates_last_database_sync(tmp_path) -> None:
    db_path = _db(tmp_path)

    sync_database_to_knowledge_base(db_path)

    assert get_sync_status(db_path, "last_database_sync")


def test_external_sync_updates_last_external_sync(tmp_path) -> None:
    db_path = _db(tmp_path)

    sync_external_sources_to_knowledge_base(db_path, tmp_path / "knowledge_sources")

    assert get_sync_status(db_path, "last_external_sync")
