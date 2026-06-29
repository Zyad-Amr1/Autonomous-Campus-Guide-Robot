"""Local document ingestion for RAG knowledge chunks."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

from controllers.rag.text_cleaner import clean_text, detect_language, split_text_into_chunks


SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".pdf"}


def ingest_text_file(path: str | Path) -> list[dict[str, Any]]:
    """Ingest a local TXT or Markdown file into chunks."""
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8-sig")
    except OSError:
        return []
    return _chunks_from_text(clean_text(text), file_path, file_path.suffix.lower())


def ingest_csv_file(path: str | Path) -> list[dict[str, Any]]:
    """Ingest a CSV file by converting rows into readable text."""
    file_path = Path(path)
    rows: list[str] = []
    try:
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames:
                for index, row in enumerate(reader, start=1):
                    values = [f"{key}: {value}" for key, value in row.items() if value not in (None, "")]
                    if values:
                        rows.append(f"Row {index}. " + ". ".join(values))
            else:
                handle.seek(0)
                for index, row in enumerate(csv.reader(handle), start=1):
                    if any(cell.strip() for cell in row):
                        rows.append(f"Row {index}. " + ". ".join(cell.strip() for cell in row if cell.strip()))
    except (OSError, csv.Error):
        return []
    return _chunks_from_text(clean_text("\n".join(rows)), file_path, ".csv")


def ingest_pdf_file(path: str | Path) -> list[dict[str, Any]]:
    """Ingest a PDF with pypdf when available; fail safely otherwise."""
    file_path = Path(path)
    try:
        from pypdf import PdfReader
    except ImportError:
        return []

    try:
        reader = PdfReader(str(file_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return []
    return _chunks_from_text(clean_text(text), file_path, ".pdf")


def ingest_document(path: str | Path) -> list[dict[str, Any]]:
    """Ingest one supported local document."""
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return ingest_text_file(file_path)
    if suffix == ".csv":
        return ingest_csv_file(file_path)
    if suffix == ".pdf":
        return ingest_pdf_file(file_path)
    return []


def ingest_folder(folder_path: str | Path) -> list[dict[str, Any]]:
    """Ingest every supported file under a folder."""
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        return []
    chunks: list[dict[str, Any]] = []
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            chunks.extend(ingest_document(path))
    return chunks


def _chunks_from_text(text: str, file_path: Path, file_type: str) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    title = file_path.stem.replace("_", " ").replace("-", " ").strip() or file_path.name
    for index, chunk_text in enumerate(split_text_into_chunks(text), start=1):
        chunks.append(
            {
                "id": f"document:{_stable_id(file_path)}:{index}",
                "source": "document",
                "title": title,
                "content": chunk_text,
                "keywords": _keywords(title, chunk_text, file_type),
                "language": detect_language(chunk_text),
                "metadata": {
                    "file_path": str(file_path),
                    "file_type": file_type.lstrip("."),
                    "chunk_index": index,
                },
            }
        )
    return chunks


def _stable_id(path: Path) -> str:
    return hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:16]


def _keywords(*parts: str) -> list[str]:
    seen: set[str] = set()
    keywords: list[str] = []
    for token in clean_text(" ".join(parts)).casefold().replace(".", " ").replace(",", " ").split():
        token = token.strip("_?؟.,،:;!()[]{}")
        if len(token) < 2 or token in seen:
            continue
        seen.add(token)
        keywords.append(token)
    return keywords

