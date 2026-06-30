"""Tests for visitor logging and future Admin Dashboard analytics queries."""

import sqlite3

import pytest

from database.init_db import initialize_database
from database.repositories.faq_repository import create_faq
from database.repositories.log_repository import (
    count_logs,
    create_log,
    get_log_by_id,
    get_logs_by_screen,
    get_most_frequent_queries,
    get_recent_logs,
    get_unmatched_questions,
    log_chatbot_interaction,
    search_logs,
)


def create_temp_db(tmp_path):
    """Initialize and return an isolated database path for one test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    return database_path


def create_test_faq(
    db_path,
    question: str = "Where is the library?",
    answer: str = "The library is in the main building.",
) -> int:
    """Create an FAQ that can be linked to interaction logs."""
    return create_faq(question, answer, "library campus", "Campus Services", db_path)


def test_create_log_returns_new_id(tmp_path) -> None:
    """Confirm log creation returns a positive integer identifier."""
    db_path = create_temp_db(tmp_path)

    log_id = create_log("Where is the library?", db_path=db_path)

    assert isinstance(log_id, int)
    assert log_id > 0


def test_create_log_saves_data_correctly(tmp_path) -> None:
    """Confirm log fields and joined FAQ context are persisted correctly."""
    db_path = create_temp_db(tmp_path)
    faq_id = create_test_faq(db_path)

    log_id = create_log(
        "  Where is the library?  ",
        faq_id,
        "  The library is in the main building.  ",
        "  Public Assistant  ",
        db_path,
    )
    log = get_log_by_id(log_id, db_path)

    assert log is not None
    assert log["query_text"] == "Where is the library?"
    assert log["response_text"] == "The library is in the main building."
    assert log["screen_name"] == "Public Assistant"
    assert log["matched_question"] == "Where is the library?"
    assert log["matched_answer"] == "The library is in the main building."


def test_create_log_rejects_empty_query_text(tmp_path) -> None:
    """Confirm interaction logs require a non-empty visitor query."""
    db_path = create_temp_db(tmp_path)

    with pytest.raises(ValueError, match="Query text cannot be empty"):
        create_log("   ", db_path=db_path)


def test_create_log_rejects_invalid_matched_faq_id(tmp_path) -> None:
    """Confirm invalid FAQ relationships are rejected by SQLite."""
    db_path = create_temp_db(tmp_path)

    with pytest.raises(sqlite3.IntegrityError):
        create_log("Question", matched_faq_id=999999, db_path=db_path)


def test_get_log_by_id_returns_none_for_missing_id(tmp_path) -> None:
    """Confirm lookup returns ``None`` for an unknown log identifier."""
    db_path = create_temp_db(tmp_path)

    assert get_log_by_id(999999, db_path) is None


def test_get_recent_logs_returns_newest_first_and_respects_limit(tmp_path) -> None:
    """Confirm recent history uses newest-first ordering and applies its limit."""
    db_path = create_temp_db(tmp_path)
    create_log("First query", db_path=db_path)
    create_log("Second query", db_path=db_path)
    create_log("Third query", db_path=db_path)

    logs = get_recent_logs(limit=2, db_path=db_path)

    assert len(logs) == 2
    assert [log["query_text"] for log in logs] == ["Third query", "Second query"]


def test_get_recent_logs_rejects_invalid_limit(tmp_path) -> None:
    """Confirm recent-history limits must be positive."""
    db_path = create_temp_db(tmp_path)

    with pytest.raises(ValueError, match="Limit must be a positive integer"):
        get_recent_logs(limit=0, db_path=db_path)


def test_count_logs_returns_correct_number(tmp_path) -> None:
    """Confirm the repository reports the current interaction total."""
    db_path = create_temp_db(tmp_path)
    create_log("First query", db_path=db_path)
    create_log("Second query", db_path=db_path)
    create_log("Third query", db_path=db_path)

    assert count_logs(db_path) == 3


def test_search_logs_matches_query_response_screen_and_faq_fields(tmp_path) -> None:
    """Confirm search covers log content, screens, and joined FAQ fields."""
    db_path = create_temp_db(tmp_path)
    library_faq_id = create_test_faq(db_path)
    admission_faq_id = create_test_faq(
        db_path,
        "How do I apply for admission?",
        "Complete the online application form.",
    )
    create_log(
        "Find books",
        library_faq_id,
        "Go upstairs to the library.",
        "Public Assistant",
        db_path,
    )
    create_log(
        "Application help",
        admission_faq_id,
        "Open the admissions portal.",
        "Admissions Screen",
        db_path,
    )

    expected_searches = {
        "Find books": "Find books",
        "upstairs": "Find books",
        "Admissions Screen": "Application help",
        "Where is the library": "Find books",
        "online application": "Application help",
    }
    for search_text, expected_query in expected_searches.items():
        assert [log["query_text"] for log in search_logs(search_text, db_path)] == [
            expected_query
        ]


def test_search_logs_with_empty_text_returns_recent_logs(tmp_path) -> None:
    """Confirm a blank search returns standard recent-log history."""
    db_path = create_temp_db(tmp_path)
    create_log("First query", db_path=db_path)
    create_log("Second query", db_path=db_path)

    logs = search_logs("   ", db_path)

    assert [log["query_text"] for log in logs] == ["Second query", "First query"]


def test_get_most_frequent_queries_returns_grouped_counts(tmp_path) -> None:
    """Confirm repeated queries are grouped and ranked by frequency."""
    db_path = create_temp_db(tmp_path)
    create_log("Where is the library?", db_path=db_path)
    create_log("Where is the library?", db_path=db_path)
    create_log("Where is the library?", db_path=db_path)
    create_log("How do I apply?", db_path=db_path)
    create_log("How do I apply?", db_path=db_path)

    rows = get_most_frequent_queries(db_path=db_path)

    assert [(row["query_text"], row["query_count"]) for row in rows] == [
        ("Where is the library?", 3),
        ("How do I apply?", 2),
    ]


def test_get_most_frequent_queries_respects_limit(tmp_path) -> None:
    """Confirm query analytics apply the requested row limit."""
    db_path = create_temp_db(tmp_path)
    create_log("Query A", db_path=db_path)
    create_log("Query B", db_path=db_path)
    create_log("Query C", db_path=db_path)

    rows = get_most_frequent_queries(limit=1, db_path=db_path)

    assert len(rows) == 1


def test_get_most_frequent_queries_rejects_invalid_limit(tmp_path) -> None:
    """Confirm analytics limits must be positive."""
    db_path = create_temp_db(tmp_path)

    with pytest.raises(ValueError, match="Limit must be a positive integer"):
        get_most_frequent_queries(limit=0, db_path=db_path)


def test_get_logs_by_screen_returns_matching_logs_case_insensitive(tmp_path) -> None:
    """Confirm screen filtering is case-insensitive and exclusive."""
    db_path = create_temp_db(tmp_path)
    create_log("Assistant query", screen_name="Public Assistant", db_path=db_path)
    create_log("Admin query", screen_name="Admin Dashboard", db_path=db_path)

    logs = get_logs_by_screen("pUbLiC aSsIsTaNt", db_path)

    assert [log["query_text"] for log in logs] == ["Assistant query"]


def test_get_logs_by_screen_with_empty_screen_returns_empty_list(tmp_path) -> None:
    """Confirm blank screen filters return no interaction logs."""
    db_path = create_temp_db(tmp_path)

    assert get_logs_by_screen("   ", db_path) == []


def test_get_unmatched_questions_returns_only_logs_without_matched_faq(tmp_path) -> None:
    """Confirm unanswered-query analytics exclude FAQ-matched interactions."""
    db_path = create_temp_db(tmp_path)
    faq_id = create_test_faq(db_path)
    create_log("Where is the library?", matched_faq_id=faq_id, db_path=db_path)
    create_log("Is there an astronomy club?", matched_faq_id=None, db_path=db_path)

    logs = get_unmatched_questions(db_path)

    assert [log["query_text"] for log in logs] == ["Is there an astronomy club?"]


def test_log_chatbot_interaction_creates_logs_table_if_missing(tmp_path) -> None:
    db_path = tmp_path / "chatbot_logs.db"

    assert log_chatbot_interaction(db_path, "Where is engineering?", "database", True)

    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'logs'
            """
        ).fetchone()
        assert row is not None
    finally:
        connection.close()


