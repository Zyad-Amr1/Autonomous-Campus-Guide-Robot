"""Tests for syncing external website and document sources."""

from __future__ import annotations

from controllers.rag.knowledge_store import load_knowledge_chunks, search_knowledge_chunks
from controllers.rag.sync_external_sources import sync_external_sources_to_knowledge_base


HTML = "<html><body><main>ECU website admissions and faculties information.</main></body></html>"


def test_fake_web_sources_json_loads_enabled_sources(tmp_path, monkeypatch) -> None:
    root = tmp_path / "knowledge_sources"
    root.mkdir()
    (root / "web_sources.json").write_text(
        '{"sources": [{"name": "ECU", "url": "https://example.edu", "enabled": true}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr("controllers.rag.web_ingestor.fetch_web_page", lambda url: HTML)

    summary = sync_external_sources_to_knowledge_base(tmp_path / "rag.db", root)

    assert summary["website_chunks"] == 1
    assert summary["errors"] == []


def test_disabled_sources_ignored(tmp_path, monkeypatch) -> None:
    root = tmp_path / "knowledge_sources"
    root.mkdir()
    (root / "web_sources.json").write_text(
        '{"sources": [{"name": "ECU", "url": "https://example.edu", "enabled": false}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr("controllers.rag.web_ingestor.fetch_web_page", lambda url: HTML)

    summary = sync_external_sources_to_knowledge_base(tmp_path / "rag.db", root)

    assert summary["website_chunks"] == 0


def test_local_documents_are_synced(tmp_path) -> None:
    root = tmp_path / "knowledge_sources"
    docs = root / "documents"
    docs.mkdir(parents=True)
    (root / "web_sources.json").write_text('{"sources": []}', encoding="utf-8")
    (docs / "info.txt").write_text("ECU document about robotics labs.", encoding="utf-8")

    summary = sync_external_sources_to_knowledge_base(tmp_path / "rag.db", root)

    assert summary["document_chunks"] == 1


def test_chunks_inserted_into_knowledge_chunks(tmp_path, monkeypatch) -> None:
    root = tmp_path / "knowledge_sources"
    docs = root / "documents"
    docs.mkdir(parents=True)
    (root / "web_sources.json").write_text(
        '{"sources": [{"name": "ECU", "url": "https://example.edu", "enabled": true}]}',
        encoding="utf-8",
    )
    (docs / "info.txt").write_text("ECU document about robotics labs.", encoding="utf-8")
    monkeypatch.setattr("controllers.rag.web_ingestor.fetch_web_page", lambda url: HTML)
    db_path = tmp_path / "rag.db"

    sync_external_sources_to_knowledge_base(db_path, root)

    sources = {chunk["source"] for chunk in load_knowledge_chunks(db_path)}
    assert {"website", "document"} <= sources


def test_sync_summary_returns_counts(tmp_path, monkeypatch) -> None:
    root = tmp_path / "knowledge_sources"
    root.mkdir()
    (root / "web_sources.json").write_text(
        '{"sources": [{"name": "ECU", "url": "https://example.edu", "enabled": true}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr("controllers.rag.web_ingestor.fetch_web_page", lambda url: HTML)

    summary = sync_external_sources_to_knowledge_base(tmp_path / "rag.db", root)

    assert set(summary) == {"website_chunks", "document_chunks", "errors"}
    assert summary["website_chunks"] == 1
    assert summary["document_chunks"] == 0


def test_errors_reported_safely(tmp_path, monkeypatch) -> None:
    root = tmp_path / "knowledge_sources"
    root.mkdir()
    (root / "web_sources.json").write_text('{"sources": []}', encoding="utf-8")

    def failing_ingest(folder):
        raise RuntimeError("bad folder")

    (root / "documents").mkdir()
    monkeypatch.setattr("controllers.rag.sync_external_sources.ingest_folder", failing_ingest)

    summary = sync_external_sources_to_knowledge_base(tmp_path / "rag.db", root)

    assert summary["document_chunks"] == 0
    assert summary["errors"]


def test_synced_external_chunks_are_searchable(tmp_path) -> None:
    root = tmp_path / "knowledge_sources"
    docs = root / "documents"
    docs.mkdir(parents=True)
    (root / "web_sources.json").write_text('{"sources": []}', encoding="utf-8")
    (docs / "admissions.txt").write_text("Admission information for ECU students.", encoding="utf-8")
    db_path = tmp_path / "rag.db"

    sync_external_sources_to_knowledge_base(db_path, root)

    results = search_knowledge_chunks("admission information", db_path)
    assert results
    assert results[0]["source"] == "document"

