"""Compatibility retriever API backed by hybrid retrieval and reranking."""

from __future__ import annotations

from typing import Any

from controllers.rag.hybrid_retriever import hybrid_retrieve
from controllers.rag.query_analyzer import detect_intent
from controllers.rag.reranker import rerank_chunks


def retrieve_relevant_chunks(
    question: str,
    chunks: list[dict[str, Any]],
    limit: int = 8,
    intent: str | None = None,
) -> list[dict[str, Any]]:
    """Return relevant chunks using the upgraded hybrid retrieval pipeline."""
    detected_intent = intent or detect_intent(question)
    candidates = hybrid_retrieve(
        question,
        chunks,
        limit=max(limit * 3, 12),
        intent=detected_intent,
    )
    return rerank_chunks(
        question,
        candidates,
        intent=detected_intent,
        limit=limit,
    )