def test_log_chatbot_interaction_inserts_chatbot_interaction(tmp_path) -> None:
    db_path = tmp_path / "chatbot_logs.db"

    assert log_chatbot_interaction(
        db_path,
        "Where is engineering?",
        "database",
        True,
        timestamp="2026-06-30T12:00:00",
    )

    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute("SELECT * FROM logs").fetchone()
        assert row[1:] == (
            "2026-06-30T12:00:00",
            "chatbot_interaction",
            "Where is engineering?",
            "database",
            1,
        )
    finally:
        connection.close()


def test_log_chatbot_interaction_works_with_existing_log_schema(tmp_path) -> None:
    db_path = create_temp_db(tmp_path)

    assert log_chatbot_interaction(db_path, "Where is engineering?", "database", True)

    logs = get_recent_logs(limit=1, db_path=db_path)
    assert logs[0]["query_text"] == "Where is engineering?"
    assert logs[0]["screen_name"] == "chatbot_interaction"
    assert logs[0]["response_text"] == "source_used=database; had_context=1"


def test_log_chatbot_interaction_returns_false_on_failure(tmp_path) -> None:
    assert (
        log_chatbot_interaction(
            tmp_path,
            "Where is engineering?",
            "database",
            True,
        )
        is False
    )


def test_log_chatbot_interaction_returns_false_for_incompatible_logs_table(
    tmp_path,
) -> None:
    db_path = tmp_path / "incompatible.db"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("CREATE TABLE logs (id INTEGER PRIMARY KEY AUTOINCREMENT)")
        connection.commit()
    finally:
        connection.close()

    assert (
        log_chatbot_interaction(db_path, "Where is engineering?", "database", True)
        is False
    )
