"""Phase 1 integration tests for the complete ECU robot database foundation."""

import sqlite3

import pytest

from database.check_tables import get_table_names
from database.init_db import initialize_database


def test_phase1_database_initialization_creates_expected_tables(tmp_path) -> None:
    """Confirm initialization creates exactly the Phase 1 application tables."""
    temp_db_path = tmp_path / "test_ecu_robot.db"

    initialize_database(temp_db_path)
    table_names = get_table_names(temp_db_path)

    assert table_names == [
        "admin",
        "courses",
        "events",
        "faculties",
        "faq",
        "logs",
        "professors",
        "rooms",
    ]


def test_phase1_default_admin_is_seeded_securely(tmp_path) -> None:
    """Confirm the initial administrator is unique and securely represented."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    connection = sqlite3.connect(temp_db_path)
    try:
        admin_rows = connection.execute(
            "SELECT username, full_name, role, password_hash FROM admin"
        ).fetchall()
    finally:
        connection.close()

    assert len(admin_rows) == 1
    username, full_name, role, password_hash = admin_rows[0]
    assert username == "admin"
    assert full_name == "System Administrator"
    assert role == "super_admin"
    assert password_hash != "admin123"
    assert password_hash.startswith("pbkdf2_sha256$100000$")


def test_phase1_database_initialization_is_idempotent(tmp_path) -> None:
    """Confirm repeated initialization does not duplicate the administrator."""
    temp_db_path = tmp_path / "test_ecu_robot.db"

    initialize_database(temp_db_path)
    initialize_database(temp_db_path)

    connection = sqlite3.connect(temp_db_path)
    try:
        admin_count = connection.execute("SELECT COUNT(*) FROM admin").fetchone()[0]
    finally:
        connection.close()

    assert admin_count == 1


def test_phase1_foreign_keys_are_enabled_and_valid(tmp_path) -> None:
    """Confirm valid academic relationships succeed and invalid ones are rejected."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    connection = sqlite3.connect(temp_db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON;")

        faculty_id = connection.execute(
            "INSERT INTO faculties (name) VALUES (?)",
            ("Faculty of Engineering",),
        ).lastrowid
        room_id = connection.execute(
            """
            INSERT INTO rooms (room_name, room_number, building, floor, category)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Robotics Laboratory", "R101", "Engineering", 1, "Laboratory"),
        ).lastrowid
        professor_id = connection.execute(
            """
            INSERT INTO professors (full_name, faculty_id, office_room_id)
            VALUES (?, ?, ?)
            """,
            ("Dr. Test Professor", faculty_id, room_id),
        ).lastrowid
        course_id = connection.execute(
            """
            INSERT INTO courses (
                course_code,
                course_name,
                faculty_id,
                professor_id,
                room_id,
                schedule_day,
                start_time,
                end_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ROB101",
                "Introduction to Robotics",
                faculty_id,
                professor_id,
                room_id,
                "Sunday",
                "09:00",
                "10:30",
            ),
        ).lastrowid

        course_row = connection.execute(
            "SELECT id FROM courses WHERE id = ?",
            (course_id,),
        ).fetchone()
        assert course_row is not None

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO professors (full_name, faculty_id) VALUES (?, ?)",
                ("Invalid Professor", 999999),
            )
    finally:
        connection.close()


def test_phase1_logs_can_reference_faq(tmp_path) -> None:
    """Confirm assistant interaction logs can retain their matched FAQ answer."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    connection = sqlite3.connect(temp_db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON;")
        faq_id = connection.execute(
            "INSERT INTO faq (question, answer) VALUES (?, ?)",
            ("Where is the library?", "The library is in the main building."),
        ).lastrowid
        connection.execute(
            "INSERT INTO logs (query_text, matched_faq_id) VALUES (?, ?)",
            ("How can I find the library?", faq_id),
        )

        result = connection.execute(
            """
            SELECT logs.query_text, faq.answer
            FROM logs
            JOIN faq ON faq.id = logs.matched_faq_id
            """
        ).fetchone()
    finally:
        connection.close()

    assert result == (
        "How can I find the library?",
        "The library is in the main building.",
    )
