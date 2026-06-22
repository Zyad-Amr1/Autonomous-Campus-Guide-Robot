"""Tests for the initial ECU Guidance Robot database schema definitions."""

from database import schema


def test_schema_module_can_be_imported() -> None:
    """Confirm the schema module is available without database initialization."""
    assert schema is not None


def test_admin_table_schema() -> None:
    """Confirm the admin schema includes its required definition and fields."""
    assert hasattr(schema, "ADMIN_TABLE_SQL")
    assert "CREATE TABLE IF NOT EXISTS admin" in schema.ADMIN_TABLE_SQL

    for column_name in ("username", "password_hash", "full_name", "role"):
        assert column_name in schema.ADMIN_TABLE_SQL


def test_faculties_table_schema() -> None:
    """Confirm the faculties schema includes its required definition and fields."""
    assert hasattr(schema, "FACULTIES_TABLE_SQL")
    assert "CREATE TABLE IF NOT EXISTS faculties" in schema.FACULTIES_TABLE_SQL

    for column_name in ("name", "description", "building", "dean_name"):
        assert column_name in schema.FACULTIES_TABLE_SQL


def test_professors_table_schema() -> None:
    """Confirm the professors schema includes its current fields and relationship."""
    assert hasattr(schema, "PROFESSORS_TABLE_SQL")
    assert "CREATE TABLE IF NOT EXISTS professors" in schema.PROFESSORS_TABLE_SQL

    for column_name in (
        "full_name",
        "faculty_id",
        "email",
        "office_hours",
        "photo_path",
    ):
        assert column_name in schema.PROFESSORS_TABLE_SQL

    assert (
        "FOREIGN KEY (faculty_id) REFERENCES faculties(id)"
        in schema.PROFESSORS_TABLE_SQL
    )
    assert "FOREIGN KEY (office_room_id)" not in schema.PROFESSORS_TABLE_SQL
