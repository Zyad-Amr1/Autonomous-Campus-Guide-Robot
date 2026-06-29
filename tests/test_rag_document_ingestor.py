"""Tests for local document ingestion."""

from __future__ import annotations

from controllers.rag.document_ingestor import ingest_document, ingest_folder


def test_text_file_creates_chunks(tmp_path) -> None:
    path = tmp_path / "info.txt"
    path.write_text("ECU faculties include Engineering and Pharmacy.", encoding="utf-8")

    chunks = ingest_document(path)

    assert chunks
    assert chunks[0]["source"] == "document"
    assert "Engineering" in chunks[0]["content"]


def test_markdown_file_creates_chunks(tmp_path) -> None:
    path = tmp_path / "admissions.md"
    path.write_text("# Admissions\nStudents can ask about admission requirements.", encoding="utf-8")

    chunks = ingest_document(path)

    assert chunks
    assert chunks[0]["metadata"]["file_type"] == "md"
    assert "Admissions" in chunks[0]["content"]


def test_csv_file_creates_chunks(tmp_path) -> None:
    path = tmp_path / "rooms.csv"
    path.write_text("name,building\nCafeteria,Student Center\n", encoding="utf-8")

    chunks = ingest_document(path)

    assert chunks
    assert "Cafeteria" in chunks[0]["content"]
    assert chunks[0]["metadata"]["file_type"] == "csv"


def test_unsupported_file_returns_empty_safely(tmp_path) -> None:
    path = tmp_path / "image.png"
    path.write_text("not supported", encoding="utf-8")

    assert ingest_document(path) == []


def test_chunking_handles_long_text(tmp_path) -> None:
    path = tmp_path / "long.txt"
    path.write_text("ECU " * 1000, encoding="utf-8")

    chunks = ingest_document(path)

    assert len(chunks) > 1
    assert all(chunk["content"] for chunk in chunks)


def test_arabic_text_is_preserved(tmp_path) -> None:
    path = tmp_path / "arabic.txt"
    path.write_text("مرحبا بكم في كليات الجامعة المصرية الصينية.", encoding="utf-8")

    chunks = ingest_document(path)

    assert chunks
    assert "كليات" in chunks[0]["content"]
    assert chunks[0]["language"] in {"ar", "mixed"}


def test_ingest_folder_reads_supported_files(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("Engineering faculty.", encoding="utf-8")
    (tmp_path / "b.md").write_text("Robotics lab.", encoding="utf-8")
    (tmp_path / "ignore.png").write_text("ignore", encoding="utf-8")

    chunks = ingest_folder(tmp_path)

    assert len(chunks) == 2

