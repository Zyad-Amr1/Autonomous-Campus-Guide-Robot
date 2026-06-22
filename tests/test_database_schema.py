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
    assert (
        "FOREIGN KEY (office_room_id) REFERENCES rooms(id)"
        in schema.PROFESSORS_TABLE_SQL
    )


def test_rooms_table_schema() -> None:
    """Confirm the rooms schema includes navigation fields and uniqueness rules."""
    assert hasattr(schema, "ROOMS_TABLE_SQL")
    assert "CREATE TABLE IF NOT EXISTS rooms" in schema.ROOMS_TABLE_SQL

    for column_name in (
        "room_name",
        "room_number",
        "building",
        "floor",
        "category",
        "x_coord",
        "y_coord",
    ):
        assert column_name in schema.ROOMS_TABLE_SQL

    assert "UNIQUE(building, floor, room_number)" in schema.ROOMS_TABLE_SQL


def test_courses_table_schema() -> None:
    """Confirm the courses schema includes scheduling fields and relationships."""
    assert hasattr(schema, "COURSES_TABLE_SQL")
    assert "CREATE TABLE IF NOT EXISTS courses" in schema.COURSES_TABLE_SQL

    for column_name in (
        "course_code",
        "course_name",
        "faculty_id",
        "professor_id",
        "room_id",
        "schedule_day",
        "start_time",
        "end_time",
    ):
        assert column_name in schema.COURSES_TABLE_SQL

    expected_foreign_keys = (
        "FOREIGN KEY (faculty_id) REFERENCES faculties(id)",
        "FOREIGN KEY (professor_id) REFERENCES professors(id)",
        "FOREIGN KEY (room_id) REFERENCES rooms(id)",
    )

    for foreign_key in expected_foreign_keys:
        assert foreign_key in schema.COURSES_TABLE_SQL


def test_events_table_schema() -> None:
    """Confirm the events schema includes date, time, and location details."""
    assert hasattr(schema, "EVENTS_TABLE_SQL")
    assert "CREATE TABLE IF NOT EXISTS events" in schema.EVENTS_TABLE_SQL

    for column_name in (
        "title",
        "description",
        "location",
        "start_date",
        "end_date",
        "start_time",
        "end_time",
    ):
        assert column_name in schema.EVENTS_TABLE_SQL


def test_faq_table_schema() -> None:
    """Confirm the FAQ schema includes searchable guidance information."""
    assert hasattr(schema, "FAQ_TABLE_SQL")
    assert "CREATE TABLE IF NOT EXISTS faq" in schema.FAQ_TABLE_SQL

    for column_name in ("question", "answer", "keywords", "category"):
        assert column_name in schema.FAQ_TABLE_SQL


def test_logs_table_schema() -> None:
    """Confirm the logs schema captures assistant interactions and FAQ matches."""
    assert hasattr(schema, "LOGS_TABLE_SQL")
    assert "CREATE TABLE IF NOT EXISTS logs" in schema.LOGS_TABLE_SQL

    for column_name in (
        "query_text",
        "matched_faq_id",
        "response_text",
        "screen_name",
    ):
        assert column_name in schema.LOGS_TABLE_SQL

    assert (
        "FOREIGN KEY (matched_faq_id) REFERENCES faq(id)"
        in schema.LOGS_TABLE_SQL
    )
