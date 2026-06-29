"""Reranking helpers for ECU chatbot retrieved chunks."""

from __future__ import annotations

from controllers.rag.query_analyzer import extract_keywords, normalize_query


_INTENT_SOURCES = {
    "faculty_info": {"faculties", "faq", "website", "document"},
    "professor_info": {"professors", "faq", "website", "document"},
    "room_location": {"rooms", "faq", "website", "document"},
    "course_schedule": {"courses", "faq", "website", "document"},
    "event_info": {"events", "faq", "website", "document"},
    "admission_info": {"faq", "website", "document", "faculties"},
    "general_info": {"faq", "website", "document", "faculties"},
}


def rerank_chunks(
    question: str,
    chunks: list[dict],
    intent: str | None = None,
    limit: int = 8,
) -> list[dict]:
    """Rerank retrieved chunks with entity, intent, focus, and noise signals."""
    if not chunks:
        return []

    question_keywords = set(extract_keywords(question))
    normalized_question = normalize_query(question)
    reranked: list[dict] = []
    for chunk in chunks:
        title = str(chunk.get("title", ""))
        content = str(chunk.get("content", ""))
        source = str(chunk.get("source", ""))
        title_keywords = set(extract_keywords(title))
        chunk_keywords = set(
            extract_keywords(
                " ".join(
                    (
                        source,
                        title,
                        content,
                        " ".join(str(keyword) for keyword in chunk.get("keywords", [])),
                    )
                )
            )
        )
        overlap = question_keywords & chunk_keywords
        title_overlap = question_keywords & title_keywords

        score = float(chunk.get("final_score", chunk.get("score", 0)) or 0)
        if normalized_question and normalized_question == normalize_query(title):
            score += 24
        elif title_overlap:
            score += len(title_overlap) * 8
        if intent and source in _INTENT_SOURCES.get(intent, set()) and overlap:
            score += 8
        score += _focus_bonus(content)
        if not overlap and not title_overlap:
            score -= 18

        if score <= 0:
            continue
        result = dict(chunk)
        result["final_score"] = round(score, 4)
        result["score"] = result["final_score"]
        details = dict(result.get("score_details") or {})
        details["rerank"] = round(score - float(chunk.get("final_score", chunk.get("score", 0)) or 0), 4)
        result["score_details"] = details
        reranked.append(result)

    reranked.sort(
        key=lambda item: (
            -float(item["final_score"]),
            str(item.get("source", "")),
            str(item.get("title", "")),
        )
    )
    return reranked[: max(1, int(limit))]


def _focus_bonus(content: str) -> float:
    length = len(content)
    if length <= 0:
        return 0.0
    if length <= 900:
        return 6.0
    if length <= 2500:
        return 2.0
    return -6.0
