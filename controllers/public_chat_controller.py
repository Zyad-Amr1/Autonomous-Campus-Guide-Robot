"""Controller for the public database-backed chat assistant."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

import requests

from controllers.university_context_controller import search_university_context
from database.connection import DB_NAME
from database.repositories.log_repository import create_log


LLMProvider = Callable[[str], str | dict[str, Any]]

ENGLISH_NO_CONTEXT = "I do not have enough information about that yet."
ARABIC_NO_CONTEXT = (
    "\u0644\u0627 \u0623\u0645\u0644\u0643 \u0645\u0639\u0644\u0648\u0645\u0627\u062a "
    "\u0643\u0627\u0641\u064a\u0629 \u0639\u0646 \u0647\u0630\u0627 \u062d\u0627\u0644\u064a\u0627."
)


def _is_arabic(text: str) -> bool:
    return any("\u0600" <= character <= "\u06ff" for character in text)


class GroqChatProvider:
    """OpenAI-compatible Groq chat completions provider."""

    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = "openai/gpt-oss-120b"

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        timeout: int = 20,
    ) -> None:
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout

    @classmethod
    def from_environment(cls) -> "GroqChatProvider | None":
        """Create a Groq provider only when GROQ_API_KEY is available."""
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            return None
        model = os.getenv("GROQ_MODEL", cls.DEFAULT_MODEL).strip() or cls.DEFAULT_MODEL
        return cls(api_key=api_key, model=model)

    def __call__(self, prompt: str) -> str:
        """Call Groq's OpenAI-compatible chat completions endpoint."""
        response = requests.post(
            self.API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are ECU Smart Assistant. Answer only from the supplied "
                            "university context. If the context is insufficient, say: "
                            f"{ENGLISH_NO_CONTEXT}"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 450,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return str(payload["choices"][0]["message"]["content"]).strip()


class PublicChatController:
    """Answer public chatbot questions from database context, with optional LLM use."""

    def __init__(
        self,
        db_path: str | Path = DB_NAME,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.db_path = db_path
        self.llm_provider = llm_provider if llm_provider is not None else GroqChatProvider.from_environment()

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
        if self.llm_provider is not None and context_items:
            prompt = self.build_prompt(cleaned_question, context_items)
            try:
                provider_response = self.llm_provider(prompt)
                answer = (
                    str(provider_response.get("answer", "")).strip()
                    if isinstance(provider_response, dict)
                    else str(provider_response).strip()
                )
                route = "llm" if answer else "fallback"
            except Exception:
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
            f"If the answer is not in the context, say exactly: {ENGLISH_NO_CONTEXT}\n"
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
            return (
                "\u0648\u062c\u062f\u062a \u0647\u0630\u0647 \u0627\u0644\u0645\u0639\u0644\u0648\u0645\u0629 "
                f"\u0641\u064a \u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u062c\u0627\u0645\u0639\u0629 ({source_type}): {answer}"
            )
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
