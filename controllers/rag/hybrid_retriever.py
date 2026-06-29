"""Hybrid retrieval for ECU chatbot knowledge chunks."""

from __future__ import annotations

from typing import Any

from controllers.rag.query_analyzer import (
    detect_intent,
    extract_keywords,
    normalize_query,
)


_INTENT_SOURCES = {
    "faculty_info": {"faculties", "faq", "website", "document"},
    "professor_info": {"professors", "faq", "website", "document"},
    "room_location": {"rooms", "faq", "website", "document"},
    "course_schedule": {"courses", "faq", "website", "document"},
    "event_info": {"events", "faq", "website", "document"},
    "admission_info": {"faq", "website", "document", "faculties"},
    "general_info": {"faq", "website", "document", "faculties"},
}


def hybrid_retrieve(
    question: str,
    chunks: list[dict],
    limit: int = 8,
    intent: str | None = None,
) -> list[dict]:
    """Retrieve chunks with keyword, phrase, intent, and optional TF-IDF scoring."""
    if not question.strip() or not chunks:
        return []

    detected_intent = intent or detect_intent(question)
    tfidf_scores = _tfidf_scores(question, chunks)
    scored: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        details = _deterministic_score_details(question, chunk, detected_intent)
        if tfidf_scores is not None:
            details["tfidf"] = round(float(tfidf_scores[index]) * 40.0, 4)
        else:
            details["tfidf"] = 0.0

        final_score = round(sum(details.values()), 4)
        if final_score <= 0:
            continue

        result = dict(chunk)
        result["score_details"] = details
        result["final_score"] = final_score
        result["score"] = final_score
        result["intent"] = detected_intent
        scored.append(result)

    scored.sort(
        key=lambda item: (
            -float(item["final_score"]),
            str(item.get("source", "")),
            str(item.get("title", "")),
        )
    )
    return scored[: max(1, int(limit))]


def _deterministic_score_details(
    question: str,
    chunk: dict,
    intent: str | None,
) -> dict[str, float]:
    normalized_question = normalize_query(question)
    question_keywords = set(extract_keywords(question))
    title = str(chunk.get("title", ""))
    content = str(chunk.get("content", ""))
    source = str(chunk.get("source", ""))
    keywords = " ".join(str(keyword) for keyword in chunk.get("keywords", []))
    normalized_title = normalize_query(title)
    normalized_content = normalize_query(content)
    normalized_chunk = normalize_query(f"{source} {title} {content} {keywords}")
    chunk_keywords = set(extract_keywords(normalized_chunk))
    title_keywords = set(extract_keywords(title))

    keyword_overlap = question_keywords & chunk_keywords
    title_overlap = question_keywords & title_keywords

    phrase_score = 0.0
    if normalized_question and normalized_question == normalized_title:
        phrase_score = 34.0
    elif normalized_question and normalized_question in normalized_title:
        phrase_score = 26.0
    elif normalized_question and normalized_question in normalized_content:
        phrase_score = 18.0

    source_intent = 0.0
    if intent and keyword_overlap and source in _INTENT_SOURCES.get(intent, set()):
        source_intent = 10.0

    return {
        "keyword_overlap": float(len(keyword_overlap) * 7),
        "title_match": float(len(title_overlap) * 10),
        "phrase_match": phrase_score,
        "source_intent": source_intent,
    }


def _tfidf_scores(question: str, chunks: list[dict]) -> list[float] | None:
    """Return optional TF-IDF cosine scores; unavailable sklearn is fine."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except Exception:
        return None

    documents = [_chunk_search_text(chunk) for chunk in chunks]
    if not any(document.strip() for document in documents):
        return None
    try:
        matrix = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            lowercase=True,
        ).fit_transform([question, *documents])
        similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    except Exception:
        return None
    return [float(value) for value in similarities]


def _chunk_search_text(chunk: dict) -> str:
    keywords = " ".join(str(keyword) for keyword in chunk.get("keywords", []))
    return " ".join(
        (
            str(chunk.get("source", "")),
            str(chunk.get("title", "")),
            str(chunk.get("content", "")),
            keywords,
        )
    )
