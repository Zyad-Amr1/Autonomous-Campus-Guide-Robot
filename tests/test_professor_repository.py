"""Tests for professor operations shared by the ECU robot applications."""

import sqlite3

import pytest

from database.connection import get_connection
from database.init_db import initialize_database
from database.repositories.faculty_repository import create_faculty
from database.repositories.professor_repository import (
    count_professors,
    create_professor,
    delete_professor,
    get_all_professors,
    get_professor_by_id,
    search_professors,
    update_professor,
)


def create_temp_db(tmp_path):
    """Initialize and return an isolated database path for one test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    return database_path


def create_test_faculty(db_path, name: str = "Engineering") -> int:
    """Create a faculty required by professor foreign keys."""
    return create_faculty(name, db_path=db_path)


def create_test_room(db_path) -> int:
    """Create a room directly until a dedicated room repository exists."""
    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO rooms (room_name, room_number, building, floor, category)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Academic Office", "A101", "Building A", 1, "Office"),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def test_create_professor_returns_new_id(tmp_path) -> None:
    """Confirm professor creation returns a positive integer identifier."""
    db_path = create_temp_db(tmp_path)
    faculty_id = create_test_faculty(db_path)

    professor_id = create_professor("Dr. Ahmed Ali", "Professor", faculty_id, db_path=db_path)

    assert isinstance(professor_id, int)
    assert professor_id > 0


def test_create_professor_saves_data_correctly(tmp_path) -> None:
    """Confirm all professor fields and joined display values are saved."""
    db_path = create_temp_db(tmp_path)
    faculty_id = create_test_faculty(db_path)
    room_id = create_test_room(db_path)

    professor_id = create_professor(
        "  Dr. Mona Hassan  ",
        "  Associate Professor  ",
        faculty_id,
        room_id,
        "  mona.hassan@ecu.edu.eg  ",
        "  01000000000  ",
        "  Sunday 10:00-12:00  ",
        "  images/mona.jpg  ",
        "  Robotics researcher  ",
        db_path,
    )
    professor = get_professor_by_id(professor_id, db_path)

    assert professor is not None
    assert professor["full_name"] == "Dr. Mona Hassan"
    assert professor["title"] == "Associate Professor"
    assert professor["email"] == "mona.hassan@ecu.edu.eg"
    assert professor["phone"] == "01000000000"
    assert professor["office_hours"] == "Sunday 10:00-12:00"
    assert professor["photo_path"] == "images/mona.jpg"
    assert professor["bio"] == "Robotics researcher"
    assert professor["faculty_name"] == "Engineering"
    assert professor["office_room_name"] is not None


def test_create_professor_rejects_empty_full_name(tmp_path) -> None:
    """Confirm whitespace-only professor names are rejected."""
    db_path = create_temp_db(tmp_path)
    faculty_id = create_test_faculty(db_path)

    with pytest.raises(ValueError, match="Professor full name cannot be empty"):
        create_professor("   ", None, faculty_id, db_path=db_path)


def test_create_professor_rejects_invalid_faculty_id(tmp_path) -> None:
    """Confirm faculty foreign-key violations are surfaced by SQLite."""
    db_path = create_temp_db(tmp_path)

    with pytest.raises(sqlite3.IntegrityError):
        create_professor("Dr. Invalid", None, 999999, db_path=db_path)


def test_get_professor_by_id_returns_none_for_missing_id(tmp_path) -> None:
    """Confirm lookup returns ``None`` for an unknown professor identifier."""
    db_path = create_temp_db(tmp_path)

    assert get_professor_by_id(999999, db_path) is None


def test_get_all_professors_returns_ordered_rows(tmp_path) -> None:
    """Confirm professor records are returned alphabetically."""
    db_path = create_temp_db(tmp_path)
    faculty_id = create_test_faculty(db_path)
    create_professor("Dr. Ziad Omar", None, faculty_id, db_path=db_path)
    create_professor("Dr. Ahmed Ali", None, faculty_id, db_path=db_path)
    create_professor("Dr. Mona Hassan", None, faculty_id, db_path=db_path)

    professors = get_all_professors(db_path)

    assert [professor["full_name"] for professor in professors] == [
        "Dr. Ahmed Ali",
        "Dr. Mona Hassan",
        "Dr. Ziad Omar",
    ]


def test_update_professor_updates_existing_row(tmp_path) -> None:
    """Confirm all editable professor fields can be updated."""
    db_path = create_temp_db(tmp_path)
    faculty_id = create_test_faculty(db_path)
    room_id = create_test_room(db_path)
    professor_id = create_professor("Dr. Ahmed Ali", None, faculty_id, db_path=db_path)

    was_updated = update_professor(
        professor_id,
        "  Dr. Ahmed Ibrahim  ",
        "  Professor  ",
        faculty_id,
        room_id,
        "  ahmed.ibrahim@ecu.edu.eg  ",
        "  01111111111  ",
        "  Monday 11:00-13:00  ",
        "  images/ahmed.jpg  ",
        "  Artificial intelligence researcher  ",
        db_path,
    )
    professor = get_professor_by_id(professor_id, db_path)

    assert was_updated is True
    assert professor is not None
    assert professor["full_name"] == "Dr. Ahmed Ibrahim"
    assert professor["title"] == "Professor"
    assert professor["office_room_id"] == room_id
    assert professor["email"] == "ahmed.ibrahim@ecu.edu.eg"
    assert professor["phone"] == "01111111111"
    assert professor["office_hours"] == "Monday 11:00-13:00"
    assert professor["photo_path"] == "images/ahmed.jpg"
    assert professor["bio"] == "Artificial intelligence researcher"


def test_update_professor_returns_false_for_missing_id(tmp_path) -> None:
    """Confirm updating an unknown professor reports no change."""
    db_path = create_temp_db(tmp_path)
    faculty_id = create_test_faculty(db_path)

    assert (
        update_professor(999999, "Dr. Missing", None, faculty_id, db_path=db_path)
        is False
    )


def test_update_professor_rejects_empty_full_name(tmp_path) -> None:
    """Confirm updates reject whitespace-only professor names."""
    db_path = create_temp_db(tmp_path)
    faculty_id = create_test_faculty(db_path)

    with pytest.raises(ValueError, match="Professor full name cannot be empty"):
        update_professor(1, "   ", None, faculty_id, db_path=db_path)


def test_delete_professor_removes_existing_row(tmp_path) -> None:
    """Confirm deleting a professor removes its database record."""
    db_path = create_temp_db(tmp_path)
    faculty_id = create_test_faculty(db_path)
    professor_id = create_professor("Dr. Ahmed Ali", None, faculty_id, db_path=db_path)

    was_deleted = delete_professor(professor_id, db_path)

    assert was_deleted is True
    assert get_professor_by_id(professor_id, db_path) is None


def test_delete_professor_returns_false_for_missing_id(tmp_path) -> None:
    """Confirm deleting an unknown professor reports no change."""
    db_path = create_temp_db(tmp_path)

    assert delete_professor(999999, db_path) is False


def test_count_professors_returns_correct_number(tmp_path) -> None:
    """Confirm the repository reports the current professor total."""
    db_path = create_temp_db(tmp_path)
    faculty_id = create_test_faculty(db_path)
    create_professor("Dr. Ahmed Ali", None, faculty_id, db_path=db_path)
    create_professor("Dr. Mona Hassan", None, faculty_id, db_path=db_path)
    create_professor("Dr. Ziad Omar", None, faculty_id, db_path=db_path)

    assert count_professors(db_path) == 3


def test_search_professors_matches_name_title_email_faculty(tmp_path) -> None:
    """Confirm search covers professor and related faculty text fields."""
    db_path = create_temp_db(tmp_path)
    engineering_id = create_test_faculty(db_path, "Engineering")
    business_id = create_test_faculty(db_path, "Business")
    create_professor(
        "Dr. Mona Hassan",
        "Associate Professor",
        engineering_id,
        email="mona.hassan@ecu.edu.eg",
        office_hours="Sunday 10:00-12:00",
        db_path=db_path,
    )
    create_professor(
        "Dr. Ahmed Ali",
        "Lecturer",
        business_id,
        email="ahmed.ali@ecu.edu.eg",
        office_hours="Monday 09:00-11:00",
        db_path=db_path,
    )

    assert [row["full_name"] for row in search_professors("Mona", db_path)] == [
        "Dr. Mona Hassan"
    ]
    assert [row["full_name"] for row in search_professors("Lecturer", db_path)] == [
        "Dr. Ahmed Ali"
    ]
    assert [
        row["full_name"]
        for row in search_professors("mona.hassan@ecu.edu.eg", db_path)
    ] == ["Dr. Mona Hassan"]
    assert [row["full_name"] for row in search_professors("Business", db_path)] == [
        "Dr. Ahmed Ali"
    ]
    assert [row["full_name"] for row in search_professors("Sunday", db_path)] == [
        "Dr. Mona Hassan"
    ]


def test_search_professors_with_empty_text_returns_all(tmp_path) -> None:
    """Confirm a blank search returns every professor in standard order."""
    db_path = create_temp_db(tmp_path)
    faculty_id = create_test_faculty(db_path)
    create_professor("Dr. Ziad Omar", None, faculty_id, db_path=db_path)
    create_professor("Dr. Ahmed Ali", None, faculty_id, db_path=db_path)

    professors = search_professors("   ", db_path)

    assert [professor["full_name"] for professor in professors] == [
        "Dr. Ahmed Ali",
        "Dr. Ziad Omar",
    ]
