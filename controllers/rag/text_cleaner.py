"""Text cleaning and chunking helpers for external RAG sources."""

from __future__ import annotations

import re


_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
_ENGLISH_RE = re.compile(r"[A-Za-z]")


def clean_text(text: str) -> str:
    """Normalize text while preserving Arabic, English, and useful punctuation."""
    lines = [re.sub(r"\s+", " ", line).strip() for line in str(text or "").splitlines()]
    return "\n".join(line for line in lines if line)


def split_text_into_chunks(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    """Split long text into overlapping non-empty chunks."""
    cleaned = clean_text(text)
    if not cleaned:
        return []

    max_chars = max(100, int(max_chars))
    overlap = max(0, min(int(overlap), max_chars // 2))
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + max_chars)
        if end < len(cleaned):
            split_at = max(cleaned.rfind("\n", start, end), cleaned.rfind(". ", start, end))
            if split_at > start + max_chars // 2:
                end = split_at + 1
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks


def detect_language(text: str) -> str:
    """Detect whether text is Arabic, English, or mixed."""
    has_arabic = _ARABIC_RE.search(text or "") is not None
    has_english = _ENGLISH_RE.search(text or "") is not None
    if has_arabic and has_english:
        return "mixed"
    if has_arabic:
        return "ar"
    return "en"

