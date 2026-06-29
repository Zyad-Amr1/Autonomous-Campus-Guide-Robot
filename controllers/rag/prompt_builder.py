"""Prompt construction for grounded public chatbot RAG answers."""

from __future__ import annotations

from typing import Any

from controllers.rag.query_analyzer import detect_language


ENGLISH_INSUFFICIENT = (
    "I do not have enough information about that yet. You can ask about faculties, "
    "rooms, professors, courses, events, or university FAQs."
)
ARABIC_INSUFFICIENT = (
    "\u0644\u0627 \u0623\u0645\u0644\u0643 \u0645\u0639\u0644\u0648\u0645\u0627\u062a "
    "\u0643\u0627\u0641\u064a\u0629 \u0639\u0646 \u0647\u0630\u0627 \u0627\u0644\u0633\u0624\u0627\u0644 "
    "\u062d\u0627\u0644\u064a\u0627. \u064a\u0645\u0643\u0646\u0643 \u0627\u0644\u0633\u0624\u0627\u0644 "
    "\u0639\u0646 \u0627\u0644\u0643\u0644\u064a\u0627\u062a \u0623\u0648 \u0627\u0644\u0642\u0627\u0639\u0627\u062a "
    "\u0623\u0648 \u0623\u0639\u0636\u0627\u0621 \u0647\u064a\u0626\u0629 \u0627\u0644\u062a\u062f\u0631\u064a\u0633 "
    "\u0623\u0648 \u0627\u0644\u062c\u062f\u0627\u0648\u0644 \u0623\u0648 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a."
)


def build_rag_prompt(
    question: str,
    chunks: list[dict[str, Any]],
    recent_messages: list[dict[str, str]] | None = None,
    language: str | None = None,
    intent: str | None = None,
) -> list[dict[str, str]]:
    """Build chat messages for a grounded ECU Smart Assistant answer."""
    user_language = language or detect_language(question)
    insufficient = ARABIC_INSUFFICIENT if user_language == "ar" else ENGLISH_INSUFFICIENT
    context = "\n\n".join(
        (
            f"Source: {chunk.get('source')}\n"
            f"Title: {chunk.get('title')}\n"
            f"Content: {chunk.get('content')}"
        )
        for chunk in chunks
    ) or "No context was retrieved."
    conversation_context = _format_recent_messages(recent_messages or [])
    language_instruction = (
        "Answer in Arabic."
        if user_language == "ar"
        else "Answer in the same language as the user."
        if user_language == "mixed"
        else "Answer in English."
    )
    system_message = (
        "You are ECU Smart Assistant.\n"
        f"Detected user language: {user_language}.\n"
        f"Detected intent: {intent or 'unknown'}.\n"
        "Use only the retrieved university context and recent conversation context.\n"
        "Do not invent facts, names, dates, schedules, rooms, requirements, or policies.\n"
        "Do not mention internal database or table names unless the user asks technically.\n"
        "If the retrieved context is weak, say that the available information is limited.\n"
        "If the question is ambiguous, ask one short clarification question.\n"
        f"If there is no useful context, say exactly: {insufficient}\n"
        f"{language_instruction}\n"
        "Be natural, helpful, concise, and professional."
    )
    user_message = (
        f"Recent conversation:\n{conversation_context}\n\n"
        f"University context:\n{context}\n\n"
        f"User question:\n{question}"
    )
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def _format_recent_messages(messages: list[dict[str, str]]) -> str:
    if not messages:
        return "No previous conversation."
    lines = []
    for message in messages[-6:]:
        role = str(message.get("role", "user")).strip() or "user"
        content = str(message.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "No previous conversation."
