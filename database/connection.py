"""Shared SQLite connections for the Admin Panel and Public Assistant."""

import sqlite3
from pathlib import Path

DB_NAME = "ecu_robot.db"


def get_connection(db_path: str | Path = DB_NAME) -> sqlite3.Connection:
    """Open a named-row connection with relational integrity enabled.

    Foreign-key enforcement protects relationships between ECU records, while
    ``sqlite3.Row`` lets both applications access query results by column name.
    """
    database_path = Path(db_path)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def database_exists(db_path: str | Path = DB_NAME) -> bool:
    """Return whether the shared SQLite database file exists."""
    return Path(db_path).is_file()
