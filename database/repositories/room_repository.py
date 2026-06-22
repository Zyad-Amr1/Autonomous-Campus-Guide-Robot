"""Isolate room and map database operations from the system's UI layers."""

import sqlite3
from pathlib import Path

from database.connection import DB_NAME, get_connection

_ROOM_ORDER_SQL = " ORDER BY building ASC, floor ASC, room_number ASC"


def _clean_text(value: str) -> str:
    """Return required text with surrounding whitespace removed."""
    return value.strip()


def _clean_optional_text(value: str | None) -> str | None:
    """Normalize optional text and convert blank values to ``None``."""
    if value is None:
        return None
    cleaned_value = value.strip()
    return cleaned_value or None


def _validate_room_fields(
    room_name: str,
    room_number: str,
    building: str,
    floor: int,
    category: str,
) -> tuple[str, str, str, str]:
    """Validate and normalize fields required by every room record."""
    normalized_name = _clean_text(room_name)
    normalized_number = _clean_text(room_number)
    normalized_building = _clean_text(building)
    normalized_category = _clean_text(category)

    if not normalized_name:
        raise ValueError("Room name cannot be empty.")
    if not normalized_number:
        raise ValueError("Room number cannot be empty.")
    if not normalized_building:
        raise ValueError("Building cannot be empty.")
    if not normalized_category:
        raise ValueError("Room category cannot be empty.")
    if not isinstance(floor, int) or isinstance(floor, bool):
        raise ValueError("Floor must be an integer.")

    return (
        normalized_name,
        normalized_number,
        normalized_building,
        normalized_category,
    )


def create_room(
    room_name: str,
    room_number: str,
    building: str,
    floor: int,
    category: str,
    description: str | None = None,
    x_coord: float | None = None,
    y_coord: float | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    """Create a validated room and return its database identifier."""
    name, number, normalized_building, normalized_category = _validate_room_fields(
        room_name,
        room_number,
        building,
        floor,
        category,
    )

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO rooms (
                room_name,
                room_number,
                building,
                floor,
                category,
                description,
                x_coord,
                y_coord
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                number,
                normalized_building,
                floor,
                normalized_category,
                _clean_optional_text(description),
                x_coord,
                y_coord,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_room_by_id(
    room_id: int,
    db_path: str | Path = DB_NAME,
) -> sqlite3.Row | None:
    """Return a room by identifier, or ``None`` when it does not exist."""
    connection = get_connection(db_path)
    try:
        return connection.execute(
            "SELECT * FROM rooms WHERE id = ?",
            (room_id,),
        ).fetchone()
    finally:
        connection.close()


def get_all_rooms(db_path: str | Path = DB_NAME) -> list[sqlite3.Row]:
    """Return all rooms in building, floor, and room-number order."""
    connection = get_connection(db_path)
    try:
        return connection.execute("SELECT * FROM rooms" + _ROOM_ORDER_SQL).fetchall()
    finally:
        connection.close()


def update_room(
    room_id: int,
    room_name: str,
    room_number: str,
    building: str,
    floor: int,
    category: str,
    description: str | None = None,
    x_coord: float | None = None,
    y_coord: float | None = None,
    db_path: str | Path = DB_NAME,
) -> bool:
    """Update a validated room and report whether the record existed."""
    name, number, normalized_building, normalized_category = _validate_room_fields(
        room_name,
        room_number,
        building,
        floor,
        category,
    )

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            UPDATE rooms
            SET room_name = ?,
                room_number = ?,
                building = ?,
                floor = ?,
                category = ?,
                description = ?,
                x_coord = ?,
                y_coord = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                name,
                number,
                normalized_building,
                floor,
                normalized_category,
                _clean_optional_text(description),
                x_coord,
                y_coord,
                room_id,
            ),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_room(room_id: int, db_path: str | Path = DB_NAME) -> bool:
    """Delete a room and report whether a record was removed."""
    connection = get_connection(db_path)
    try:
        cursor = connection.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def count_rooms(db_path: str | Path = DB_NAME) -> int:
    """Return the total number of room records."""
    connection = get_connection(db_path)
    try:
        row = connection.execute("SELECT COUNT(*) FROM rooms").fetchone()
        return int(row[0])
    finally:
        connection.close()


def search_rooms(
    search_text: str,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Search room identity, location, category, and description fields."""
    normalized_search = search_text.strip()
    if not normalized_search:
        return get_all_rooms(db_path)

    search_pattern = f"%{normalized_search}%"
    connection = get_connection(db_path)
    try:
        return connection.execute(
            """
            SELECT * FROM rooms
            WHERE room_name LIKE ?
               OR room_number LIKE ?
               OR building LIKE ?
               OR category LIKE ?
               OR description LIKE ?
            """
            + _ROOM_ORDER_SQL,
            (search_pattern,) * 5,
        ).fetchall()
    finally:
        connection.close()


def get_rooms_by_category(
    category: str,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Return rooms matching a non-empty category without case sensitivity."""
    normalized_category = category.strip()
    if not normalized_category:
        return []

    connection = get_connection(db_path)
    try:
        return connection.execute(
            "SELECT * FROM rooms WHERE category = ? COLLATE NOCASE" + _ROOM_ORDER_SQL,
            (normalized_category,),
        ).fetchall()
    finally:
        connection.close()


def get_mappable_rooms(db_path: str | Path = DB_NAME) -> list[sqlite3.Row]:
    """Return rooms that have complete coordinates for the future 2D map."""
    connection = get_connection(db_path)
    try:
        return connection.execute(
            """
            SELECT * FROM rooms
            WHERE x_coord IS NOT NULL
              AND y_coord IS NOT NULL
            """
            + _ROOM_ORDER_SQL
        ).fetchall()
    finally:
        connection.close()
