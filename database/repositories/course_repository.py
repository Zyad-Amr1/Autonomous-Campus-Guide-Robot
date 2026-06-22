"""Isolate course and schedule database logic from the system's UI layers."""

import sqlite3
from datetime import date
from pathlib import Path

from database.connection import DB_NAME, get_connection

_COURSE_SELECT_SQL = """
SELECT
    courses.*,
    faculties.name AS faculty_name,
    professors.full_name AS professor_name,
    rooms.room_name AS room_name,
    rooms.room_number AS room_number,
    rooms.building AS building,
    rooms.floor AS floor
FROM courses
LEFT JOIN faculties ON courses.faculty_id = faculties.id
LEFT JOIN professors ON courses.professor_id = professors.id
LEFT JOIN rooms ON courses.room_id = rooms.id
"""

_COURSE_ORDER_SQL = (
    " ORDER BY courses.schedule_day ASC, courses.start_time ASC, "
    "courses.course_code ASC"
)


def _clean_required_text(value: str, field_name: str) -> str:
    """Normalize required text or raise a clear validation error."""
    cleaned_value = value.strip()
    if not cleaned_value:
        raise ValueError(f"{field_name} cannot be empty.")
    return cleaned_value


def _clean_optional_text(value: str | None) -> str | None:
    """Normalize optional text and convert blank values to ``None``."""
    if value is None:
        return None
    cleaned_value = value.strip()
    return cleaned_value or None


def _clean_course_text_fields(
    course_code: str,
    course_name: str,
    schedule_day: str,
    start_time: str,
    end_time: str,
) -> tuple[str, str, str, str, str]:
    """Validate and normalize all required course text fields."""
    return (
        _clean_required_text(course_code, "Course code"),
        _clean_required_text(course_name, "Course name"),
        _clean_required_text(schedule_day, "Schedule day"),
        _clean_required_text(start_time, "Start time"),
        _clean_required_text(end_time, "End time"),
    )


def create_course(
    course_code: str,
    course_name: str,
    faculty_id: int,
    professor_id: int | None,
    room_id: int | None,
    schedule_day: str,
    start_time: str,
    end_time: str,
    semester: str | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    """Create a validated course schedule and return its identifier."""
    code, name, day, starts_at, ends_at = _clean_course_text_fields(
        course_code,
        course_name,
        schedule_day,
        start_time,
        end_time,
    )

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO courses (
                course_code,
                course_name,
                faculty_id,
                professor_id,
                room_id,
                schedule_day,
                start_time,
                end_time,
                semester
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                code,
                name,
                faculty_id,
                professor_id,
                room_id,
                day,
                starts_at,
                ends_at,
                _clean_optional_text(semester),
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_course_by_id(
    course_id: int,
    db_path: str | Path = DB_NAME,
) -> sqlite3.Row | None:
    """Return one course with its joined faculty, professor, and room data."""
    connection = get_connection(db_path)
    try:
        return connection.execute(
            _COURSE_SELECT_SQL + " WHERE courses.id = ?",
            (course_id,),
        ).fetchone()
    finally:
        connection.close()


def get_all_courses(db_path: str | Path = DB_NAME) -> list[sqlite3.Row]:
    """Return all joined course schedules in stable display order."""
    connection = get_connection(db_path)
    try:
        return connection.execute(_COURSE_SELECT_SQL + _COURSE_ORDER_SQL).fetchall()
    finally:
        connection.close()


def update_course(
    course_id: int,
    course_code: str,
    course_name: str,
    faculty_id: int,
    professor_id: int | None,
    room_id: int | None,
    schedule_day: str,
    start_time: str,
    end_time: str,
    semester: str | None = None,
    db_path: str | Path = DB_NAME,
) -> bool:
    """Update a course schedule and report whether the record existed."""
    code, name, day, starts_at, ends_at = _clean_course_text_fields(
        course_code,
        course_name,
        schedule_day,
        start_time,
        end_time,
    )

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            UPDATE courses
            SET course_code = ?,
                course_name = ?,
                faculty_id = ?,
                professor_id = ?,
                room_id = ?,
                schedule_day = ?,
                start_time = ?,
                end_time = ?,
                semester = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                code,
                name,
                faculty_id,
                professor_id,
                room_id,
                day,
                starts_at,
                ends_at,
                _clean_optional_text(semester),
                course_id,
            ),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_course(course_id: int, db_path: str | Path = DB_NAME) -> bool:
    """Delete a course and report whether a record was removed."""
    connection = get_connection(db_path)
    try:
        cursor = connection.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def count_courses(db_path: str | Path = DB_NAME) -> int:
    """Return the total number of course records."""
    connection = get_connection(db_path)
    try:
        row = connection.execute("SELECT COUNT(*) FROM courses").fetchone()
        return int(row[0])
    finally:
        connection.close()


def search_courses(
    search_text: str,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Search course schedules and their joined academic/location details."""
    normalized_search = search_text.strip()
    if not normalized_search:
        return get_all_courses(db_path)

    search_pattern = f"%{normalized_search}%"
    connection = get_connection(db_path)
    try:
        return connection.execute(
            _COURSE_SELECT_SQL
            + """
            WHERE courses.course_code LIKE ?
               OR courses.course_name LIKE ?
               OR courses.schedule_day LIKE ?
               OR courses.semester LIKE ?
               OR faculties.name LIKE ?
               OR professors.full_name LIKE ?
               OR rooms.room_name LIKE ?
               OR rooms.room_number LIKE ?
               OR rooms.building LIKE ?
            """
            + _COURSE_ORDER_SQL,
            (search_pattern,) * 9,
        ).fetchall()
    finally:
        connection.close()


def get_courses_by_day(
    schedule_day: str,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Return joined courses for a non-empty day without case sensitivity."""
    normalized_day = schedule_day.strip()
    if not normalized_day:
        return []

    connection = get_connection(db_path)
    try:
        return connection.execute(
            _COURSE_SELECT_SQL
            + """
            WHERE courses.schedule_day = ? COLLATE NOCASE
            ORDER BY courses.start_time ASC, courses.course_code ASC
            """,
            (normalized_day,),
        ).fetchall()
    finally:
        connection.close()


def get_today_courses(db_path: str | Path = DB_NAME) -> list[sqlite3.Row]:
    """Return courses scheduled for today's day name."""
    today_name = date.today().strftime("%A")
    return get_courses_by_day(today_name, db_path)
