"""Isolate university event database operations from the system's UI layers."""

import sqlite3
from datetime import date
from pathlib import Path

from database.connection import DB_NAME, get_connection

_EVENT_ORDER_SQL = " ORDER BY start_date ASC, title ASC"


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


def _validate_date_text(value: str, field_name: str) -> str:
    """Return a stripped ISO date or raise a clear validation error."""
    cleaned_value = value.strip()
    try:
        date.fromisoformat(cleaned_value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.") from error
    return cleaned_value


def _validate_event_values(
    title: str,
    start_date: str,
    end_date: str,
) -> tuple[str, str, str]:
    """Normalize required event values and validate their date range."""
    normalized_title = _clean_required_text(title, "Event title")
    normalized_start = _validate_date_text(start_date, "Start date")
    normalized_end = _validate_date_text(end_date, "End date")

    if date.fromisoformat(normalized_end) < date.fromisoformat(normalized_start):
        raise ValueError("End date cannot be before start date.")

    return normalized_title, normalized_start, normalized_end


def create_event(
    title: str,
    description: str | None,
    location: str | None,
    start_date: str,
    end_date: str,
    start_time: str | None = None,
    end_time: str | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    """Create a validated university event and return its identifier."""
    normalized_title, normalized_start, normalized_end = _validate_event_values(
        title,
        start_date,
        end_date,
    )

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO events (
                title,
                description,
                location,
                start_date,
                end_date,
                start_time,
                end_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized_title,
                _clean_optional_text(description),
                _clean_optional_text(location),
                normalized_start,
                normalized_end,
                _clean_optional_text(start_time),
                _clean_optional_text(end_time),
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_event_by_id(
    event_id: int,
    db_path: str | Path = DB_NAME,
) -> sqlite3.Row | None:
    """Return an event by identifier, or ``None`` when it does not exist."""
    connection = get_connection(db_path)
    try:
        return connection.execute(
            "SELECT * FROM events WHERE id = ?",
            (event_id,),
        ).fetchone()
    finally:
        connection.close()


def get_all_events(db_path: str | Path = DB_NAME) -> list[sqlite3.Row]:
    """Return all events in start-date and title order."""
    connection = get_connection(db_path)
    try:
        return connection.execute("SELECT * FROM events" + _EVENT_ORDER_SQL).fetchall()
    finally:
        connection.close()


def update_event(
    event_id: int,
    title: str,
    description: str | None,
    location: str | None,
    start_date: str,
    end_date: str,
    start_time: str | None = None,
    end_time: str | None = None,
    db_path: str | Path = DB_NAME,
) -> bool:
    """Update a validated event and report whether the record existed."""
    normalized_title, normalized_start, normalized_end = _validate_event_values(
        title,
        start_date,
        end_date,
    )

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            UPDATE events
            SET title = ?,
                description = ?,
                location = ?,
                start_date = ?,
                end_date = ?,
                start_time = ?,
                end_time = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                normalized_title,
                _clean_optional_text(description),
                _clean_optional_text(location),
                normalized_start,
                normalized_end,
                _clean_optional_text(start_time),
                _clean_optional_text(end_time),
                event_id,
            ),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_event(event_id: int, db_path: str | Path = DB_NAME) -> bool:
    """Delete an event and report whether a record was removed."""
    connection = get_connection(db_path)
    try:
        cursor = connection.execute("DELETE FROM events WHERE id = ?", (event_id,))
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def count_events(db_path: str | Path = DB_NAME) -> int:
    """Return the total number of university event records."""
    connection = get_connection(db_path)
    try:
        row = connection.execute("SELECT COUNT(*) FROM events").fetchone()
        return int(row[0])
    finally:
        connection.close()


def search_events(
    search_text: str,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Search event text and date fields using partial matching."""
    normalized_search = search_text.strip()
    if not normalized_search:
        return get_all_events(db_path)

    search_pattern = f"%{normalized_search}%"
    connection = get_connection(db_path)
    try:
        return connection.execute(
            """
            SELECT * FROM events
            WHERE title LIKE ?
               OR description LIKE ?
               OR location LIKE ?
               OR start_date LIKE ?
               OR end_date LIKE ?
            """
            + _EVENT_ORDER_SQL,
            (search_pattern,) * 5,
        ).fetchall()
    finally:
        connection.close()


def get_active_events(
    current_date: str | None = None,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Return events active on an inclusive validated date."""
    active_date = (
        date.today().isoformat()
        if current_date is None
        else _validate_date_text(current_date, "Current date")
    )

    connection = get_connection(db_path)
    try:
        return connection.execute(
            """
            SELECT * FROM events
            WHERE ? BETWEEN start_date AND end_date
            """
            + _EVENT_ORDER_SQL,
            (active_date,),
        ).fetchall()
    finally:
        connection.close()
