"""Tests for strict professor CSV import and export behavior."""

import csv

import pytest

from controllers.professor_csv_controller import (
    EXPORT_COLUMNS,
    NEW_ONLY_COLUMNS,
    OPTIONAL_ID_COLUMNS,
    export_professors_to_csv,
    import_professors_from_csv,
    validate_professors_csv_headers,
)
from database.init_db import initialize_database
from database.repositories.faculty_repository import create_faculty
from database.repositories.professor_repository import (
    create_professor,
    get_all_professors,
    get_professor_by_id,
)
from database.repositories.room_repository import create_room


def _create_temp_db(tmp_path):
    """Initialize and return an isolated database for one CSV test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    return database_path


def _create_dependencies(db_path) -> tuple[int, int]:
    """Create and return valid faculty and office-room identifiers."""
    faculty_id = create_faculty("Engineering", db_path=db_path)
    room_id = create_room(
        "Academic Office",
        "A101",
        "Engineering Building",
        1,
        "Office",
        db_path=db_path,
    )
    return faculty_id, room_id


def _write_csv(csv_path, headers, rows) -> None:
    """Write a temporary UTF-8 CSV fixture with explicit headers."""
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        writer.writerows(rows)


def _new_row(faculty_id: int, room_id: int) -> list:
    """Return one complete new-professor CSV row."""
    return [
        "Dr. Mona Hassan",
        "Professor",
        faculty_id,
        room_id,
        "mona@example.edu",
        "01000000000",
        "Sunday 10:00-12:00",
        "photos/mona.jpg",
        "Engineering professor.",
    ]


def test_validate_professors_csv_headers_accepts_new_only_format() -> None:
    """Confirm the documented new-professor format is accepted."""
    assert validate_professors_csv_headers(NEW_ONLY_COLUMNS) == NEW_ONLY_COLUMNS


def test_validate_professors_csv_headers_accepts_id_format() -> None:
    """Confirm the documented update/create format is accepted."""
    assert (
        validate_professors_csv_headers(OPTIONAL_ID_COLUMNS)
        == OPTIONAL_ID_COLUMNS
    )


def test_validate_professors_csv_headers_rejects_extra_columns() -> None:
    """Confirm undocumented columns are rejected rather than mapped."""
    with pytest.raises(ValueError, match="Expected exactly"):
        validate_professors_csv_headers([*NEW_ONLY_COLUMNS, "extra"])


def test_validate_professors_csv_headers_rejects_missing_required_columns() -> None:
    """Confirm headers without required fields are rejected."""
    with pytest.raises(ValueError, match="Expected exactly"):
        validate_professors_csv_headers(NEW_ONLY_COLUMNS[1:])


def test_import_professors_from_csv_creates_new_professors(tmp_path) -> None:
    """Confirm new-only CSV rows create professor records."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    csv_path = tmp_path / "professors.csv"
    _write_csv(csv_path, NEW_ONLY_COLUMNS, [_new_row(faculty_id, room_id)])

    summary = import_professors_from_csv(csv_path, db_path)

    assert summary["created"] == 1
    assert summary["updated"] == 0
    assert summary["skipped"] == 0
    assert summary["errors"] == []
    assert get_all_professors(db_path)[0]["full_name"] == "Dr. Mona Hassan"


def test_import_professors_from_csv_allows_empty_office_room_id(tmp_path) -> None:
    """Confirm office_room_id may be empty and is stored as null."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, _ = _create_dependencies(db_path)
    row = _new_row(faculty_id, "")
    csv_path = tmp_path / "professors.csv"
    _write_csv(csv_path, NEW_ONLY_COLUMNS, [row])

    summary = import_professors_from_csv(csv_path, db_path)
    professors = get_all_professors(db_path)

    assert summary == {"created": 1, "updated": 0, "skipped": 0, "errors": []}
    assert professors[0]["office_room_id"] is None


def test_import_professors_from_csv_updates_existing_professor_when_id_exists(
    tmp_path,
) -> None:
    """Confirm a valid existing ID updates its professor record."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    professor_id = create_professor(
        "Old Name",
        "Lecturer",
        faculty_id,
        room_id,
        db_path=db_path,
    )
    csv_path = tmp_path / "professors.csv"
    updated_row = _new_row(faculty_id, room_id)
    updated_row[0] = "Dr. Updated"
    _write_csv(csv_path, OPTIONAL_ID_COLUMNS, [[professor_id, *updated_row]])

    summary = import_professors_from_csv(csv_path, db_path)
    professor = get_professor_by_id(professor_id, db_path)

    assert summary["updated"] == 1
    assert professor is not None
    assert professor["full_name"] == "Dr. Updated"


