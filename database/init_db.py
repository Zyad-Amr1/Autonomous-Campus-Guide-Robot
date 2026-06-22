"""Initialize the shared SQLite database for the Admin Panel and Public Assistant."""

import binascii
import hashlib
import os
import sqlite3
from pathlib import Path

from database.connection import DB_NAME
from database.schema import (
    ADMIN_TABLE_SQL,
    COURSES_TABLE_SQL,
    EVENTS_TABLE_SQL,
    FACULTIES_TABLE_SQL,
    FAQ_TABLE_SQL,
    LOGS_TABLE_SQL,
    PROFESSORS_TABLE_SQL,
    ROOMS_TABLE_SQL,
)

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_FULL_NAME = "System Administrator"
DEFAULT_ADMIN_ROLE = "super_admin"


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Return a salted PBKDF2-SHA256 representation of a password."""
    password_salt = salt if salt is not None else os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        password_salt,
        100000,
    )
    salt_hex = binascii.hexlify(password_salt).decode("ascii")
    hash_hex = binascii.hexlify(password_hash).decode("ascii")
    return f"pbkdf2_sha256$100000${salt_hex}${hash_hex}"


def get_schema_statements() -> list[str]:
    """Return table definitions in foreign-key dependency order."""
    return [
        ADMIN_TABLE_SQL,
        FACULTIES_TABLE_SQL,
        ROOMS_TABLE_SQL,
        PROFESSORS_TABLE_SQL,
        COURSES_TABLE_SQL,
        EVENTS_TABLE_SQL,
        FAQ_TABLE_SQL,
        LOGS_TABLE_SQL,
    ]


def initialize_database(db_path: str | Path = DB_NAME) -> Path:
    """Create the shared schema and seed the default administrator safely."""
    database_path = Path(db_path)
    connection = sqlite3.connect(database_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON;")

        for statement in get_schema_statements():
            connection.execute(statement)

        connection.execute(
            """
            INSERT OR IGNORE INTO admin (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                DEFAULT_ADMIN_USERNAME,
                hash_password(DEFAULT_ADMIN_PASSWORD),
                DEFAULT_ADMIN_FULL_NAME,
                DEFAULT_ADMIN_ROLE,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    return database_path


def main() -> None:
    """Initialize the default database and display its initial credentials."""
    database_path = initialize_database()
    print(f"Database initialized successfully: {database_path}")
    print(f"Default admin username: {DEFAULT_ADMIN_USERNAME}")
    print(f"Default admin password: {DEFAULT_ADMIN_PASSWORD}")


if __name__ == "__main__":
    main()
