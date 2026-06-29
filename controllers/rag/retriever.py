"""Simple deterministic retriever for public chatbot RAG chunks."""

from __future__ import annotations

import re
from typing import Any


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
}
_SOURCE_PRIORITY = {
    "faq": 0,
    "rooms": 1,
    "faculties": 2,
    "professors": 3,
    "courses": 4,
    "events": 5,
}


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


def _chunk_tokens(chunk: dict[str, Any]) -> set[str]:
    keyword_text = " ".join(str(keyword) for keyword in chunk.get("keywords", []))
    return _tokens(f"{chunk.get('source', '')} {chunk.get('title', '')} {chunk.get('content', '')} {keyword_text}")


def retrieve_relevant_chunks(
    question: str,
    chunks: list[dict[str, Any]],
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Return best matching chunks sorted by deterministic relevance score."""
    question_tokens = _tokens(question)
    if not question_tokens:
        return []

    scored: list[dict[str, Any]] = []
    for chunk in chunks:
        source = str(chunk.get("source", ""))
        chunk_tokens = _chunk_tokens(chunk)
        overlap = question_tokens & chunk_tokens
        alias_overlap = question_tokens & _SOURCE_ALIASES.get(source, set())
        title_tokens = _tokens(str(chunk.get("title", "")))
        title_overlap = question_tokens & title_tokens
        score = (len(overlap) * 4) + (len(title_overlap) * 4) + (len(alias_overlap) * 2)
        if score <= 0:
            continue
        result = dict(chunk)
        result["score"] = score
        scored.append(result)

    scored.sort(
        key=lambda item: (
            -int(item["score"]),
            _SOURCE_PRIORITY.get(str(item.get("source", "")), 99),
            str(item.get("title", "")),
        )
    )
    return scored[: max(1, int(limit))]

