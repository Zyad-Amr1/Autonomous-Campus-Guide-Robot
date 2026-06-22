"""Isolate admin authentication database logic from the user-interface layer."""

import hashlib
import hmac
import sqlite3
from pathlib import Path

from database.connection import DB_NAME, get_connection


def get_admin_by_username(
    username: str,
    db_path: str | Path = DB_NAME,
) -> sqlite3.Row | None:
    """Return the admin matching ``username``, or ``None`` when absent."""
    connection = get_connection(db_path)
    try:
        return connection.execute(
            "SELECT * FROM admin WHERE username = ?",
            (username,),
        ).fetchone()
    finally:
        connection.close()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a PBKDF2-SHA256 hash without raising errors."""
    try:
        algorithm, iterations_text, salt_hex, hash_hex = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_text)
        if iterations <= 0:
            return False

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
    except (AttributeError, TypeError, ValueError, OverflowError):
        return False

    return hmac.compare_digest(calculated_hash, expected_hash)


def authenticate_admin(
    username: str,
    password: str,
    db_path: str | Path = DB_NAME,
) -> dict | None:
    """Return safe admin profile data when the supplied credentials are valid."""
    admin = get_admin_by_username(username, db_path)
    if admin is None or not verify_password(password, admin["password_hash"]):
        return None

    return {
        "id": admin["id"],
        "username": admin["username"],
        "full_name": admin["full_name"],
        "role": admin["role"],
    }
