"""Tests for room and map operations shared by the ECU robot applications."""

import sqlite3

import pytest

from database.init_db import initialize_database
from database.repositories.room_repository import (
    count_rooms,
    create_room,
    delete_room,
    get_all_rooms,
    get_mappable_rooms,
    get_room_by_id,
    get_rooms_by_category,
    search_rooms,
    update_room,
)


def create_temp_db(tmp_path):
    """Initialize and return an isolated database path for one test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    return database_path


def test_create_room_returns_new_id(tmp_path) -> None:
    """Confirm room creation returns a positive integer identifier."""
    db_path = create_temp_db(tmp_path)

    room_id = create_room(
        "Robotics Laboratory",
        "R101",
        "Engineering",
        1,
        "Laboratory",
        db_path=db_path,
    )

    assert isinstance(room_id, int)
    assert room_id > 0


def test_create_room_saves_data_correctly(tmp_path) -> None:
    """Confirm all room fields are normalized and persisted correctly."""
    db_path = create_temp_db(tmp_path)

    room_id = create_room(
        "  Robotics Laboratory  ",
        "  R101  ",
        "  Engineering  ",
        1,
        "  Laboratory  ",
        "  Advanced robotics equipment  ",
        125.5,
        240.25,
        db_path,
    )
    room = get_room_by_id(room_id, db_path)

    assert room is not None
    assert room["room_name"] == "Robotics Laboratory"
    assert room["room_number"] == "R101"
    assert room["building"] == "Engineering"
    assert room["floor"] == 1
    assert room["category"] == "Laboratory"
    assert room["description"] == "Advanced robotics equipment"
    assert room["x_coord"] == 125.5
    assert room["y_coord"] == 240.25


def test_create_room_rejects_empty_required_fields(tmp_path) -> None:
    """Confirm each required room text field rejects blank input."""
    db_path = create_temp_db(tmp_path)
    valid_values = {
        "room_name": "Robotics Laboratory",
        "room_number": "R101",
        "building": "Engineering",
        "floor": 1,
        "category": "Laboratory",
    }

    for field_name in ("room_name", "room_number", "building", "category"):
        invalid_values = valid_values.copy()
        invalid_values[field_name] = "   "
        with pytest.raises(ValueError):
            create_room(**invalid_values, db_path=db_path)


def test_create_room_rejects_non_integer_floor(tmp_path) -> None:
    """Confirm non-integer floor values are rejected."""
    db_path = create_temp_db(tmp_path)

    with pytest.raises(ValueError, match="Floor must be an integer"):
        create_room(
            "Robotics Laboratory",
            "R101",
            "Engineering",
            "first",  # type: ignore[arg-type]
            "Laboratory",
            db_path=db_path,
        )


def test_create_room_rejects_duplicate_building_floor_room_number(tmp_path) -> None:
    """Confirm SQLite enforces each room's unique physical location."""
    db_path = create_temp_db(tmp_path)
    create_room("Robotics Laboratory", "R101", "Engineering", 1, "Laboratory", db_path=db_path)

    with pytest.raises(sqlite3.IntegrityError):
        create_room("Second Lab", "R101", "Engineering", 1, "Laboratory", db_path=db_path)


def test_get_room_by_id_returns_none_for_missing_id(tmp_path) -> None:
    """Confirm lookup returns ``None`` for an unknown room identifier."""
    db_path = create_temp_db(tmp_path)

    assert get_room_by_id(999999, db_path) is None


def test_get_all_rooms_returns_ordered_rows(tmp_path) -> None:
    """Confirm rooms use stable building, floor, and room-number ordering."""
    db_path = create_temp_db(tmp_path)
    create_room("Room B2", "B200", "Building B", 2, "Classroom", db_path=db_path)
    create_room("Room A2", "A201", "Building A", 2, "Classroom", db_path=db_path)
    create_room("Room A1-2", "A102", "Building A", 1, "Classroom", db_path=db_path)
    create_room("Room A1-1", "A101", "Building A", 1, "Classroom", db_path=db_path)

    rooms = get_all_rooms(db_path)

    assert [
        (room["building"], room["floor"], room["room_number"]) for room in rooms
    ] == [
        ("Building A", 1, "A101"),
        ("Building A", 1, "A102"),
        ("Building A", 2, "A201"),
        ("Building B", 2, "B200"),
    ]


def test_update_room_updates_existing_row(tmp_path) -> None:
    """Confirm all editable room fields can be updated."""
    db_path = create_temp_db(tmp_path)
    room_id = create_room("Old Room", "A101", "Building A", 1, "Classroom", db_path=db_path)

    was_updated = update_room(
        room_id,
        "  Innovation Laboratory  ",
        "  B205  ",
        "  Building B  ",
        2,
        "  Laboratory  ",
        "  Updated room  ",
        300.0,
        450.0,
        db_path,
    )
    room = get_room_by_id(room_id, db_path)

    assert was_updated is True
    assert room is not None
    assert room["room_name"] == "Innovation Laboratory"
    assert room["room_number"] == "B205"
    assert room["building"] == "Building B"
    assert room["floor"] == 2
    assert room["category"] == "Laboratory"
    assert room["description"] == "Updated room"
    assert room["x_coord"] == 300.0
    assert room["y_coord"] == 450.0


