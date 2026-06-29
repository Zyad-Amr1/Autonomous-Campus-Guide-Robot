"""Tests for the public custom RAG chatbot controller."""

from __future__ import annotations

import sqlite3

from controllers.public_chat_controller import (
    ARABIC_NO_CONTEXT,
    ENGLISH_NO_CONTEXT,
    GroqChatProvider,
    PublicChatController,
    load_groq_config,
)
from controllers.rag.conversation_memory import ConversationMemory
from controllers.rag.knowledge_chunker import build_knowledge_chunks
from controllers.rag.knowledge_store import init_knowledge_store, mark_knowledge_dirty, upsert_knowledge_chunks
from controllers.rag.prompt_builder import build_rag_prompt, detect_language
from controllers.rag.retriever import retrieve_relevant_chunks
from database.init_db import initialize_database


def _db(tmp_path):
    db_path = tmp_path / "chat.db"
    initialize_database(db_path)
    connection = sqlite3.connect(db_path)
    try:
        faculty_id = connection.execute(
            """
            INSERT INTO faculties (name, description, building, dean_name)
            VALUES (?, ?, ?, ?)
            """,
            ("Engineering", "Engineering and robotics programs.", "Building A", "Dr. Adel"),
        ).lastrowid
        room_id = connection.execute(
            """
            INSERT INTO rooms (room_name, room_number, building, floor, category, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("Cafeteria", "C-01", "Student Center", 1, "Service", "Food court and student break area."),
        ).lastrowid
        professor_id = connection.execute(
            """
            INSERT INTO professors (full_name, title, faculty_id, office_room_id, email, office_hours, bio)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Dr. Mona Hassan",
                "Professor",
                faculty_id,
                room_id,
                "mona.hassan@ecu.edu.eg",
                "Sunday 10:00-12:00",
                "Robotics researcher.",
            ),
        ).lastrowid
        connection.execute(
            """
            INSERT INTO courses (
                course_code, course_name, faculty_id, professor_id, room_id,
                schedule_day, start_time, end_time, semester
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("ROB101", "Introduction to Robotics", faculty_id, professor_id, room_id, "Monday", "09:00", "11:00", "Fall"),
        )
        connection.execute(
            """
            INSERT INTO events (title, description, location, start_date, end_date, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("Open Day", "Meet ECU faculties and student clubs.", "Main Hall", "2026-07-01", "2026-07-01", "10:00", "14:00"),
        )
        connection.execute(
            """
            INSERT INTO faq (question, answer, keywords, category)
            VALUES (?, ?, ?, ?)
            """,
            ("Where is student affairs?", "Student affairs is in Building B.", "student affairs services", "services"),
        )
        connection.commit()
    finally:
        connection.close()
    return db_path


def _disable_real_groq(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    monkeypatch.setattr("controllers.public_chat_controller._project_root", lambda: tmp_path)


def test_chunks_are_created_from_fake_sqlite_data(tmp_path) -> None:
    chunks = build_knowledge_chunks(_db(tmp_path))

    sources = {chunk["source"] for chunk in chunks}
    assert {"faculties", "professors", "rooms", "courses", "events", "faq"} <= sources
    assert all({"id", "source", "title", "content", "keywords", "language"} <= set(chunk) for chunk in chunks)
    assert any(chunk["title"] == "Engineering" for chunk in chunks)


def test_retrieval_returns_relevant_faculty_chunk(tmp_path) -> None:
    chunks = build_knowledge_chunks(_db(tmp_path))

    results = retrieve_relevant_chunks("Tell me about faculties", chunks)

    assert results
    assert results[0]["source"] == "faculties"
    assert "Engineering" in results[0]["title"]


def test_retrieval_returns_relevant_professor_chunk(tmp_path) -> None:
    chunks = build_knowledge_chunks(_db(tmp_path))

    results = retrieve_relevant_chunks("Who are the professors?", chunks)

    assert results
    assert results[0]["source"] == "professors"
    assert "Dr. Mona Hassan" in results[0]["title"]


def test_retrieval_returns_relevant_room_chunk(tmp_path) -> None:
    chunks = build_knowledge_chunks(_db(tmp_path))

    results = retrieve_relevant_chunks("Where is cafeteria?", chunks)

    assert results
    assert results[0]["source"] == "rooms"
    assert "Cafeteria" in results[0]["title"]


def test_retrieval_returns_no_chunks_for_unrelated_question(tmp_path) -> None:
    chunks = build_knowledge_chunks(_db(tmp_path))

    results = retrieve_relevant_chunks("Tell me about parking permits on Mars", chunks)

    assert results == []


def test_exact_title_match_ranks_higher() -> None:
    chunks = [
        {
            "id": "faculties:1",
            "source": "faculties",
            "title": "Faculty of Engineering",
            "content": "Engineering programs.",
            "keywords": ["engineering"],
            "language": "en",
        },
        {
            "id": "faq:1",
            "source": "faq",
            "title": "Engineering clubs",
            "content": "Student club information.",
            "keywords": ["engineering"],
            "language": "en",
        },
    ]

    results = retrieve_relevant_chunks("Faculty of Engineering", chunks, intent="faculty_info")

    assert results[0]["id"] == "faculties:1"
    assert results[0]["score"] > results[1]["score"]


def test_intent_matching_source_ranks_higher() -> None:
    chunks = [
        {
            "id": "rooms:1",
            "source": "rooms",
            "title": "Engineering Hall",
            "content": "A hall in Building A.",
            "keywords": ["engineering"],
            "language": "en",
        },
        {
            "id": "faculties:1",
            "source": "faculties",
            "title": "Engineering",
            "content": "Engineering and robotics programs.",
            "keywords": ["engineering"],
            "language": "en",
        },
    ]

    results = retrieve_relevant_chunks("Tell me about Engineering", chunks, intent="faculty_info")

    assert results[0]["source"] == "faculties"


def test_arabic_query_retrieves_arabic_chunk() -> None:
    chunks = [
        {
            "id": "faculties:ar",
            "source": "faculties",
            "title": "كلية الهندسة",
            "content": "تضم برامج الهندسة والروبوتات.",
            "keywords": ["كلية", "الهندسة"],
            "language": "ar",
        }
    ]

    results = retrieve_relevant_chunks("ما هي كلية الهندسة؟", chunks, intent="faculty_info")

    assert results
    assert results[0]["id"] == "faculties:ar"


def test_prompt_includes_retrieved_context_and_user_question(tmp_path) -> None:
    chunks = retrieve_relevant_chunks("Where is cafeteria?", build_knowledge_chunks(_db(tmp_path)))

    messages = build_rag_prompt("Where is cafeteria?", chunks)

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "ECU Smart Assistant" in messages[0]["content"]
    assert "Cafeteria" in messages[1]["content"]
    assert "Where is cafeteria?" in messages[1]["content"]


def test_arabic_question_produces_arabic_instruction(tmp_path) -> None:
    chunks = retrieve_relevant_chunks("ما هي كليات الجامعة؟", build_knowledge_chunks(_db(tmp_path)))

    messages = build_rag_prompt("ما هي كليات الجامعة؟", chunks)

    assert detect_language("ما هي كليات الجامعة؟") == "ar"
    assert "Answer in Arabic." in messages[0]["content"]
    assert "Use only the retrieved university context" in messages[0]["content"]


def test_answer_question_returns_no_context_when_nothing_found(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("Tell me about parking permits on Mars")

    assert result["route"] == "no_context"
    assert result["confidence"] == "low"
    assert result["sources"] == []
    assert result["answer"] == ENGLISH_NO_CONTEXT
    assert result["intent"] == "unknown"
    assert result["language"] == "en"
    assert result["debug"]["retrieved_count"] == 0
    assert result["debug"]["used_groq"] is False
    assert result["debug"]["chunk_count_before"] == 0
    assert result["debug"]["chunk_count_after"] >= 1
    assert result["debug"]["source_counts"]


def test_no_context_does_not_call_fake_llm(tmp_path) -> None:
    calls = []

    def fake_provider(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        return "Should not be used."

    controller = PublicChatController(db_path=_db(tmp_path), llm_provider=fake_provider)

    result = controller.answer_question("Tell me about parking permits on Mars")

    assert result["route"] == "no_context"
    assert calls == []
    assert result["debug"]["used_groq"] is False


def test_empty_knowledge_store_auto_syncs_database(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    calls = []

    def fake_sync(db_path):
        calls.append(db_path)
        return {"chunks_created": 0, "sources": {}}

    monkeypatch.setattr("controllers.public_chat_controller.sync_database_to_knowledge_base", fake_sync)
    db_path = _db(tmp_path)
    init_knowledge_store(db_path)
    controller = PublicChatController(db_path=db_path)

    result = controller.answer_question("Tell me about parking permits on Mars")

    assert calls == [db_path]
    assert result["debug"]["auto_synced_database"] is True
    assert result["debug"]["chunk_count_before"] == 0


def test_professor_question_retrieves_professor_chunk(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("who are the professors?")

    assert result["route"] != "no_context"
    assert result["sources"][0]["source"] == "professors"
    assert "Dr. Mona Hassan" in result["answer"]


def test_staff_members_question_retrieves_professor_chunk(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("staff members")

    assert result["route"] != "no_context"
    assert result["sources"][0]["source"] == "professors"


def test_faculty_question_retrieves_faculty_chunk(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("what faculties are available")

    assert result["route"] != "no_context"
    assert result["sources"][0]["source"] == "faculties"
    assert "Engineering" in result["answer"]


def test_cafeteria_question_retrieves_room_chunk(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("where is the cafeteria?")

    assert result["route"] != "no_context"
    assert result["sources"][0]["source"] == "rooms"
    assert "Cafeteria" in result["answer"]


def test_no_context_answer_is_clear_not_question_mark(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("Tell me about parking permits on Mars")

    assert result["route"] == "no_context"
    assert result["answer"] == ENGLISH_NO_CONTEXT
    assert result["answer"] != "?"


def test_answer_question_includes_knowledge_dirty_debug_flag(tmp_path) -> None:
    db_path = _db(tmp_path)
    mark_knowledge_dirty(db_path, "FAQ data changed")
    controller = PublicChatController(db_path=db_path, llm_provider=None)

    result = controller.answer_question("Where is cafeteria?")

    assert result["route"] == "rag_fallback"
    assert result["debug"]["knowledge_dirty"] is True
    assert "Cafeteria" in result["answer"]


def test_no_context_still_works_when_knowledge_is_dirty(tmp_path) -> None:
    db_path = _db(tmp_path)
    mark_knowledge_dirty(db_path, "Courses data changed")
    controller = PublicChatController(db_path=db_path, llm_provider=None)

    result = controller.answer_question("Tell me about parking permits on Mars")

    assert result["route"] == "no_context"
    assert result["sources"] == []
    assert result["answer"] == ENGLISH_NO_CONTEXT
    assert result["debug"]["knowledge_dirty"] is True


def test_answer_question_returns_arabic_no_context(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("أين موقف السيارات على المريخ؟")

    assert result["route"] == "no_context"
    assert result["answer"] == ARABIC_NO_CONTEXT
    assert result["language"] == "ar"


def test_answer_question_retrieves_from_knowledge_chunks(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    db_path = _db(tmp_path)
    upsert_knowledge_chunks(
        db_path,
        [
            {
                "id": "rooms:custom",
                "source": "rooms",
                "title": "Cafeteria",
                "content": "The cafeteria is beside the Student Center entrance.",
                "keywords": ["cafeteria", "student", "food"],
                "language": "en",
                "metadata": {"origin": "test"},
            }
        ],
    )
    controller = PublicChatController(db_path=db_path)

    result = controller.answer_question("Where is cafeteria?")

    assert result["route"] == "rag_fallback"
    assert result["sources"][0]["source"] == "rooms"
    assert result["sources"][0]["title"] == "Cafeteria"
    assert set(result["sources"][0]) == {"source", "title", "score"}
    assert result["sources"][0]["score"] > 0
    assert "Student Center entrance" in result["answer"]
    assert result["intent"] == "room_location"
    assert result["language"] == "en"
    assert result["debug"]["retrieved_count"] >= 1
    assert result["debug"]["top_score"] > 0
    assert result["debug"]["context_chars"] > 0


def test_answer_question_uses_retriever_pipeline(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    calls = []

    def fake_retrieve(question, chunks, limit=8, intent=None):
        calls.append({"question": question, "limit": limit, "intent": intent, "chunk_count": len(chunks)})
        return [
            {
                "id": "faculties:test",
                "source": "faculties",
                "title": "Faculty of Engineering",
                "content": "Engineering faculty context.",
                "keywords": ["engineering"],
                "final_score": 80,
                "score": 80,
            }
        ]

    monkeypatch.setattr(
        "controllers.public_chat_controller.retrieve_relevant_chunks",
        fake_retrieve,
    )
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("Tell me about Faculty of Engineering")

    assert calls
    assert calls[0]["intent"] == "faculty_info"
    assert result["route"] == "rag_fallback"
    assert result["confidence"] == "medium"


def test_confidence_high_for_strong_multiple_matches(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)

    def fake_retrieve(_question, _chunks, limit=8, intent=None):
        return [
            {
                "id": "faculties:test",
                "source": "faculties",
                "title": "Faculty of Engineering",
                "content": "Engineering faculty context.",
                "keywords": ["engineering"],
                "final_score": 80,
                "score": 80,
            },
            {
                "id": "faq:test",
                "source": "faq",
                "title": "Engineering departments",
                "content": "Engineering department context.",
                "keywords": ["engineering", "departments"],
                "final_score": 62,
                "score": 62,
            },
        ]

    monkeypatch.setattr(
        "controllers.public_chat_controller.retrieve_relevant_chunks",
        fake_retrieve,
    )
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("Tell me about Faculty of Engineering")

    assert result["confidence"] == "high"


def test_empty_knowledge_chunks_falls_back_to_database_rows(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    db_path = _db(tmp_path)
    init_knowledge_store(db_path)
    controller = PublicChatController(db_path=db_path)

    result = controller.answer_question("Where is cafeteria?")

    assert result["route"] == "rag_fallback"
    assert result["sources"][0]["source"] == "rooms"
    assert "score" in result["sources"][0]
    assert "Cafeteria" in result["answer"]


def test_answer_question_uses_fake_llm_provider_when_provided(tmp_path) -> None:
    calls: list[list[dict[str, str]]] = []

    def fake_provider(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        return "LLM answer from fake provider."

    controller = PublicChatController(db_path=_db(tmp_path), llm_provider=fake_provider)

    result = controller.answer_question("Where is cafeteria?")

    assert calls
    assert calls[0][0]["role"] == "system"
    assert "Cafeteria" in calls[0][1]["content"]
    assert result["route"] == "rag_groq"
    assert result["answer"] == "LLM answer from fake provider."
    assert result["intent"] == "room_location"
    assert result["language"] == "en"
    assert result["debug"]["used_groq"] is True


def test_empty_provider_answer_falls_back_safely(tmp_path) -> None:
    def empty_provider(_messages: list[dict[str, str]]) -> str:
        return ""

    controller = PublicChatController(db_path=_db(tmp_path), llm_provider=empty_provider)

    result = controller.answer_question("Where is cafeteria?")

    assert result["route"] == "rag_fallback"
    assert "Cafeteria" in result["answer"]
    assert result["debug"]["used_groq"] is False


def test_provider_answer_that_ignores_context_falls_back(tmp_path) -> None:
    def unrelated_provider(_messages: list[dict[str, str]]) -> str:
        return "Paris airports and ancient mountain weather forecasts are unrelated."

    controller = PublicChatController(db_path=_db(tmp_path), llm_provider=unrelated_provider)

    result = controller.answer_question("Where is cafeteria?")

    assert result["route"] == "rag_fallback"
    assert "Cafeteria" in result["answer"]
    assert result["debug"]["used_groq"] is False


def test_follow_up_question_uses_conversation_memory(tmp_path) -> None:
    calls: list[list[dict[str, str]]] = []

    def fake_provider(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        return "Grounded response."

    memory = ConversationMemory()
    controller = PublicChatController(
        db_path=_db(tmp_path),
        llm_provider=fake_provider,
        conversation_memory=memory,
    )

    first = controller.answer_question("Tell me about Faculty of Engineering")
    second = controller.answer_question("What departments does it have?")

    assert first["route"] == "rag_groq"
    assert second["route"] == "rag_groq"
    assert "Tell me about Faculty of Engineering" in calls[-1][1]["content"]
    assert "Recent conversation:" in calls[-1][1]["content"]
    assert second["intent"] == "faculty_info"


def test_clear_memory_is_safe(tmp_path) -> None:
    memory = ConversationMemory()
    memory.add_user_message("Tell me about Engineering")
    controller = PublicChatController(
        db_path=_db(tmp_path),
        llm_provider=None,
        conversation_memory=memory,
    )

    controller.clear_memory()

    assert memory.get_recent_messages() == []


def test_retry_style_repeated_answer_question_is_safe(tmp_path) -> None:
    calls: list[list[dict[str, str]]] = []

    def fake_provider(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        return "Repeated answer."

    controller = PublicChatController(db_path=_db(tmp_path), llm_provider=fake_provider)

    first = controller.answer_question("Where is cafeteria?")
    second = controller.answer_question("Where is cafeteria?")

    assert first["answer"] == "Repeated answer."
    assert second["answer"] == "Repeated answer."
    assert len(calls) == 2


def test_ambiguous_follow_up_without_context_asks_clarification(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    memory = ConversationMemory()
    memory.add_user_message("Tell me about parking on Mars")
    controller = PublicChatController(
        db_path=_db(tmp_path),
        conversation_memory=memory,
    )

    result = controller.answer_question("Tell me more")

    assert result["route"] == "no_context"
    assert result["confidence"] == "low"
    assert "clarify" in result["answer"].casefold()


def test_weak_context_gives_low_or_medium_confidence(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)

    def weak_retrieve(_question, _chunks, limit=8, intent=None):
        return [
            {
                "id": "faq:weak",
                "source": "faq",
                "title": "Weak",
                "content": "Small context.",
                "keywords": ["weak"],
                "final_score": 10,
                "score": 10,
            }
        ]

    monkeypatch.setattr(
        "controllers.public_chat_controller.retrieve_relevant_chunks",
        weak_retrieve,
    )
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("Tell me about weak context")

    assert result["confidence"] in {"low", "medium"}
    assert result["debug"]["top_score"] == 10


def test_answer_question_falls_back_safely_when_provider_fails(tmp_path) -> None:
    calls: list[list[dict[str, str]]] = []

    def failing_provider(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        raise RuntimeError("network down")

    controller = PublicChatController(db_path=_db(tmp_path), llm_provider=failing_provider)

    result = controller.answer_question("Where is cafeteria?")

    assert calls
    assert result["route"] == "rag_fallback"
    assert "Cafeteria" in result["answer"]
    assert result["sources"][0]["source"] == "rooms"
    assert set(result["sources"][0]) == {"source", "title", "score"}


def test_fake_llm_receives_limited_context(tmp_path) -> None:
    calls: list[list[dict[str, str]]] = []
    db_path = _db(tmp_path)
    long_content = "Engineering details. " * 900
    upsert_knowledge_chunks(
        db_path,
        [
            {
                "id": f"faculties:long:{index}",
                "source": "faculties",
                "title": f"Faculty of Engineering Detail {index}",
                "content": long_content,
                "keywords": ["engineering", "faculty"],
                "language": "en",
                "metadata": {},
            }
            for index in range(5)
        ],
    )

    def fake_provider(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        return "Limited context answer."

    controller = PublicChatController(db_path=db_path, llm_provider=fake_provider)

    result = controller.answer_question("Tell me about Faculty of Engineering")

    assert result["route"] == "rag_groq"
    assert calls
    assert len(calls[0][1]["content"]) < 8500
    assert "[Source:" in calls[0][1]["content"]


def test_missing_secrets_file_does_not_crash(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)

    config = load_groq_config()

    assert config == {"api_key": "", "model": "openai/gpt-oss-120b"}


def test_invalid_secrets_json_does_not_crash(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    (secrets_dir / "api_keys.json").write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr("controllers.public_chat_controller._project_root", lambda: tmp_path)

    config = load_groq_config()

    assert config == {"api_key": "", "model": "openai/gpt-oss-120b"}


def test_config_loads_api_key_from_environment_first(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "env-key")
    monkeypatch.setenv("GROQ_MODEL", "env-model")
    monkeypatch.setattr("controllers.public_chat_controller._project_root", lambda: tmp_path)

    config = load_groq_config()

    assert config == {"api_key": "env-key", "model": "env-model"}


def test_config_loads_api_key_from_secrets_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    (secrets_dir / "api_keys.json").write_text(
        '{"GROQ_API_KEY": "file-key", "GROQ_MODEL": "file-model"}',
        encoding="utf-8",
    )
    monkeypatch.setattr("controllers.public_chat_controller._project_root", lambda: tmp_path)

    config = load_groq_config()

    assert config == {"api_key": "file-key", "model": "file-model"}


def test_environment_variable_overrides_file_value(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "env-key")
    monkeypatch.setenv("GROQ_MODEL", "env-model")
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    (secrets_dir / "api_keys.json").write_text(
        '{"GROQ_API_KEY": "file-key", "GROQ_MODEL": "file-model"}',
        encoding="utf-8",
    )
    monkeypatch.setattr("controllers.public_chat_controller._project_root", lambda: tmp_path)

    config = load_groq_config()

    assert config == {"api_key": "env-key", "model": "env-model"}


def test_groq_provider_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.delenv("GROQ_MODEL", raising=False)

    provider = GroqChatProvider.from_environment()

    assert provider is not None
    assert provider.api_key == "test-key"
    assert provider.model == "openai/gpt-oss-120b"
