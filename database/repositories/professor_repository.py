"""Isolate professor database operations from the system's UI layers."""

import sqlite3
from pathlib import Path

from database.connection import DB_NAME, get_connection

_PROFESSOR_SELECT_SQL = """
SELECT
    professors.*,
    faculties.name AS faculty_name,
    CASE
        WHEN rooms.id IS NULL THEN NULL
        ELSE rooms.room_name || ' - ' || rooms.room_number
    END AS office_room_name
FROM professors
LEFT JOIN faculties ON professors.faculty_id = faculties.id
LEFT JOIN rooms ON professors.office_room_id = rooms.id
"""


def _clean_optional_text(value: str | None) -> str | None:
    """Normalize optional text and convert blank values to ``None``."""
    if value is None:
        return None
    cleaned_value = value.strip()
    return cleaned_value or None


def create_professor(
    full_name: str,
    title: str | None,
    faculty_id: int,
    office_room_id: int | None = None,
    email: str | None = None,
    phone: str | None = None,
    office_hours: str | None = None,
    photo_path: str | None = None,
    bio: str | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    """Create a professor and return the new database identifier."""
    normalized_name = full_name.strip()
    if not normalized_name:
        raise ValueError("Professor full name cannot be empty.")

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO professors (
                full_name,
                title,
                faculty_id,
                office_room_id,
                email,
                phone,
                office_hours,
                photo_path,
                bio
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized_name,
                _clean_optional_text(title),
                faculty_id,
                office_room_id,
                _clean_optional_text(email),
                _clean_optional_text(phone),
                _clean_optional_text(office_hours),
                _clean_optional_text(photo_path),
                _clean_optional_text(bio),
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_professor_by_id(
    professor_id: int,
    db_path: str | Path = DB_NAME,
) -> sqlite3.Row | None:
    """Return one professor with faculty and office-room display details."""
    connection = get_connection(db_path)
    try:
        return connection.execute(
            _PROFESSOR_SELECT_SQL + " WHERE professors.id = ?",
            (professor_id,),
        ).fetchone()
    finally:
        connection.close()


def get_all_professors(
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Return all professors alphabetically with their joined display details."""
    connection = get_connection(db_path)
    try:
        return connection.execute(
            _PROFESSOR_SELECT_SQL + " ORDER BY professors.full_name ASC"
        ).fetchall()
    finally:
        connection.close()


def update_professor(
    professor_id: int,
    full_name: str,
    title: str | None,
    faculty_id: int,
    office_room_id: int | None = None,
    email: str | None = None,
    phone: str | None = None,
    office_hours: str | None = None,
    photo_path: str | None = None,
    bio: str | None = None,
    db_path: str | Path = DB_NAME,
) -> bool:
    """Update a professor and report whether the record existed."""
    normalized_name = full_name.strip()
    if not normalized_name:
        raise ValueError("Professor full name cannot be empty.")

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            UPDATE professors
            SET full_name = ?,
                title = ?,
                faculty_id = ?,
                office_room_id = ?,
                email = ?,
                phone = ?,
                office_hours = ?,
                photo_path = ?,
                bio = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                normalized_name,
                _clean_optional_text(title),
                faculty_id,
                office_room_id,
                _clean_optional_text(email),
                _clean_optional_text(phone),
                _clean_optional_text(office_hours),
                _clean_optional_text(photo_path),
                _clean_optional_text(bio),
                professor_id,
            ),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_professor(
    professor_id: int,
    db_path: str | Path = DB_NAME,
) -> bool:
    """Delete a professor and report whether a record was removed."""
    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            "DELETE FROM professors WHERE id = ?",
            (professor_id,),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def count_professors(db_path: str | Path = DB_NAME) -> int:
    """Return the total number of professor records."""
    connection = get_connection(db_path)
    try:
        row = connection.execute("SELECT COUNT(*) FROM professors").fetchone()
        return int(row[0])
    finally:
        connection.close()


def search_professors(
    search_text: str,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Search professor and related faculty information by partial text."""
    normalized_search = search_text.strip()
    if not normalized_search:
        return get_all_professors(db_path)

    search_pattern = f"%{normalized_search}%"
    connection = get_connection(db_path)
    try:
        return connection.execute(
            _PROFESSOR_SELECT_SQL
            + """
            WHERE professors.full_name LIKE ?
               OR professors.title LIKE ?
               OR professors.email LIKE ?
               OR faculties.name LIKE ?
               OR professors.office_hours LIKE ?
            ORDER BY professors.full_name ASC
            """,
            (search_pattern,) * 5,
        ).fetchall()
    finally:
        connection.close()
