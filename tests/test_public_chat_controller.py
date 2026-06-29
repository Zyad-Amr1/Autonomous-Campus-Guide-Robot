"""Tests for the public dynamic chatbot controller."""

from __future__ import annotations

import sqlite3

from controllers.public_chat_controller import (
    ENGLISH_NO_CONTEXT,
    GroqChatProvider,
    PublicChatController,
    load_groq_config,
)
from controllers.university_context_controller import search_university_context
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


def test_search_university_context_returns_best_snippets(tmp_path) -> None:
    db_path = _db(tmp_path)

    results = search_university_context("Where is cafeteria?", db_path)

    assert results
    assert results[0]["source_type"] == "rooms"
    assert "Cafeteria" in results[0]["snippet"]


def test_no_api_key_uses_fallback(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("Where is student affairs?")

    assert controller.llm_provider is None
    assert result["route"] == "database_context"
    assert "Student affairs is in Building B" in result["answer"]


def test_public_chat_controller_returns_dynamic_answer_from_faq_context(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("Where is student affairs?")

    assert result["route"] == "database_context"
    assert result["confidence"] in {"high", "medium"}
    assert "Student affairs is in Building B" in result["answer"]
    assert result["sources"][0]["source_type"] == "faq"


def test_public_chat_controller_returns_professor_answer(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("Who are the professors?")

    assert "Dr. Mona Hassan" in result["answer"]
    assert result["sources"][0]["source_type"] == "professors"


def test_public_chat_controller_returns_room_answer(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("Where is cafeteria?")

    assert "Cafeteria" in result["answer"]
    assert "Student Center" in result["answer"]
    assert result["sources"][0]["source_type"] == "rooms"


def test_fallback_works_when_no_context_found(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    controller = PublicChatController(db_path=_db(tmp_path))

    result = controller.answer_question("Tell me about parking permits on Mars")

    assert result["route"] == "fallback"
    assert result["confidence"] == "low"
    assert result["sources"] == []
    assert result["answer"] == ENGLISH_NO_CONTEXT


def test_missing_secrets_file_does_not_crash(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    monkeypatch.setattr("controllers.public_chat_controller._project_root", lambda: tmp_path)

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


def test_fake_llm_provider_is_called_when_provided(tmp_path) -> None:
    calls: list[str] = []

    def fake_provider(prompt: str) -> str:
        calls.append(prompt)
        return "LLM answer from fake provider."

    controller = PublicChatController(db_path=_db(tmp_path), llm_provider=fake_provider)

    result = controller.answer_question("Where is cafeteria?")

    assert calls
    assert result["route"] == "llm"
    assert result["answer"] == "LLM answer from fake provider."


def test_api_failure_falls_back_safely(tmp_path) -> None:
    calls: list[str] = []

    def failing_provider(prompt: str) -> str:
        calls.append(prompt)
        raise RuntimeError("network down")

    controller = PublicChatController(db_path=_db(tmp_path), llm_provider=failing_provider)

    result = controller.answer_question("Where is cafeteria?")

    assert calls
    assert result["route"] == "fallback"
    assert "Cafeteria" in result["answer"]
    assert result["sources"][0]["source_type"] == "rooms"


def test_groq_provider_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.delenv("GROQ_MODEL", raising=False)

    provider = GroqChatProvider.from_environment()

    assert provider is not None
    assert provider.api_key == "test-key"
    assert provider.model == "openai/gpt-oss-120b"


def test_build_prompt_includes_context_and_question(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    controller = PublicChatController(db_path=_db(tmp_path))
    context = search_university_context("Where is cafeteria?", controller.db_path)

    prompt = controller.build_prompt("Where is cafeteria?", context)

    assert "ECU Smart Assistant" in prompt
    assert "Cafeteria" in prompt
    assert "Where is cafeteria?" in prompt