def test_update_room_returns_false_for_missing_id(tmp_path) -> None:
    """Confirm updating an unknown room reports no change."""
    db_path = create_temp_db(tmp_path)

    assert (
        update_room(
            999999,
            "Room",
            "A101",
            "Building A",
            1,
            "Classroom",
            db_path=db_path,
        )
        is False
    )


def test_update_room_rejects_empty_required_fields(tmp_path) -> None:
    """Confirm updates validate every required room text field."""
    db_path = create_temp_db(tmp_path)
    room_id = create_room("Room", "A101", "Building A", 1, "Classroom", db_path=db_path)
    valid_values = {
        "room_name": "Updated Room",
        "room_number": "A102",
        "building": "Building A",
        "floor": 1,
        "category": "Classroom",
    }

    for field_name in ("room_name", "room_number", "building", "category"):
        invalid_values = valid_values.copy()
        invalid_values[field_name] = "   "
        with pytest.raises(ValueError):
            update_room(room_id, **invalid_values, db_path=db_path)


def test_delete_room_removes_existing_row(tmp_path) -> None:
    """Confirm deleting a room removes its database record."""
    db_path = create_temp_db(tmp_path)
    room_id = create_room("Room", "A101", "Building A", 1, "Classroom", db_path=db_path)

    was_deleted = delete_room(room_id, db_path)

    assert was_deleted is True
    assert get_room_by_id(room_id, db_path) is None


def test_delete_room_returns_false_for_missing_id(tmp_path) -> None:
    """Confirm deleting an unknown room reports no change."""
    db_path = create_temp_db(tmp_path)

    assert delete_room(999999, db_path) is False


def test_count_rooms_returns_correct_number(tmp_path) -> None:
    """Confirm the repository reports the current room total."""
    db_path = create_temp_db(tmp_path)
    create_room("Room 1", "A101", "Building A", 1, "Classroom", db_path=db_path)
    create_room("Room 2", "A102", "Building A", 1, "Classroom", db_path=db_path)
    create_room("Room 3", "B201", "Building B", 2, "Office", db_path=db_path)

    assert count_rooms(db_path) == 3


def test_search_rooms_matches_name_number_building_category_description(tmp_path) -> None:
    """Confirm search covers every requested room text field."""
    db_path = create_temp_db(tmp_path)
    create_room(
        "Robotics Laboratory",
        "R101",
        "Engineering",
        1,
        "Laboratory",
        "Advanced robotics equipment",
        db_path=db_path,
    )
    create_room(
        "Student Services",
        "S201",
        "Main Building",
        2,
        "Office",
        "Enrollment support",
        db_path=db_path,
    )

    assert [room["room_name"] for room in search_rooms("Robotics", db_path)] == [
        "Robotics Laboratory"
    ]
    assert [room["room_name"] for room in search_rooms("S201", db_path)] == [
        "Student Services"
    ]
    assert [room["room_name"] for room in search_rooms("Engineering", db_path)] == [
        "Robotics Laboratory"
    ]
    assert [room["room_name"] for room in search_rooms("Office", db_path)] == [
        "Student Services"
    ]
    assert [room["room_name"] for room in search_rooms("Enrollment", db_path)] == [
        "Student Services"
    ]


def test_search_rooms_with_empty_text_returns_all(tmp_path) -> None:
    """Confirm a blank search returns every room in standard order."""
    db_path = create_temp_db(tmp_path)
    create_room("Room B", "B201", "Building B", 2, "Office", db_path=db_path)
    create_room("Room A", "A101", "Building A", 1, "Classroom", db_path=db_path)

    rooms = search_rooms("   ", db_path)

    assert [room["room_name"] for room in rooms] == ["Room A", "Room B"]


def test_get_rooms_by_category_returns_matching_rooms(tmp_path) -> None:
    """Confirm category filtering is case-insensitive and exclusive."""
    db_path = create_temp_db(tmp_path)
    create_room("Lab 1", "A101", "Building A", 1, "Laboratory", db_path=db_path)
    create_room("Lab 2", "A102", "Building A", 1, "Laboratory", db_path=db_path)
    create_room("Office", "B201", "Building B", 2, "Office", db_path=db_path)

    rooms = get_rooms_by_category("laboratory", db_path)

    assert [room["room_name"] for room in rooms] == ["Lab 1", "Lab 2"]


def test_get_mappable_rooms_returns_only_rooms_with_coordinates(tmp_path) -> None:
    """Confirm map queries require both coordinate values."""
    db_path = create_temp_db(tmp_path)
    create_room(
        "Mapped Room",
        "A101",
        "Building A",
        1,
        "Classroom",
        x_coord=100.0,
        y_coord=200.0,
        db_path=db_path,
    )
    create_room("Unmapped Room", "A102", "Building A", 1, "Classroom", db_path=db_path)
    create_room(
        "Partial Room",
        "A103",
        "Building A",
        1,
        "Classroom",
        x_coord=150.0,
        db_path=db_path,
    )

    rooms = get_mappable_rooms(db_path)

    assert [room["room_name"] for room in rooms] == ["Mapped Room"]
