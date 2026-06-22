"""Isolate visitor interaction logging and analytics from the UI layer."""

import sqlite3
from pathlib import Path

from database.connection import DB_NAME, get_connection

_LOG_SELECT_SQL = """
SELECT
    logs.*,
    faq.question AS matched_question,
    faq.answer AS matched_answer
FROM logs
LEFT JOIN faq ON logs.matched_faq_id = faq.id
"""

_LOG_ORDER_SQL = " ORDER BY logs.created_at DESC, logs.id DESC"


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


def _validate_limit(limit: int) -> None:
    """Ensure analytics and history limits are positive integers."""
    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        raise ValueError("Limit must be a positive integer.")


def create_log(
    query_text: str,
    matched_faq_id: int | None = None,
    response_text: str | None = None,
    screen_name: str | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    """Create a visitor interaction log and return its identifier."""
    normalized_query = _clean_required_text(query_text, "Query text")

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO logs (
                query_text,
                matched_faq_id,
                response_text,
                screen_name
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                normalized_query,
                matched_faq_id,
                _clean_optional_text(response_text),
                _clean_optional_text(screen_name),
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_log_by_id(
    log_id: int,
    db_path: str | Path = DB_NAME,
) -> sqlite3.Row | None:
    """Return one log with its matched FAQ context when available."""
    connection = get_connection(db_path)
    try:
        return connection.execute(
            _LOG_SELECT_SQL + " WHERE logs.id = ?",
            (log_id,),
        ).fetchone()
    finally:
        connection.close()


def get_recent_logs(
    limit: int = 50,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Return a validated number of newest interaction logs."""
    _validate_limit(limit)

    connection = get_connection(db_path)
    try:
        return connection.execute(
            _LOG_SELECT_SQL + _LOG_ORDER_SQL + " LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        connection.close()


def count_logs(db_path: str | Path = DB_NAME) -> int:
    """Return the total number of visitor interaction logs."""
    connection = get_connection(db_path)
    try:
        row = connection.execute("SELECT COUNT(*) FROM logs").fetchone()
        return int(row[0])
    finally:
        connection.close()


def search_logs(
    search_text: str,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Search log content, screen names, and matched FAQ information."""
    normalized_search = search_text.strip()
    if not normalized_search:
        return get_recent_logs(db_path=db_path)

    search_pattern = f"%{normalized_search}%"
    connection = get_connection(db_path)
    try:
        return connection.execute(
            _LOG_SELECT_SQL
            + """
            WHERE logs.query_text LIKE ?
               OR logs.response_text LIKE ?
               OR logs.screen_name LIKE ?
               OR faq.question LIKE ?
               OR faq.answer LIKE ?
            """
            + _LOG_ORDER_SQL,
            (search_pattern,) * 5,
        ).fetchall()
    finally:
        connection.close()


def get_most_frequent_queries(
    limit: int = 10,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Return grouped query frequencies for future analytics charts."""
    _validate_limit(limit)

    connection = get_connection(db_path)
    try:
        return connection.execute(
            """
            SELECT query_text, COUNT(*) AS query_count
            FROM logs
            GROUP BY query_text
            ORDER BY query_count DESC, query_text ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        connection.close()


def get_logs_by_screen(
    screen_name: str,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Return logs matching a non-empty screen name without case sensitivity."""
    normalized_screen = screen_name.strip()
    if not normalized_screen:
        return []

    connection = get_connection(db_path)
    try:
        return connection.execute(
            _LOG_SELECT_SQL
            + " WHERE logs.screen_name = ? COLLATE NOCASE"
            + _LOG_ORDER_SQL,
            (normalized_screen,),
        ).fetchall()
    finally:
        connection.close()


def get_unmatched_questions(
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Return unanswered interactions that may require new FAQ content."""
    connection = get_connection(db_path)
    try:
        return connection.execute(
            _LOG_SELECT_SQL
            + " WHERE logs.matched_faq_id IS NULL"
            + _LOG_ORDER_SQL
        ).fetchall()
    finally:
        connection.close()
