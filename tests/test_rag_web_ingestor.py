"""Tests for website ingestion without real internet calls."""

from __future__ import annotations

from controllers.rag.web_ingestor import (
    extract_visible_text_from_html,
    fetch_web_page,
    ingest_web_page,
)


HTML = """
<html>
  <head><title>ECU Page</title><style>.x{}</style><script>bad()</script></head>
  <body>
    <nav>Navigation noise</nav>
    <main><h1>ECU Faculties</h1><p>Engineering and Pharmacy information.</p></main>
    <footer>Footer noise</footer>
  </body>
</html>
"""


def test_visible_text_extracted_from_html() -> None:
    text = extract_visible_text_from_html(HTML)

    assert "ECU Faculties" in text
    assert "Engineering and Pharmacy" in text


def test_script_style_removed() -> None:
    text = extract_visible_text_from_html(HTML)

    assert "bad()" not in text
    assert ".x" not in text
    assert "Navigation noise" not in text
    assert "Footer noise" not in text


def test_fake_web_page_creates_chunks(monkeypatch) -> None:
    monkeypatch.setattr("controllers.rag.web_ingestor.fetch_web_page", lambda url: HTML)

    chunks = ingest_web_page("https://example.edu", title="Example ECU")

    assert chunks
    assert chunks[0]["source"] == "website"
    assert chunks[0]["title"] == "Example ECU"
    assert "Engineering" in chunks[0]["content"]


def test_failed_request_does_not_crash(monkeypatch) -> None:
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: (_ for _ in ()).throw(Exception("down")))

    assert fetch_web_page("https://example.edu") == ""


def test_no_real_internet_calls(monkeypatch) -> None:
    called = False

    def fake_fetch(url):
        nonlocal called
        called = True
        return HTML

    monkeypatch.setattr("controllers.rag.web_ingestor.fetch_web_page", fake_fetch)

    chunks = ingest_web_page("https://example.edu")

    assert called is True
    assert chunks

