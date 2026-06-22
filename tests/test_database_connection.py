"""Tests for the shared ECU robot SQLite connection helper."""

import sqlite3

from database import connection


def test_database_connection_module_can_be_imported() -> None:
    """Confirm the shared connection module remains importable."""
    assert connection is not None


def test_database_name_is_correct() -> None:
    """Confirm both applications use the expected shared database filename."""
    assert connection.DB_NAME == "ecu_robot.db"


def test_database_exists_returns_false_for_missing_path(tmp_path) -> None:
    """Confirm a missing temporary database is reported accurately."""
    missing_path = tmp_path / "missing_ecu_robot.db"

    assert connection.database_exists(missing_path) is False


def test_get_connection_creates_sqlite_connection_with_named_rows(tmp_path) -> None:
    """Confirm the helper opens a temporary database with named-row access."""
    database_path = tmp_path / "test_ecu_robot.db"

    database_connection = connection.get_connection(database_path)
    try:
        assert isinstance(database_connection, sqlite3.Connection)
        assert database_connection.row_factory is sqlite3.Row
        assert database_path.is_file()
    finally:
        database_connection.close()


def test_get_connection_enables_foreign_keys(tmp_path) -> None:
    """Confirm every shared connection enforces SQLite foreign keys."""
    database_path = tmp_path / "test_ecu_robot.db"

    database_connection = connection.get_connection(database_path)
    try:
        foreign_keys_enabled = database_connection.execute(
            "PRAGMA foreign_keys;"
        ).fetchone()[0]
    finally:
        database_connection.close()

    assert foreign_keys_enabled == 1
