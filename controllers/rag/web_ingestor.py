"""Website ingestion for local RAG knowledge chunks."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from controllers.rag.source_config import load_web_sources
from controllers.rag.text_cleaner import clean_text, detect_language, split_text_into_chunks


def fetch_web_page(url: str, timeout: int = 15) -> str:
    """Fetch one web page as text; return empty string on failure."""
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "ECU-Guidance-Robot/1.0"})
        response.raise_for_status()
        return response.text
    except Exception:
        return ""


def extract_visible_text_from_html(html: str) -> str:
    """Extract visible page text while removing common noisy elements."""
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "form"]):
        tag.decompose()
    return clean_text(soup.get_text("\n"))


def ingest_web_page(url: str, title: str | None = None) -> list[dict[str, Any]]:
    """Fetch, clean, and chunk a website page."""
    html = fetch_web_page(url)
    if not html:
        return []
    text = extract_visible_text_from_html(html)
    page_title = title or _title_from_html(html) or url
    chunks: list[dict[str, Any]] = []
    for index, chunk_text in enumerate(split_text_into_chunks(text), start=1):
        chunks.append(
            {
                "id": f"website:{_stable_id(url)}:{index}",
                "source": "website",
                "title": page_title,
                "content": chunk_text,
                "keywords": _keywords(page_title, chunk_text, url),
                "language": detect_language(chunk_text),
                "metadata": {
                    "url": url,
                    "chunk_index": index,
                },
            }
        )
    return chunks


def ingest_web_sources_config(config_path: str | Path) -> list[dict[str, Any]]:
    """Ingest all enabled website sources from a JSON config file."""
    chunks: list[dict[str, Any]] = []
    for source in load_web_sources(config_path):
        if not source.get("enabled", True):
            continue
        url = str(source.get("url") or "").strip()
        if not url:
            continue
        chunks.extend(ingest_web_page(url, title=source.get("name")))
    return chunks


def _title_from_html(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    title = soup.find("title")
    return clean_text(title.get_text(" ")) if title else ""


def _stable_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


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
