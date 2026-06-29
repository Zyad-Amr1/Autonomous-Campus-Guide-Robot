"""Prompt construction for grounded public chatbot RAG answers."""

from __future__ import annotations

from typing import Any


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


def detect_language(text: str) -> str:
    """Detect whether the user is asking in Arabic or English."""
    return "ar" if any("\u0600" <= character <= "\u06ff" for character in text) else "en"


def build_rag_prompt(question: str, chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Build chat messages for a grounded ECU Smart Assistant answer."""
    language = detect_language(question)
    insufficient = ARABIC_INSUFFICIENT if language == "ar" else ENGLISH_INSUFFICIENT
    context = "\n\n".join(
        (
            f"Source: {chunk.get('source')}\n"
            f"Title: {chunk.get('title')}\n"
            f"Content: {chunk.get('content')}"
        )
        for chunk in chunks
    ) or "No context was retrieved."
    language_instruction = "Answer in Arabic." if language == "ar" else "Answer in English."
    system_message = (
        "You are ECU Smart Assistant.\n"
        "Answer only using the provided university context.\n"
        f"If context is insufficient, say exactly: {insufficient}\n"
        f"{language_instruction}\n"
        "Be helpful, concise, and professional.\n"
        "Do not invent names, schedules, rooms, or policies."
    )
    user_message = (
        f"University context:\n{context}\n\n"
        f"User question:\n{question}"
    )
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

