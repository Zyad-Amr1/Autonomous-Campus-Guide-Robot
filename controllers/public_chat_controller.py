"""Controller for the public database-backed chat assistant."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Callable

import requests

from controllers.rag.conversation_memory import ConversationMemory
from controllers.rag.knowledge_chunker import build_knowledge_chunks
from controllers.rag.knowledge_store import (
    init_knowledge_store,
    load_knowledge_chunks,
)
from controllers.rag.prompt_builder import (
    ARABIC_INSUFFICIENT,
    ENGLISH_INSUFFICIENT,
    build_rag_prompt,
    detect_language,
)
from controllers.rag.query_analyzer import detect_intent, extract_keywords
from controllers.rag.retriever import retrieve_relevant_chunks
from database.connection import DB_NAME
from database.repositories.log_repository import create_log


LLMProvider = Callable[[list[dict[str, str]]], str | dict[str, Any]]

ENGLISH_NO_CONTEXT = ENGLISH_INSUFFICIENT
ARABIC_NO_CONTEXT = ARABIC_INSUFFICIENT
GROQ_DEFAULT_MODEL = "openai/gpt-oss-120b"


def _is_arabic(text: str) -> bool:
    return any("\u0600" <= character <= "\u06ff" for character in text)


def _project_root() -> Path:
    """Return the repository root that contains the app's top-level folders."""
    current_file = Path(__file__).resolve()
    for folder in (current_file.parent, *current_file.parents):
        if all((folder / name).exists() for name in ("apps", "controllers", "database", "ui")):
            return folder
    return current_file.parents[1]


