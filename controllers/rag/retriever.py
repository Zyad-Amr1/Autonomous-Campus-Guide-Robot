"""Simple deterministic retriever for public chatbot RAG chunks."""

from __future__ import annotations

import re
from typing import Any

from controllers.rag.query_analyzer import (
    detect_intent,
    extract_keywords,
    normalize_query,
)


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
    "document": {"document", "documents", "file", "files", "pdf", "manual", "\u0645\u0644\u0641", "\u0645\u0633\u062a\u0646\u062f"},
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
_INTENT_SOURCES = {
    "faculty_info": {"faculties", "faq", "website", "document"},
    "professor_info": {"professors", "faq", "website", "document"},
    "room_location": {"rooms", "faq", "website", "document"},
    "course_schedule": {"courses", "faq", "website", "document"},
    "event_info": {"events", "faq", "website", "document"},
    "admission_info": {"faq", "website", "document", "faculties"},
    "general_info": {"faq", "website", "document", "faculties"},
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
    intent: str | None = None,
) -> list[dict[str, Any]]:
    """Return best matching chunks sorted by deterministic hybrid relevance."""
    normalized_question = normalize_query(question)
    question_keywords = set(extract_keywords(question))
    question_tokens = _tokens(normalized_question)
    detected_intent = intent or detect_intent(question)
    if not question_tokens and not question_keywords:
        return []

    scored: list[dict[str, Any]] = []
    for chunk in chunks:
        source = str(chunk.get("source", ""))
        title = str(chunk.get("title", ""))
        content = str(chunk.get("content", ""))
        keyword_text = " ".join(str(keyword) for keyword in chunk.get("keywords", []))
        normalized_title = normalize_query(title)
        normalized_content = normalize_query(content)
        normalized_chunk_text = normalize_query(
            f"{source} {title} {content} {keyword_text}"
        )
        chunk_tokens = _chunk_tokens(chunk)
        chunk_keywords = set(extract_keywords(normalized_chunk_text))
        overlap = (question_tokens | question_keywords) & (chunk_tokens | chunk_keywords)
        alias_overlap = question_tokens & _SOURCE_ALIASES.get(source, set())
        title_tokens = _tokens(normalized_title)
        title_overlap = (question_tokens | question_keywords) & title_tokens
        source_bonus = 0
        if detected_intent and source in _INTENT_SOURCES.get(detected_intent, set()):
            source_bonus = 8

        phrase_bonus = 0
        if normalized_question and normalized_question == normalized_title:
            phrase_bonus += 28
        elif normalized_question and normalized_question in normalized_title:
            phrase_bonus += 18
        elif normalized_question and normalized_question in normalized_content:
            phrase_bonus += 12

        base_score = (
            (len(overlap) * 5)
            + (len(title_overlap) * 7)
            + (len(alias_overlap) * 3)
            + phrase_bonus
        )
        if base_score <= 0:
            continue
        score = base_score + source_bonus
        if score <= 0:
            continue
        result = dict(chunk)
        result["score"] = score
        result["intent"] = detected_intent
        scored.append(result)

    scored.sort(
        key=lambda item: (
            -int(item["score"]),
            _SOURCE_PRIORITY.get(str(item.get("source", "")), 99),
            str(item.get("title", "")),
        )
    )
    return scored[: max(1, int(limit))]
