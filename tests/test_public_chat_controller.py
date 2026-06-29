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
from controllers.rag.knowledge_chunker import build_knowledge_chunks
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
    assert ARABIC_NO_CONTEXT in messages[0]["content"]


def test_answer_question_returns_no_context_when_nothing_found(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("Tell me about parking permits on Mars")

    assert result["route"] == "no_context"
    assert result["confidence"] == "low"
    assert result["sources"] == []
    assert result["answer"] == ENGLISH_NO_CONTEXT


def test_answer_question_returns_arabic_no_context(tmp_path, monkeypatch) -> None:
    _disable_real_groq(monkeypatch, tmp_path)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("أين موقف السيارات على المريخ؟")

    assert result["route"] == "no_context"
    assert result["answer"] == ARABIC_NO_CONTEXT


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

