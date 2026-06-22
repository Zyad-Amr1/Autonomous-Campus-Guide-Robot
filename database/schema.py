"""SQLite schema statements for the shared ECU Guidance Robot database."""

ADMIN_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

FACULTIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS faculties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    building TEXT,
    dean_name TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

PROFESSORS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS professors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    title TEXT,
    faculty_id INTEGER NOT NULL,
    office_room_id INTEGER,
    email TEXT UNIQUE,
    phone TEXT,
    office_hours TEXT,
    photo_path TEXT,
    bio TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (faculty_id) REFERENCES faculties(id) ON DELETE CASCADE
);
"""
