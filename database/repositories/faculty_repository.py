"""Isolate faculty CRUD database logic from the Admin Dashboard UI layer."""

import sqlite3
from pathlib import Path

from database.connection import DB_NAME, get_connection


def _strip_optional_text(value: str | None) -> str | None:
    """Strip optional text while preserving ``None`` for nullable columns."""
    return value.strip() if value is not None else None


def create_faculty(
    name: str,
    description: str | None = None,
    building: str | None = None,
    dean_name: str | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    """Create a faculty and return its database identifier."""
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("Faculty name cannot be empty.")

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO faculties (name, description, building, dean_name)
            VALUES (?, ?, ?, ?)
            """,
            (
                normalized_name,
                _strip_optional_text(description),
                _strip_optional_text(building),
                _strip_optional_text(dean_name),
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_all_faculties(
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Return all faculties ordered alphabetically by name."""
    connection = get_connection(db_path)
    try:
        return connection.execute(
            "SELECT * FROM faculties ORDER BY name ASC"
        ).fetchall()
    finally:
        connection.close()


def get_faculty_by_id(
    faculty_id: int,
    db_path: str | Path = DB_NAME,
) -> sqlite3.Row | None:
    """Return a faculty by identifier, or ``None`` when it does not exist."""
    connection = get_connection(db_path)
    try:
        return connection.execute(
            "SELECT * FROM faculties WHERE id = ?",
            (faculty_id,),
        ).fetchone()
    finally:
        connection.close()


def update_faculty(
    faculty_id: int,
    name: str,
    description: str | None = None,
    building: str | None = None,
    dean_name: str | None = None,
    db_path: str | Path = DB_NAME,
) -> bool:
    """Update a faculty and report whether the record existed."""
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("Faculty name cannot be empty.")

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            UPDATE faculties
            SET name = ?,
                description = ?,
                building = ?,
                dean_name = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                normalized_name,
                _strip_optional_text(description),
                _strip_optional_text(building),
                _strip_optional_text(dean_name),
                faculty_id,
            ),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_faculty(
    faculty_id: int,
    db_path: str | Path = DB_NAME,
) -> bool:
    """Delete a faculty and report whether a record was removed."""
    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            "DELETE FROM faculties WHERE id = ?",
            (faculty_id,),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def count_faculties(db_path: str | Path = DB_NAME) -> int:
    """Return the total number of faculty records."""
    connection = get_connection(db_path)
    try:
        row = connection.execute("SELECT COUNT(*) FROM faculties").fetchone()
        return int(row[0])
    finally:
        connection.close()
