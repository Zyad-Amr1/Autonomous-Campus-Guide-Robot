"""Controller for the public database-backed chat assistant."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from controllers.university_context_controller import search_university_context
from database.connection import DB_NAME
from database.repositories.log_repository import create_log


LLMProvider = Callable[[str], str | dict[str, Any]]

ENGLISH_NO_CONTEXT = (
    "I do not have enough information about that yet. You can ask about faculties, "
    "rooms, professors, courses, events, or university FAQs."
)
ARABIC_NO_CONTEXT = (
    "لا أملك معلومات كافية عن هذا السؤال حاليا. يمكنك السؤال عن الكليات أو القاعات "
    "أو أعضاء هيئة التدريس أو الجداول أو الفعاليات."
)


def _is_arabic(text: str) -> bool:
    return any("\u0600" <= character <= "\u06ff" for character in text)


class PublicChatController:
    """Answer public chatbot questions from database context, with optional LLM use."""

    def __init__(
        self,
        db_path: str | Path = DB_NAME,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.db_path = db_path
        self.llm_provider = llm_provider

    def answer_question(self, question: str) -> dict[str, Any]:
        """Answer a visitor question and include confidence, route, and sources."""
        cleaned_question = question.strip()
        if not cleaned_question:
            return {
                "answer": ENGLISH_NO_CONTEXT,
                "confidence": "low",
                "sources": [],
                "route": "fallback",
            }

        context_items = search_university_context(cleaned_question, self.db_path)
        sources = [
            {
                "source_type": item["source_type"],
                "id": item.get("id"),
                "title": item["title"],
                "snippet": item["snippet"],
            }
            for item in context_items
        ]

        route = "database_context"
        if self.llm_provider is not None:
            prompt = self.build_prompt(cleaned_question, context_items)
            provider_response = self.llm_provider(prompt)
            answer = (
                str(provider_response.get("answer", "")).strip()
                if isinstance(provider_response, dict)
                else str(provider_response).strip()
            )
            route = "llm"
            if not answer:
                answer = self.generate_fallback_answer(cleaned_question, context_items)
                route = "fallback"
        else:
            answer = self.generate_fallback_answer(cleaned_question, context_items)
            if not context_items:
                route = "fallback"

        confidence = self._confidence_for(context_items, route)
        self._log_chat(cleaned_question, answer, context_items)
        return {
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "route": route,
        }

    def build_prompt(self, question: str, context_items: list[dict[str, Any]]) -> str:
        """Build an LLM-ready grounded prompt from retrieved database context."""
        context_lines = "\n".join(
            f"- [{item['source_type']}] {item['title']}: {item['snippet']}"
            for item in context_items
        ) or "No matching university context was found."
        return (
            "You are ECU Smart Assistant.\n"
            "Answer using only the provided university context.\n"
            "If the answer is not in the context, say you do not have enough information.\n"
            "Keep the answer concise and helpful.\n"
            "Support English or Arabic depending on the user's question language.\n\n"
            f"University context:\n{context_lines}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )

    def generate_fallback_answer(
        self,
        question: str,
        context_items: list[dict[str, Any]],
    ) -> str:
        """Generate a concise answer directly from retrieved database context."""
        if not context_items:
            return ARABIC_NO_CONTEXT if _is_arabic(question) else ENGLISH_NO_CONTEXT

        best = context_items[0]
        source_type = str(best["source_type"]).replace("_", " ")
        answer = str(best["snippet"]).strip()
        if _is_arabic(question):
            return f"وجدت هذه المعلومة في بيانات الجامعة ({source_type}): {answer}"
        return f"From ECU {source_type}: {answer}"

    def _confidence_for(self, context_items: list[dict[str, Any]], route: str) -> str:
        if route == "llm" and context_items:
            return "high"
        if not context_items:
            return "low"
        top_score = int(context_items[0].get("score", 0))
        return "high" if top_score >= 12 else "medium"

    def _log_chat(
        self,
        question: str,
        answer: str,
        context_items: list[dict[str, Any]],
    ) -> None:
        matched_faq_id = None
        if context_items and context_items[0].get("source_type") == "faq":
            matched_faq_id = context_items[0].get("id")
        try:
            create_log(
                question,
                matched_faq_id=int(matched_faq_id) if matched_faq_id is not None else None,
                response_text=answer,
                screen_name="public_chat",
                db_path=self.db_path,
            )
        except Exception:
            return
