"""Searchable university context for the public chatbot."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from database.connection import DB_NAME, get_connection


_WORD_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
_STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "available",
    "can",
    "do",
    "does",
    "find",
    "for",
    "how",
    "i",
    "in",
    "is",
    "me",
    "of",
    "on",
    "tell",
    "the",
    "there",
    "to",
    "what",
    "where",
    "who",
    "عن",
    "في",
    "ما",
    "من",
    "هي",
    "هو",
}
_SOURCE_ALIASES = {
    "faculties": {"faculty", "faculties", "college", "colleges", "كلية", "الكليات", "كليات"},
    "professors": {"professor", "professors", "doctor", "doctors", "staff", "دكتور", "الدكاترة", "دكاترة", "استاذ", "أساتذة"},
    "rooms": {"room", "rooms", "hall", "halls", "القاعة", "القاعات", "قاعه", "قاعة", "قاعات"},
    "courses": {"course", "courses", "schedule", "class", "classes", "الجدول", "الجداول", "جدول", "جداول", "مقرر", "مقررات"},
    "events": {"event", "events", "news", "activity", "activities", "الفعاليات", "فعالية", "فعاليات", "اخبار", "أخبار"},
    "faq": {"faq", "question", "questions", "help", "السؤال", "الاسئلة", "الأسئلة", "سؤال", "اسئلة", "أسئلة"},
}
_SOURCE_PRIORITY = {
    "faq": 0,
    "rooms": 1,
    "faculties": 2,
    "professors": 3,
    "courses": 4,
    "events": 5,
}


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _clean_parts(*parts: Any) -> str:
    return " ".join(str(part).strip() for part in parts if part not in (None, ""))


def _tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw_token in _WORD_RE.findall(text):
        token = raw_token.strip("_?؟.,،:;!()[]{}").casefold()
        if not token:
            continue
        if token in _STOPWORDS:
            continue
        tokens.add(token)
        if token.startswith("ال") and len(token) > 2:
            tokens.add(token[2:])
    return tokens


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _safe_rows(
    connection: sqlite3.Connection,
    table_name: str,
    query: str,
) -> list[sqlite3.Row]:
    if not _table_exists(connection, table_name):
        return []
    try:
        return connection.execute(query).fetchall()
    except sqlite3.Error:
        return []


def get_university_context(db_path: str | Path = DB_NAME) -> dict[str, list[dict[str, Any]]]:
    """Load searchable public university context from SQLite tables."""
    connection = get_connection(db_path)
    try:
        faculties = [
            _row_to_dict(row)
            for row in _safe_rows(
                connection,
                "faculties",
                """
                SELECT id, name, description, building, dean_name
                FROM faculties
                ORDER BY name
                """,
            )
        ]
        rooms = [
            _row_to_dict(row)
            for row in _safe_rows(
                connection,
                "rooms",
                """
                SELECT id, room_name, room_number, building, floor, category, description
                FROM rooms
                ORDER BY building, floor, room_number
                """,
            )
        ]
        professors = [
            _row_to_dict(row)
            for row in _safe_rows(
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
            )
        ]
        courses = [
            _row_to_dict(row)
            for row in _safe_rows(
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
            )
        ]
        events = [
            _row_to_dict(row)
            for row in _safe_rows(
                connection,
                "events",
                """
                SELECT id, title, description, location, start_date, end_date, start_time, end_time
                FROM events
                ORDER BY start_date, start_time, title
                """,
            )
        ]
        faq = [
            _row_to_dict(row)
            for row in _safe_rows(
                connection,
                "faq",
                """
                SELECT id, question, answer, keywords, category
                FROM faq
                ORDER BY category, question
                """,
            )
        ]
        return {
            "faculties": faculties,
            "professors": professors,
            "rooms": rooms,
            "courses": courses,
            "events": events,
            "faq": faq,
        }
    finally:
        connection.close()


def _context_items(context: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for faculty in context["faculties"]:
        title = str(faculty.get("name") or "Faculty")
        snippet = _clean_parts(
            title,
            faculty.get("description"),
            f"Building: {faculty.get('building')}" if faculty.get("building") else None,
            f"Dean: {faculty.get('dean_name')}" if faculty.get("dean_name") else None,
        )
        items.append({"source_type": "faculties", "id": faculty.get("id"), "title": title, "snippet": snippet})

    for professor in context["professors"]:
        title = str(professor.get("full_name") or "Professor")
        snippet = _clean_parts(
            professor.get("title"),
            title,
            f"Faculty: {professor.get('faculty_name')}" if professor.get("faculty_name") else None,
            f"Office: {professor.get('office_room_name')} {professor.get('office_room_number')} {professor.get('office_building')}".strip()
            if professor.get("office_room_name") or professor.get("office_room_number") or professor.get("office_building")
            else None,
            f"Email: {professor.get('email')}" if professor.get("email") else None,
            f"Office hours: {professor.get('office_hours')}" if professor.get("office_hours") else None,
            professor.get("bio"),
        )
        items.append({"source_type": "professors", "id": professor.get("id"), "title": title, "snippet": snippet})

    for room in context["rooms"]:
        title = str(room.get("room_name") or room.get("room_number") or "Room")
        snippet = _clean_parts(
            title,
            room.get("room_number"),
            f"Building: {room.get('building')}" if room.get("building") else None,
            f"Floor: {room.get('floor')}" if room.get("floor") is not None else None,
            f"Category: {room.get('category')}" if room.get("category") else None,
            room.get("description"),
        )
        items.append({"source_type": "rooms", "id": room.get("id"), "title": title, "snippet": snippet})

    for course in context["courses"]:
        title = _clean_parts(course.get("course_code"), course.get("course_name")) or "Course"
        snippet = _clean_parts(
            title,
            f"Faculty: {course.get('faculty_name')}" if course.get("faculty_name") else None,
            f"Professor: {course.get('professor_name')}" if course.get("professor_name") else None,
            f"Room: {course.get('room_name')} {course.get('room_number')} {course.get('building')}".strip()
            if course.get("room_name") or course.get("room_number") or course.get("building")
            else None,
            f"Schedule: {course.get('schedule_day')} {course.get('start_time')}-{course.get('end_time')}",
            f"Semester: {course.get('semester')}" if course.get("semester") else None,
        )
        items.append({"source_type": "courses", "id": course.get("id"), "title": title, "snippet": snippet})

    for event in context["events"]:
        title = str(event.get("title") or "Event")
        snippet = _clean_parts(
            title,
            event.get("description"),
            f"Location: {event.get('location')}" if event.get("location") else None,
            f"Date: {event.get('start_date')} to {event.get('end_date')}",
            f"Time: {event.get('start_time')}-{event.get('end_time')}" if event.get("start_time") else None,
        )
        items.append({"source_type": "events", "id": event.get("id"), "title": title, "snippet": snippet})

    for faq in context["faq"]:
        title = str(faq.get("question") or "FAQ")
        snippet = _clean_parts(title, faq.get("answer"), faq.get("keywords"), faq.get("category"))
        items.append({"source_type": "faq", "id": faq.get("id"), "title": title, "snippet": snippet})

    for item in items:
        item["search_text"] = _clean_parts(item["source_type"], item["title"], item["snippet"])
    return items


def search_university_context(
    question: str,
    db_path: str | Path = DB_NAME,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Return best matching context snippets for a visitor question."""
    normalized_question = question.strip()
    if not normalized_question:
        return []

    question_tokens = _tokens(normalized_question)
    context = get_university_context(db_path)
    scored_items: list[dict[str, Any]] = []
    for item in _context_items(context):
        search_text = str(item["search_text"])
        text_tokens = _tokens(search_text)
        overlap = question_tokens & text_tokens
        substring_bonus = 3 if normalized_question.casefold() in search_text.casefold() else 0
        score = len(overlap) * 4 + substring_bonus
        source_aliases = _SOURCE_ALIASES.get(str(item["source_type"]), set())
        if question_tokens & source_aliases:
            score += 2
        if score <= 0:
            continue
        result = dict(item)
        result["score"] = score
        scored_items.append(result)

    scored_items.sort(
        key=lambda item: (
            -int(item["score"]),
            _SOURCE_PRIORITY.get(str(item["source_type"]), 99),
            str(item["title"]),
        )
    )
    return scored_items[: max(1, int(limit))]
