"""Fuzzy database retrieval for trusted local chatbot context."""

import sqlite3
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

SEARCH_THRESHOLD = 45

_TABLE_CONFIG = {
    "faculties": {
        "fields": ("name", "description", "building", "dean_name"),
        "title": ("name",),
        "labels": ("faculty", "faculties"),
    },
    "professors": {
        "fields": ("full_name", "title", "email", "phone", "office_hours", "bio"),
        "title": ("full_name", "title"),
        "labels": ("professor", "professors", "faculty"),
    },
    "rooms": {
        "fields": (
            "room_name",
            "room_number",
            "building",
            "floor",
            "category",
            "description",
        ),
        "title": ("room_name", "room_number"),
        "labels": ("room", "rooms", "location", "locations"),
    },
    "courses": {
        "fields": (
            "course_code",
            "course_name",
            "schedule_day",
            "start_time",
            "end_time",
            "semester",
        ),
        "title": ("course_code", "course_name"),
        "labels": ("course", "courses", "class", "classes"),
    },
    "events": {
        "fields": (
            "title",
            "description",
            "location",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
        ),
        "title": ("title",),
        "labels": ("event", "events"),
    },
    "faq": {
        "fields": ("question", "answer", "keywords", "category"),
        "title": ("question",),
        "labels": ("faq", "question", "questions", "answer", "answers"),
    },
}


def retrieve_from_database(
    query: str,
    db_path: str | Path,
    limit: int = 5,
) -> list[dict]:
    """Return top fuzzy matches from trusted SQLite chatbot tables."""
    normalized_query = query.strip()
    if not normalized_query or limit <= 0:
        return []

    results: list[dict] = []
    connection = sqlite3.connect(Path(db_path))
    connection.row_factory = sqlite3.Row
    try:
        for table_name, config in _TABLE_CONFIG.items():
            if not _table_exists(connection, table_name):
                continue

            columns = _get_table_columns(connection, table_name)
            search_fields = [
                field for field in config["fields"] if field in columns
            ]
            if not search_fields:
                continue

            rows = connection.execute(f'SELECT * FROM "{table_name}"').fetchall()
            for row in rows:
                raw = dict(row)
                title = _join_values(raw, config["title"]) or table_name.title()
                content = _join_values(raw, search_fields)
                searchable_text = " ".join(
                    [table_name, *config["labels"], title, content]
                )
                score = _score_match(normalized_query, searchable_text)

                if score >= SEARCH_THRESHOLD:
                    results.append(
                        {
                            "source": "database",
                            "source_table": table_name,
                            "title": title,
                            "content": content,
                            "score": score,
                            "raw": raw,
                        }
                    )
    finally:
        connection.close()

    results.sort(key=lambda result: result["score"], reverse=True)
    return results[:limit]


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def _get_table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    rows = connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    return {row["name"] for row in rows}


def _join_values(raw: dict[str, Any], fields: tuple[str, ...] | list[str]) -> str:
    values = []
    for field in fields:
        value = raw.get(field)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            values.append(text)
    return " | ".join(values)


def _score_match(query: str, searchable_text: str) -> int:
    return int(
        max(
            fuzz.partial_ratio(query, searchable_text),
            fuzz.token_set_ratio(query, searchable_text),
            fuzz.WRatio(query, searchable_text),
        )
    )
