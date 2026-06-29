"""Convert university SQLite rows into searchable knowledge chunks."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from database.connection import DB_NAME, get_connection


_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
_ENGLISH_RE = re.compile(r"[A-Za-z]")
_WORD_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _safe_rows(connection: sqlite3.Connection, table_name: str, query: str) -> list[dict[str, Any]]:
    if not _table_exists(connection, table_name):
        return []
    try:
        return [_row_to_dict(row) for row in connection.execute(query).fetchall()]
    except sqlite3.Error:
        return []


def _clean_parts(*parts: Any) -> str:
    return " ".join(str(part).strip() for part in parts if part not in (None, ""))


def detect_chunk_language(text: str) -> str:
    """Classify chunk text as English, Arabic, or mixed."""
    has_arabic = _ARABIC_RE.search(text) is not None
    has_english = _ENGLISH_RE.search(text) is not None
    if has_arabic and has_english:
        return "mixed"
    if has_arabic:
        return "ar"
    return "en"


def _keywords(*parts: Any) -> list[str]:
    text = _clean_parts(*parts).casefold()
    seen: set[str] = set()
    keywords: list[str] = []
    for token in _WORD_RE.findall(text):
        token = token.strip("_?؟.,،:;!()[]{}")
        if len(token) < 2 or token in seen:
            continue
        seen.add(token)
        keywords.append(token)
    return keywords


def _chunk(source: str, row_id: Any, title: str, content: str, *keyword_parts: Any) -> dict[str, Any]:
    full_text = _clean_parts(title, content, *keyword_parts)
    return {
        "id": f"{source}:{row_id}",
        "source": source,
        "title": title,
        "content": content,
        "keywords": _keywords(full_text),
        "language": detect_chunk_language(full_text),
    }


def build_knowledge_chunks(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    """Read SQLite university data and return RAG knowledge chunks."""
    connection = get_connection(db_path)
    try:
        rows_by_source = {
            "faculties": _safe_rows(
                connection,
                "faculties",
                """
                SELECT id, name, description, building, dean_name
                FROM faculties
                ORDER BY name
                """,
            ),
            "rooms": _safe_rows(
                connection,
                "rooms",
                """
                SELECT id, room_name, room_number, building, floor, category, description
                FROM rooms
                ORDER BY building, floor, room_number
                """,
            ),
            "professors": _safe_rows(
                connection,
                "professors",
                """
                SELECT
                    professors.id,
                    professors.full_name,
                    professors.title,
                    professors.email,
                    professors.phone,
                    professors.office_hours,
                    professors.bio,
                    faculties.name AS faculty_name,
                    rooms.room_name AS office_room_name,
                    rooms.room_number AS office_room_number,
                    rooms.building AS office_building
                FROM professors
                LEFT JOIN faculties ON professors.faculty_id = faculties.id
                LEFT JOIN rooms ON professors.office_room_id = rooms.id
                ORDER BY professors.full_name
                """,
            ),
            "courses": _safe_rows(
                connection,
                "courses",
                """
                SELECT
                    courses.id,
                    courses.course_code,
                    courses.course_name,
                    courses.schedule_day,
                    courses.start_time,
                    courses.end_time,
                    courses.semester,
                    faculties.name AS faculty_name,
                    professors.full_name AS professor_name,
                    rooms.room_name AS room_name,
                    rooms.room_number AS room_number,
                    rooms.building AS building
                FROM courses
                LEFT JOIN faculties ON courses.faculty_id = faculties.id
                LEFT JOIN professors ON courses.professor_id = professors.id
                LEFT JOIN rooms ON courses.room_id = rooms.id
                ORDER BY courses.course_code, courses.schedule_day, courses.start_time
                """,
            ),
            "events": _safe_rows(
                connection,
                "events",
                """
                SELECT id, title, description, location, start_date, end_date, start_time, end_time
                FROM events
                ORDER BY start_date, start_time, title
                """,
            ),
            "faq": _safe_rows(
                connection,
                "faq",
                """
                SELECT id, question, answer, keywords, category
                FROM faq
                ORDER BY category, question
                """,
            ),
        }
    finally:
        connection.close()

    chunks: list[dict[str, Any]] = []
    for row in rows_by_source["faculties"]:
        title = str(row.get("name") or "Faculty")
        content = _clean_parts(
            row.get("description"),
            f"Building: {row.get('building')}" if row.get("building") else None,
            f"Dean: {row.get('dean_name')}" if row.get("dean_name") else None,
        )
        chunks.append(_chunk("faculties", row.get("id"), title, content, row.get("building"), row.get("dean_name")))

    for row in rows_by_source["professors"]:
        title = str(row.get("full_name") or "Professor")
        content = _clean_parts(
            row.get("title"),
            f"Faculty: {row.get('faculty_name')}" if row.get("faculty_name") else None,
            f"Office: {row.get('office_room_name')} {row.get('office_room_number')} {row.get('office_building')}".strip()
            if row.get("office_room_name") or row.get("office_room_number") or row.get("office_building")
            else None,
            f"Email: {row.get('email')}" if row.get("email") else None,
            f"Phone: {row.get('phone')}" if row.get("phone") else None,
            f"Office hours: {row.get('office_hours')}" if row.get("office_hours") else None,
            row.get("bio"),
        )
        chunks.append(_chunk("professors", row.get("id"), title, content, row.get("faculty_name")))

    for row in rows_by_source["rooms"]:
        title = str(row.get("room_name") or row.get("room_number") or "Room")
        content = _clean_parts(
            f"Room number: {row.get('room_number')}" if row.get("room_number") else None,
            f"Building: {row.get('building')}" if row.get("building") else None,
            f"Floor: {row.get('floor')}" if row.get("floor") is not None else None,
            f"Category: {row.get('category')}" if row.get("category") else None,
            row.get("description"),
        )
        chunks.append(_chunk("rooms", row.get("id"), title, content, row.get("room_number"), row.get("building"), row.get("category")))

    for row in rows_by_source["courses"]:
        title = _clean_parts(row.get("course_code"), row.get("course_name")) or "Course"
        content = _clean_parts(
            f"Faculty: {row.get('faculty_name')}" if row.get("faculty_name") else None,
            f"Professor: {row.get('professor_name')}" if row.get("professor_name") else None,
            f"Room: {row.get('room_name')} {row.get('room_number')} {row.get('building')}".strip()
            if row.get("room_name") or row.get("room_number") or row.get("building")
            else None,
            f"Schedule: {row.get('schedule_day')} {row.get('start_time')}-{row.get('end_time')}",
            f"Semester: {row.get('semester')}" if row.get("semester") else None,
        )
        chunks.append(_chunk("courses", row.get("id"), title, content, row.get("course_code"), row.get("course_name")))

    for row in rows_by_source["events"]:
        title = str(row.get("title") or "Event")
        content = _clean_parts(
            row.get("description"),
            f"Location: {row.get('location')}" if row.get("location") else None,
            f"Date: {row.get('start_date')} to {row.get('end_date')}",
            f"Time: {row.get('start_time')}-{row.get('end_time')}" if row.get("start_time") else None,
        )
        chunks.append(_chunk("events", row.get("id"), title, content, row.get("location")))

    for row in rows_by_source["faq"]:
        title = str(row.get("question") or "FAQ")
        content = _clean_parts(row.get("answer"), f"Category: {row.get('category')}" if row.get("category") else None)
        chunks.append(_chunk("faq", row.get("id"), title, content, row.get("keywords"), row.get("category")))

    return chunks

