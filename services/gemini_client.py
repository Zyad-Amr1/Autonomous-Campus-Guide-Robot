"""Safe Gemini client wrapper for grounded chatbot answers."""

import os
import time
from typing import Any

from google import genai
from google.genai import types

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency smoke tests cover dotenv.
    load_dotenv = None


DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_MAX_REQUESTS_PER_MINUTE = 10
SYSTEM_INSTRUCTION = """
You are ECU Smart Assistant.
Answer ONLY from the provided context.
If the context is insufficient, say that the available ECU information is not enough.
Suggest contacting the relevant ECU office when appropriate.
Do not use general web knowledge.
Do not invent professor names, room locations, schedules, admissions details, or policies.
Keep answers short and kiosk-appropriate, about 2-4 sentences.
Answer in the same language as the user.
Do not use markdown tables.
Use clean bullet points only when helpful.
""".strip()

_rate_limiter = None
_rate_limiter_limit = None


class GeminiRateLimiter:
    """Small in-memory, non-blocking request limiter."""

    def __init__(self, max_requests_per_minute: int = DEFAULT_MAX_REQUESTS_PER_MINUTE):
        self.max_requests_per_minute = max_requests_per_minute
        self._request_timestamps: list[float] = []

    def can_send_now(self) -> bool:
        self._remove_expired_timestamps()
        return len(self._request_timestamps) < self.max_requests_per_minute

    def record_request(self) -> None:
        self._remove_expired_timestamps()
        self._request_timestamps.append(time.monotonic())

    def seconds_until_available(self) -> float:
        self._remove_expired_timestamps()
        if len(self._request_timestamps) < self.max_requests_per_minute:
            return 0.0
        oldest_timestamp = min(self._request_timestamps)
        return max(0.0, 60.0 - (time.monotonic() - oldest_timestamp))

    def reset(self) -> None:
        self._request_timestamps.clear()

    def _remove_expired_timestamps(self) -> None:
        cutoff = time.monotonic() - 60.0
        self._request_timestamps = [
            timestamp
            for timestamp in self._request_timestamps
            if timestamp > cutoff
        ]


def ask_gemini(question: str, context_blocks: list[dict]) -> dict:
    """Ask Gemini for a short answer grounded only in provided context."""
    _load_dotenv_if_available()
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return _result(False, "", "missing_api_key", model)

    limiter = _get_rate_limiter()
    if not limiter.can_send_now():
        return _result(
            False,
            "",
            "rate_limited_local",
            model,
            retry_after_seconds=limiter.seconds_until_available(),
        )

    limiter.record_request()

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=_build_prompt(question, context_blocks),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
                max_output_tokens=300,
            ),
        )
        answer = str(getattr(response, "text", "") or "").strip()
        if not answer:
            return _result(False, "", "empty_response", model)
        return _result(True, answer, None, model)
    except Exception as exc:
        error_type = "rate_limited" if _is_rate_limit_error(exc) else "api_error"
        return _result(False, "", error_type, model)


def _load_dotenv_if_available() -> None:
    if load_dotenv is not None:
        load_dotenv()


def _get_rate_limiter() -> GeminiRateLimiter:
    global _rate_limiter, _rate_limiter_limit

    limit = _get_max_requests_per_minute()
    if _rate_limiter is None or _rate_limiter_limit != limit:
        _rate_limiter = GeminiRateLimiter(limit)
        _rate_limiter_limit = limit
    return _rate_limiter


def _get_max_requests_per_minute() -> int:
    raw_limit = os.getenv("GEMINI_MAX_REQUESTS_PER_MINUTE", "")
    try:
        limit = int(raw_limit)
    except ValueError:
        return DEFAULT_MAX_REQUESTS_PER_MINUTE
    return limit if limit > 0 else DEFAULT_MAX_REQUESTS_PER_MINUTE


def _build_prompt(question: str, context_blocks: list[dict]) -> str:
    context_text = "\n\n".join(
        _format_context_block(index, block)
        for index, block in enumerate(context_blocks, start=1)
    )
    if not context_text:
        context_text = "[No context provided]"

    return (
        "Use only the context blocks below to answer the question.\n\n"
        f"{context_text}\n\n"
        f"Question: {question.strip()}"
    )


def _format_context_block(index: int, block: dict[str, Any]) -> str:
    source = str(block.get("source", "unknown")).strip() or "unknown"
    title = str(block.get("title", "Untitled")).strip() or "Untitled"
    url = str(block.get("url", "") or "").strip()
    content = str(block.get("content", "") or "").strip()

    lines = [
        f"[Context {index}]",
        f"Source: {source}",
        f"Title: {title}",
    ]
    if url:
        lines.append(f"URL: {url}")
    lines.append(f"Content: {content}")
    return "\n".join(lines)


def _is_rate_limit_error(exc: Exception) -> bool:
    message = str(exc).casefold()
    rate_limit_terms = ("429", "rate", "quota", "resource_exhausted")
    return any(term in message for term in rate_limit_terms)


def _result(
    ok: bool,
    answer: str,
    error_type: str | None,
    model: str,
    retry_after_seconds: float | None = None,
) -> dict:
    result = {
        "ok": ok,
        "answer": answer,
        "error_type": error_type,
        "model": model,
    }
    if retry_after_seconds is not None:
        result["retry_after_seconds"] = retry_after_seconds
    return result
