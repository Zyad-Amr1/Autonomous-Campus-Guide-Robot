"""Tests for secure, repeatable initialization of the ECU robot database."""

import sqlite3
from pathlib import Path

from database import schema
from database.init_db import (
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    get_schema_statements,
    hash_password,
    initialize_database,
)


def test_hash_password_uses_pbkdf2_without_plain_text() -> None:
    """Confirm passwords use the expected PBKDF2 format and hide plain text."""
    password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)

    assert password_hash.startswith("pbkdf2_sha256$100000$")
    assert DEFAULT_ADMIN_PASSWORD not in password_hash


def test_schema_statements_follow_dependency_order() -> None:
    """Confirm all table statements are returned in safe creation order."""
    statements = get_schema_statements()

    assert len(statements) == 8
    assert statements == [
        schema.ADMIN_TABLE_SQL,
        schema.FACULTIES_TABLE_SQL,
        schema.ROOMS_TABLE_SQL,
        schema.PROFESSORS_TABLE_SQL,
        schema.COURSES_TABLE_SQL,
        schema.EVENTS_TABLE_SQL,
        schema.FAQ_TABLE_SQL,
        schema.LOGS_TABLE_SQL,
    ]


def test_initialize_database_creates_schema_and_default_admin(tmp_path: Path) -> None:
    """Confirm initialization creates every table and a hashed admin account."""
    database_path = tmp_path / "test_ecu_robot.db"

    result_path = initialize_database(database_path)

    assert result_path == database_path
    assert database_path.exists()

    connection = sqlite3.connect(database_path)
    try:
        table_rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        admin_row = connection.execute(
            "SELECT username, password_hash FROM admin WHERE username = ?",
            (DEFAULT_ADMIN_USERNAME,),
        ).fetchone()
    finally:
        connection.close()

    table_names = {row[0] for row in table_rows}
    expected_tables = {
        "admin",
        "faculties",
        "rooms",
        "professors",
        "courses",
        "events",
        "faq",
        "logs",
    }

    assert expected_tables.issubset(table_names)
    assert admin_row is not None
    assert admin_row[0] == DEFAULT_ADMIN_USERNAME
    assert admin_row[1] != DEFAULT_ADMIN_PASSWORD


def test_initialize_database_does_not_duplicate_default_admin(tmp_path: Path) -> None:
    """Confirm repeated initialization remains safe and idempotent."""
    database_path = tmp_path / "test_ecu_robot.db"

    initialize_database(database_path)
    initialize_database(database_path)

    connection = sqlite3.connect(database_path)
    try:
        admin_count = connection.execute(
            "SELECT COUNT(*) FROM admin WHERE username = ?",
            (DEFAULT_ADMIN_USERNAME,),
        ).fetchone()[0]
    finally:
        connection.close()

    assert admin_count == 1