def test_import_professors_from_csv_creates_when_id_missing(tmp_path) -> None:
    """Confirm a blank optional ID creates a new professor."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    csv_path = tmp_path / "professors.csv"
    _write_csv(
        csv_path,
        OPTIONAL_ID_COLUMNS,
        [["", *_new_row(faculty_id, room_id)]],
    )

    summary = import_professors_from_csv(csv_path, db_path)

    assert summary["created"] == 1
    assert len(get_all_professors(db_path)) == 1


def test_import_professors_from_csv_skips_empty_full_name_rows(tmp_path) -> None:
    """Confirm row-level full-name validation skips bad records."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    row = _new_row(faculty_id, room_id)
    row[0] = ""
    csv_path = tmp_path / "professors.csv"
    _write_csv(csv_path, NEW_ONLY_COLUMNS, [row])

    summary = import_professors_from_csv(csv_path, db_path)

    assert summary["skipped"] == 1
    assert "Row 2" in summary["errors"][0]
    assert get_all_professors(db_path) == []


def test_import_professors_from_csv_skips_invalid_faculty_id_rows(
    tmp_path,
) -> None:
    """Confirm non-integer faculty IDs are reported and skipped."""
    db_path = _create_temp_db(tmp_path)
    _, room_id = _create_dependencies(db_path)
    row = _new_row("not-an-id", room_id)
    csv_path = tmp_path / "professors.csv"
    _write_csv(csv_path, NEW_ONLY_COLUMNS, [row])

    summary = import_professors_from_csv(csv_path, db_path)

    assert summary["skipped"] == 1
    assert "faculty_id must be an integer" in summary["errors"][0]
    assert get_all_professors(db_path) == []


def test_import_professors_skips_missing_faculty_with_clear_error(tmp_path) -> None:
    """Confirm a well-formed but absent faculty ID gets actionable guidance."""
    db_path = _create_temp_db(tmp_path)
    _, room_id = _create_dependencies(db_path)
    csv_path = tmp_path / "professors.csv"
    _write_csv(csv_path, NEW_ONLY_COLUMNS, [_new_row(9999, room_id)])

    summary = import_professors_from_csv(csv_path, db_path)

    assert summary["skipped"] == 1
    assert summary["created"] == 0
    assert summary["errors"] == [
        "Row 2: faculty_id 9999 does not exist. "
        "Import faculties.csv first or use a valid faculty_id."
    ]
    assert "FOREIGN KEY constraint failed" not in summary["errors"][0]
    assert get_all_professors(db_path) == []


def test_import_professors_skips_missing_room_with_clear_error(tmp_path) -> None:
    """Confirm a well-formed but absent office room gets actionable guidance."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, _ = _create_dependencies(db_path)
    csv_path = tmp_path / "professors.csv"
    _write_csv(csv_path, NEW_ONLY_COLUMNS, [_new_row(faculty_id, 9999)])

    summary = import_professors_from_csv(csv_path, db_path)

    assert summary["skipped"] == 1
    assert summary["created"] == 0
    assert summary["errors"] == [
        "Row 2: office_room_id 9999 does not exist. "
        "Import rooms.csv first or leave office_room_id empty."
    ]
    assert "FOREIGN KEY constraint failed" not in summary["errors"][0]
    assert get_all_professors(db_path) == []


def test_export_professors_to_csv_writes_expected_columns_and_rows(
    tmp_path,
) -> None:
    """Confirm export uses exact documented columns and current rows."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    create_professor(
        "Dr. Mona Hassan",
        "Professor",
        faculty_id,
        room_id,
        db_path=db_path,
    )
    csv_path = tmp_path / "exported_professors.csv"

    exported_count = export_professors_to_csv(csv_path, db_path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.reader(csv_file))

    assert exported_count == 1
    assert rows[0] == EXPORT_COLUMNS
    assert rows[1][1] == "Dr. Mona Hassan"