def load_groq_config() -> dict[str, str]:
    """Load Groq API configuration from env first, then local secrets JSON."""
    env_api_key = os.getenv("GROQ_API_KEY", "").strip()
    env_model = os.getenv("GROQ_MODEL", "").strip()
    if env_api_key:
        return {
            "api_key": env_api_key,
            "model": env_model or GROQ_DEFAULT_MODEL,
        }

    config: dict[str, str] = {
        "api_key": "",
        "model": env_model or GROQ_DEFAULT_MODEL,
    }
    secrets_path = _project_root() / "secrets" / "api_keys.json"
    try:
        raw_config = json.loads(secrets_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return config

    if not isinstance(raw_config, dict):
        return config

    file_api_key = str(raw_config.get("GROQ_API_KEY") or "").strip()
    file_model = str(raw_config.get("GROQ_MODEL") or "").strip()
    if file_api_key:
        config["api_key"] = file_api_key
    if file_model:
        config["model"] = file_model
    return config


class GroqChatProvider:
    """OpenAI-compatible Groq chat completions provider."""

    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = GROQ_DEFAULT_MODEL

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
        """Create a Groq provider from env or local secrets when a key exists."""
        config = load_groq_config()
        if not config["api_key"]:
            return None
        return cls(api_key=config["api_key"], model=config["model"])

    def __call__(self, messages: list[dict[str, str]]) -> str:
        """Call Groq's OpenAI-compatible chat completions endpoint."""
        response = requests.post(
            self.API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
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
        conversation_memory: ConversationMemory | None = None,
    ) -> None:
        self.db_path = db_path
        self.llm_provider = llm_provider if llm_provider is not None else GroqChatProvider.from_environment()
        self.conversation_memory = conversation_memory or ConversationMemory()

    def answer_question(self, question: str) -> dict[str, Any]:
        """Answer a visitor question and include confidence, route, and sources."""
        cleaned_question = question.strip()
        language = detect_language(cleaned_question)
        intent = detect_intent(cleaned_question)
        if not cleaned_question:
            return {
                "answer": ENGLISH_NO_CONTEXT,
                "confidence": "low",
                "sources": [],
                "route": "no_context",
                "intent": "unknown",
                "language": "en",
            }

        recent_messages = self.conversation_memory.get_recent_messages()
        retrieval_query = self._expanded_retrieval_query(cleaned_question, recent_messages)
        retrieval_intent = intent if intent != "unknown" else detect_intent(retrieval_query)
        retrieved_chunks = self._retrieve_chunks(retrieval_query, retrieval_intent)
        sources = self._sources_from_chunks(retrieved_chunks)

        if not retrieved_chunks:
            answer = (
                self._clarification_answer(cleaned_question)
                if self._is_ambiguous_follow_up(cleaned_question, recent_messages)
                else self._insufficient_answer(cleaned_question)
            )
            self._log_chat(cleaned_question, answer, retrieved_chunks)
            self._remember_turn(cleaned_question, answer)
            return {
                "answer": answer,
                "confidence": "low",
                "sources": [],
                "route": "no_context",
                "intent": retrieval_intent,
                "language": language,
            }

        route = "rag_fallback"
        if self.llm_provider is not None:
            messages = build_rag_prompt(
                cleaned_question,
                retrieved_chunks,
                recent_messages=recent_messages,
                language=language,
                intent=retrieval_intent,
            )
            try:
                provider_response = self.llm_provider(messages)
                answer = (
                    str(provider_response.get("answer", "")).strip()
                    if isinstance(provider_response, dict)
                    else str(provider_response).strip()
                )
                if answer:
                    route = "rag_groq"
                else:
                    answer = self.generate_fallback_answer(cleaned_question, retrieved_chunks)
                    route = "rag_fallback"
            except Exception:
                answer = self.generate_fallback_answer(cleaned_question, retrieved_chunks)
                route = "rag_fallback"
        else:
            answer = self.generate_fallback_answer(cleaned_question, retrieved_chunks)

        confidence = self._confidence_for(retrieved_chunks, route)
        if confidence == "low":
            answer = self._with_limited_context_note(answer, cleaned_question)
        self._log_chat(cleaned_question, answer, retrieved_chunks)
        self._remember_turn(cleaned_question, answer)
        return {
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "route": route,
            "intent": retrieval_intent,
            "language": language,
        }

    def build_prompt(
        self,
        question: str,
        context_items: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Build an LLM-ready grounded prompt from retrieved database context."""
        return build_rag_prompt(
            question,
            context_items,
            recent_messages=self.conversation_memory.get_recent_messages(),
            language=detect_language(question),
            intent=detect_intent(question),
        )

    def clear_memory(self) -> None:
        """Safely clear in-memory conversation context for the public chat."""
        try:
            self.conversation_memory.clear()
        except Exception:
            return

    def generate_fallback_answer(
        self,
        question: str,
        context_items: list[dict[str, Any]],
    ) -> str:
        """Generate a concise answer directly from retrieved database context."""
        if not context_items:
            return self._insufficient_answer(question)

        top_chunks = context_items[:3]
        if detect_language(question) == "ar":
            details = " ".join(
                f"{chunk['title']}: {chunk['content']}" for chunk in top_chunks
            )
            return (
                "\u0628\u0646\u0627\u0621 \u0639\u0644\u0649 \u0628\u064a\u0627\u0646\u0627\u062a "
                f"\u0627\u0644\u062c\u0627\u0645\u0639\u0629: {details}"
            )

        details = " ".join(
            f"{chunk['title']}: {chunk['content']}" for chunk in top_chunks
        )
        return f"Based on ECU university data: {details}"

    def _confidence_for(self, context_items: list[dict[str, Any]], route: str) -> str:
        if not context_items:
            return "low"
        scores = [float(item.get("final_score", item.get("score", 0)) or 0) for item in context_items]
        top_score = max(scores) if scores else 0
        relevant_count = sum(1 for score in scores if score >= 22)
        if top_score >= 55 and relevant_count >= 2:
            return "high"
        if top_score >= 24 or relevant_count >= 1:
            return "medium"
        return "low"

    def _log_chat(
        self,
        question: str,
        answer: str,
        context_items: list[dict[str, Any]],
    ) -> None:
        matched_faq_id = None
        if context_items and context_items[0].get("source_type") == "faq":
            matched_faq_id = context_items[0].get("id")
        elif context_items and context_items[0].get("source") == "faq":
            raw_id = str(context_items[0].get("id", "")).split(":", maxsplit=1)[-1]
            matched_faq_id = int(raw_id) if raw_id.isdigit() else None
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

    def _insufficient_answer(self, question: str) -> str:
        """Return the no-context answer in the user's language."""
        return ARABIC_NO_CONTEXT if detect_language(question) == "ar" else ENGLISH_NO_CONTEXT

    def _clarification_answer(self, question: str) -> str:
        """Ask a short clarification when the follow-up lacks a clear subject."""
        if detect_language(question) == "ar":
            return "\u0645\u0645\u0643\u0646 \u062a\u0648\u0636\u062d \u0645\u0627 \u0627\u0644\u0645\u0648\u0636\u0648\u0639 \u0627\u0644\u0630\u064a \u062a\u0642\u0635\u062f\u0647\u061f"
        return "Could you clarify which ECU topic you mean?"

    def _with_limited_context_note(self, answer: str, question: str) -> str:
        """Mark weak retrieved context without adding new facts."""
        if detect_language(question) == "ar":
            note = "\u0627\u0644\u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0627\u0644\u0645\u062a\u0627\u062d\u0629 \u0645\u062d\u062f\u0648\u062f\u0629. "
        else:
            note = "Available information is limited. "
        return answer if answer.startswith(note.strip()) else f"{note}{answer}"

    def _sources_from_chunks(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return public source metadata for retrieved chunks."""
        return [
            {
                "source": str(chunk.get("source", "")),
                "title": str(chunk.get("title", "")),
                "score": round(float(chunk.get("final_score", chunk.get("score", 0)) or 0), 4),
            }
            for chunk in chunks
        ]

    def _expanded_retrieval_query(
        self,
        question: str,
        recent_messages: list[dict[str, str]],
    ) -> str:
        """Expand short follow-ups with recent user context."""
        if not self._is_ambiguous_follow_up(question, recent_messages):
            return question
        previous_user_messages = [
            message["content"]
            for message in recent_messages
            if message.get("role") == "user" and message.get("content")
        ]
        if not previous_user_messages:
            return question
        return f"{previous_user_messages[-1]} {question}"

    def _is_ambiguous_follow_up(
        self,
        question: str,
        recent_messages: list[dict[str, str]],
    ) -> bool:
        """Detect short context-dependent questions."""
        keywords = extract_keywords(question)
        lowered = question.casefold()
        follow_up_markers = (
            " it",
            " its",
            "they",
            "them",
            "there",
            "more",
            "department",
            "departments",
            "\u0627\u0642\u0633\u0627\u0645",
            "\u0623\u0642\u0633\u0627\u0645",
            "\u0647\u0627",
            "\u0647\u0648",
            "\u0647\u064a",
            "\u0645\u064a\u0646",
        )
        return (
            bool(recent_messages)
            and len(keywords) <= 4
            and any(marker in f" {lowered} " for marker in follow_up_markers)
        )

    def _remember_turn(self, question: str, answer: str) -> None:
        self.conversation_memory.add_user_message(question)
        self.conversation_memory.add_assistant_message(answer)

    def _retrieve_chunks(self, question: str, intent: str | None = None) -> list[dict[str, Any]]:
        """Retrieve from persistent store first, then direct DB chunks if empty."""
        init_knowledge_store(self.db_path)
        stored_chunks = load_knowledge_chunks(self.db_path)
        if stored_chunks:
            return retrieve_relevant_chunks(question, stored_chunks, intent=intent)
        return retrieve_relevant_chunks(
            question,
            build_knowledge_chunks(self.db_path),
            intent=intent,
        )
