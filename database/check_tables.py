"""Verify the SQLite database structure after database initialization."""

import sqlite3
from pathlib import Path

from database.connection import DB_NAME


def get_table_names(db_path: str | Path = DB_NAME) -> list[str]:
    """Return alphabetically sorted user-created table names."""
    database_path = Path(db_path)
    if not database_path.is_file():
        raise FileNotFoundError(
            "Database file not found. Run: python -m database.init_db"
        )

    connection = sqlite3.connect(database_path)
    try:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
    finally:
        connection.close()

    return [row[0] for row in rows]


def main() -> None:
    """Print the user-created tables or explain how to initialize the database."""
    try:
        table_names = get_table_names()
    except FileNotFoundError as error:
        print(error)
        return

    print("Database tables found:")
    for table_name in table_names:
        print(f"- {table_name}")


if __name__ == "__main__":
    main()
