"""Tests for faculty CRUD operations used by the future Admin Dashboard."""

import pytest

from database.init_db import initialize_database
from database.repositories.faculty_repository import (
    count_faculties,
    create_faculty,
    delete_faculty,
    get_all_faculties,
    get_faculty_by_id,
    update_faculty,
)


def test_create_faculty_returns_new_id(tmp_path) -> None:
    """Confirm faculty creation returns a positive integer identifier."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    faculty_id = create_faculty("Engineering", db_path=temp_db_path)

    assert isinstance(faculty_id, int)
    assert faculty_id > 0


def test_create_faculty_saves_data_correctly(tmp_path) -> None:
    """Confirm faculty fields are normalized and persisted correctly."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    faculty_id = create_faculty(
        "  Engineering  ",
        "  Engineering programs  ",
        "  Building A  ",
        "  Dr. Ahmed Hassan  ",
        temp_db_path,
    )
    faculty = get_faculty_by_id(faculty_id, temp_db_path)

    assert faculty is not None
    assert faculty["name"] == "Engineering"
    assert faculty["description"] == "Engineering programs"
    assert faculty["building"] == "Building A"
    assert faculty["dean_name"] == "Dr. Ahmed Hassan"


def test_create_faculty_rejects_empty_name(tmp_path) -> None:
    """Confirm whitespace-only faculty names are rejected."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    with pytest.raises(ValueError, match="Faculty name cannot be empty"):
        create_faculty("   ", db_path=temp_db_path)


def test_get_all_faculties_returns_ordered_rows(tmp_path) -> None:
    """Confirm faculty records are returned alphabetically."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)
    create_faculty("Medicine", db_path=temp_db_path)
    create_faculty("Business", db_path=temp_db_path)
    create_faculty("Engineering", db_path=temp_db_path)

    faculties = get_all_faculties(temp_db_path)

    assert [faculty["name"] for faculty in faculties] == [
        "Business",
        "Engineering",
        "Medicine",
    ]


def test_get_faculty_by_id_returns_none_for_missing_id(tmp_path) -> None:
    """Confirm lookup returns ``None`` for an unknown faculty identifier."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    assert get_faculty_by_id(999999, temp_db_path) is None


def test_update_faculty_updates_existing_row(tmp_path) -> None:
    """Confirm all editable faculty fields can be updated."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)
    faculty_id = create_faculty("Engineering", db_path=temp_db_path)

    was_updated = update_faculty(
        faculty_id,
        "  Applied Engineering  ",
        "  Updated description  ",
        "  Building B  ",
        "  Dr. Mona Ali  ",
        temp_db_path,
    )
    faculty = get_faculty_by_id(faculty_id, temp_db_path)

    assert was_updated is True
    assert faculty is not None
    assert faculty["name"] == "Applied Engineering"
    assert faculty["description"] == "Updated description"
    assert faculty["building"] == "Building B"
    assert faculty["dean_name"] == "Dr. Mona Ali"


def test_update_faculty_returns_false_for_missing_id(tmp_path) -> None:
    """Confirm updating an unknown faculty reports no change."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    assert update_faculty(999999, "Engineering", db_path=temp_db_path) is False


def test_update_faculty_rejects_empty_name(tmp_path) -> None:
    """Confirm updates reject whitespace-only faculty names."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    with pytest.raises(ValueError, match="Faculty name cannot be empty"):
        update_faculty(1, "   ", db_path=temp_db_path)


def test_delete_faculty_removes_existing_row(tmp_path) -> None:
    """Confirm deleting a faculty removes its database record."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)
    faculty_id = create_faculty("Engineering", db_path=temp_db_path)

    was_deleted = delete_faculty(faculty_id, temp_db_path)

    assert was_deleted is True
    assert get_faculty_by_id(faculty_id, temp_db_path) is None


def test_delete_faculty_returns_false_for_missing_id(tmp_path) -> None:
    """Confirm deleting an unknown faculty reports no change."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    assert delete_faculty(999999, temp_db_path) is False


def test_count_faculties_returns_correct_number(tmp_path) -> None:
    """Confirm the repository reports the current faculty total."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)
    create_faculty("Engineering", db_path=temp_db_path)
    create_faculty("Business", db_path=temp_db_path)
    create_faculty("Medicine", db_path=temp_db_path)

    assert count_faculties(temp_db_path) == 3
