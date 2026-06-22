"""Isolate FAQ data logic for the UI and future public assistant answers."""

import sqlite3
from pathlib import Path

from database.connection import DB_NAME, get_connection

_FAQ_ORDER_SQL = " ORDER BY category ASC, question ASC"


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


def create_faq(
    question: str,
    answer: str,
    keywords: str | None = None,
    category: str | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    """Create a validated FAQ record and return its identifier."""
    normalized_question = _clean_required_text(question, "FAQ question")
    normalized_answer = _clean_required_text(answer, "FAQ answer")

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO faq (question, answer, keywords, category)
            VALUES (?, ?, ?, ?)
            """,
            (
                normalized_question,
                normalized_answer,
                _clean_optional_text(keywords),
                _clean_optional_text(category),
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_faq_by_id(
    faq_id: int,
    db_path: str | Path = DB_NAME,
) -> sqlite3.Row | None:
    """Return an FAQ by identifier, or ``None`` when it does not exist."""
    connection = get_connection(db_path)
    try:
        return connection.execute(
            "SELECT * FROM faq WHERE id = ?",
            (faq_id,),
        ).fetchone()
    finally:
        connection.close()


def get_all_faqs(db_path: str | Path = DB_NAME) -> list[sqlite3.Row]:
    """Return all FAQs in category and question order."""
    connection = get_connection(db_path)
    try:
        return connection.execute("SELECT * FROM faq" + _FAQ_ORDER_SQL).fetchall()
    finally:
        connection.close()


def update_faq(
    faq_id: int,
    question: str,
    answer: str,
    keywords: str | None = None,
    category: str | None = None,
    db_path: str | Path = DB_NAME,
) -> bool:
    """Update a validated FAQ and report whether the record existed."""
    normalized_question = _clean_required_text(question, "FAQ question")
    normalized_answer = _clean_required_text(answer, "FAQ answer")

    connection = get_connection(db_path)
    try:
        cursor = connection.execute(
            """
            UPDATE faq
            SET question = ?,
                answer = ?,
                keywords = ?,
                category = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                normalized_question,
                normalized_answer,
                _clean_optional_text(keywords),
                _clean_optional_text(category),
                faq_id,
            ),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_faq(faq_id: int, db_path: str | Path = DB_NAME) -> bool:
    """Delete an FAQ and report whether a record was removed."""
    connection = get_connection(db_path)
    try:
        cursor = connection.execute("DELETE FROM faq WHERE id = ?", (faq_id,))
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def count_faqs(db_path: str | Path = DB_NAME) -> int:
    """Return the total number of FAQ records."""
    connection = get_connection(db_path)
    try:
        row = connection.execute("SELECT COUNT(*) FROM faq").fetchone()
        return int(row[0])
    finally:
        connection.close()


def search_faqs(
    search_text: str,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Search FAQ questions, answers, keywords, and categories."""
    normalized_search = search_text.strip()
    if not normalized_search:
        return get_all_faqs(db_path)

    search_pattern = f"%{normalized_search}%"
    connection = get_connection(db_path)
    try:
        return connection.execute(
            """
            SELECT * FROM faq
            WHERE question LIKE ?
               OR answer LIKE ?
               OR keywords LIKE ?
               OR category LIKE ?
            """
            + _FAQ_ORDER_SQL,
            (search_pattern,) * 4,
        ).fetchall()
    finally:
        connection.close()


def get_faqs_by_category(
    category: str,
    db_path: str | Path = DB_NAME,
) -> list[sqlite3.Row]:
    """Return FAQs matching a non-empty category without case sensitivity."""
    normalized_category = category.strip()
    if not normalized_category:
        return []

    connection = get_connection(db_path)
    try:
        return connection.execute(
            """
            SELECT * FROM faq
            WHERE category = ? COLLATE NOCASE
            ORDER BY question ASC
            """,
            (normalized_category,),
        ).fetchall()
    finally:
        connection.close()


def find_best_faq_match(
    query_text: str,
    db_path: str | Path = DB_NAME,
) -> sqlite3.Row | None:
    """Return the highest-scoring deterministic FAQ match for a user query."""
    query_words = query_text.lower().split()
    if not query_words:
        return None

    best_faq: sqlite3.Row | None = None
    best_score = 0

    for faq in get_all_faqs(db_path):
        question = faq["question"].lower()
        answer = faq["answer"].lower()
        keywords = (faq["keywords"] or "").lower()
        category = (faq["category"] or "").lower()

        score = 0
        for word in query_words:
            if word in question:
                score += 3
            if word in keywords:
                score += 3
            if word in category:
                score += 1
            if word in answer:
                score += 1

        if score > best_score:
            best_score = score
            best_faq = faq

    return best_faq if best_score > 0 else None
