"""RAG chatbot orchestration for trusted ECU answers."""

from database.repositories.log_repository import log_chatbot_interaction
from database.repositories.search_repository import retrieve_from_database
from services.ecu_website_client import retrieve_from_website
from services.gemini_client import ask_gemini

STRONG_DATABASE_SCORE = 65
NO_CONTEXT_ANSWER_EN = (
    "I do not have enough ECU information about that yet. Please contact the "
    "relevant ECU office for accurate details."
)
NO_CONTEXT_ANSWER_AR = (
    "لا أملك معلومات كافية من مصادر ECU حول هذا السؤال حاليًا. من فضلك تواصل "
    "مع المكتب المختص في الجامعة للحصول على تفاصيل دقيقة."
)


def get_chatbot_response(question: str, db_path) -> dict:
    """Return a grounded chatbot response using DB, then website, then Gemini."""
    try:
        database_matches = retrieve_from_database(question, db_path)
    except Exception:
        database_matches = []

    strong_database_matches = [
        match
        for match in database_matches
        if int(match.get("score", 0) or 0) >= STRONG_DATABASE_SCORE
    ]

    if strong_database_matches:
        result = _answer_with_context(question, strong_database_matches, "database")
        return _with_logging(result, question, db_path)

    try:
        website_result = retrieve_from_website(question)
    except Exception:
        website_result = None

    if website_result:
        result = _answer_with_context(question, [website_result], "ecu_website")
        return _with_logging(result, question, db_path)

    result = _base_response(
        answer=_no_context_answer(question),
        had_context=False,
        source_used="none",
        matched_rooms=[],
        matched_professors=[],
        sources=[],
        gemini_status="not_called",
        error=None,
    )
    return _with_logging(result, question, db_path)


def is_arabic(text: str) -> bool:
    """Return whether text contains Arabic characters."""
    return any("\u0600" <= character <= "\u06ff" for character in text)


def _answer_with_context(question: str, context_blocks: list[dict], source_used: str) -> dict:
    try:
        gemini_result = ask_gemini(question, context_blocks)
    except Exception:
        gemini_result = {
            "ok": False,
            "answer": "",
            "error_type": "api_error",
        }

    matched_rooms = _database_matches_for_table(context_blocks, "rooms")
    matched_professors = _database_matches_for_table(context_blocks, "professors")
    sources = _clean_sources(context_blocks, source_used)

    if gemini_result.get("ok") is True:
        return _base_response(
            answer=gemini_result.get("answer", ""),
            had_context=True,
            source_used=source_used,
            matched_rooms=matched_rooms,
            matched_professors=matched_professors,
            sources=sources,
            gemini_status="ok",
            error=None,
        )

    error_type = gemini_result.get("error_type") or "api_error"
    fallback_answer = _fallback_answer(question, context_blocks, source_used)
    return _base_response(
        answer=fallback_answer,
        had_context=True,
        source_used=source_used,
        matched_rooms=matched_rooms,
        matched_professors=matched_professors,
        sources=sources,
        gemini_status=error_type,
        error=error_type,
    )


def _fallback_answer(question: str, context_blocks: list[dict], source_used: str) -> str:
    best_context = context_blocks[0]
    title = str(best_context.get("title", "") or "").strip()
    content = _short_text(str(best_context.get("content", "") or "").strip())

    if source_used == "database":
        intro = "بناءً على سجلات ECU:" if is_arabic(question) else "Based on ECU records:"
        return " ".join(part for part in [intro, title + "." if title else "", content] if part)

    intro = "بناءً على موقع ECU:" if is_arabic(question) else "Based on the ECU website:"
    return " ".join(part for part in [intro, content] if part)


def _short_text(text: str, max_length: int = 300) -> str:
    cleaned_text = " ".join(text.split())
    if len(cleaned_text) <= max_length:
        return cleaned_text

    truncated = cleaned_text[:max_length].rstrip()
    sentence_end = max(
        truncated.rfind("."),
        truncated.rfind("!"),
        truncated.rfind("?"),
        truncated.rfind("؟"),
    )
    if sentence_end >= int(max_length * 0.5):
        return truncated[: sentence_end + 1].strip()
    return truncated.strip()


def _database_matches_for_table(matches: list[dict], table_name: str) -> list[dict]:
    return [
        {
            "title": match.get("title", ""),
            "content": match.get("content", ""),
            "score": match.get("score", 0),
        }
        for match in matches
        if match.get("source_table") == table_name
    ]


def _clean_sources(context_blocks: list[dict], source_used: str) -> list[dict]:
    if source_used == "ecu_website":
        return [
            {
                "source": "ecu_website",
                "title": block.get("title", ""),
                "url": block.get("url", ""),
            }
            for block in context_blocks
        ]

    return [
        {
            "source": "database",
            "title": block.get("title", ""),
            "source_table": block.get("source_table", ""),
            "score": block.get("score", 0),
        }
        for block in context_blocks
    ]


def _no_context_answer(question: str) -> str:
    return NO_CONTEXT_ANSWER_AR if is_arabic(question) else NO_CONTEXT_ANSWER_EN


def _with_logging(result: dict, question: str, db_path) -> dict:
    try:
        logged = log_chatbot_interaction(
            db_path=db_path,
            question=question,
            source_used=result["source_used"],
            had_context=result["had_context"],
        )
    except Exception:
        logged = False

    return {
        **result,
        "logged": logged,
    }


def _base_response(
    answer: str,
    had_context: bool,
    source_used: str,
    matched_rooms: list[dict],
    matched_professors: list[dict],
    sources: list[dict],
    gemini_status: str,
    error: str | None,
) -> dict:
    return {
        "answer": answer,
        "had_context": had_context,
        "source_used": source_used,
        "matched_rooms": matched_rooms,
        "matched_professors": matched_professors,
        "sources": sources,
        "gemini_status": gemini_status,
        "error": error,
    }
