"""Tests for strict faculty CSV import and export behavior."""

import csv

import pytest

from controllers.faculty_csv_controller import (
    EXPORT_COLUMNS,
    import_faculties_from_csv,
    export_faculties_to_csv,
    validate_faculties_csv_headers,
)
from database.init_db import initialize_database
from database.repositories.faculty_repository import (
    create_faculty,
    get_all_faculties,
    get_faculty_by_id,
)


def _create_temp_db(tmp_path):
    """Initialize and return an isolated database for one CSV test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    return database_path


def _write_csv(csv_path, headers, rows) -> None:
    """Write a temporary UTF-8 CSV fixture using explicit headers."""
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        writer.writerows(rows)


def test_validate_faculties_csv_headers_accepts_new_only_format() -> None:
    """Confirm the documented new-faculty format is accepted."""
    headers = ["name", "description", "building", "dean_name"]

    assert validate_faculties_csv_headers(headers) == headers


def test_validate_faculties_csv_headers_accepts_id_format() -> None:
    """Confirm the documented update/create format is accepted."""
    headers = ["id", "name", "description", "building", "dean_name"]

    assert validate_faculties_csv_headers(headers) == headers


def test_validate_faculties_csv_headers_rejects_extra_columns() -> None:
    """Confirm undocumented columns are rejected rather than mapped."""
    with pytest.raises(ValueError, match="Expected exactly"):
        validate_faculties_csv_headers(
            ["name", "description", "building", "dean_name", "extra"]
        )


def test_validate_faculties_csv_headers_rejects_missing_name() -> None:
    """Confirm headers without the required name column are rejected."""
    with pytest.raises(ValueError, match="Expected exactly"):
        validate_faculties_csv_headers(["description", "building", "dean_name"])


def test_import_faculties_from_csv_creates_new_faculties(tmp_path) -> None:
    """Confirm new-only CSV rows create faculty records."""
    db_path = _create_temp_db(tmp_path)
    csv_path = tmp_path / "faculties.csv"
    _write_csv(
        csv_path,
        ["name", "description", "building", "dean_name"],
        [
            ["Engineering", "Engineering programs", "Building A", "Dean One"],
            ["Business", "Business programs", "Building B", "Dean Two"],
        ],
    )

    summary = import_faculties_from_csv(csv_path, db_path)

    assert summary["created"] == 2
    assert summary["updated"] == 0
    assert len(get_all_faculties(db_path)) == 2


def test_import_faculties_from_csv_updates_existing_faculty_when_id_exists(
    tmp_path,
) -> None:
    """Confirm a valid existing ID updates its faculty record."""
    db_path = _create_temp_db(tmp_path)
    faculty_id = create_faculty("Engineering", db_path=db_path)
    csv_path = tmp_path / "faculties.csv"
    _write_csv(
        csv_path,
        ["id", "name", "description", "building", "dean_name"],
        [[faculty_id, "Applied Engineering", "Updated", "Building B", "Dean"]],
    )

    summary = import_faculties_from_csv(csv_path, db_path)
    faculty = get_faculty_by_id(faculty_id, db_path)

    assert summary["updated"] == 1
    assert faculty is not None
    assert faculty["name"] == "Applied Engineering"
    assert faculty["building"] == "Building B"


def test_import_faculties_from_csv_creates_when_id_missing(tmp_path) -> None:
    """Confirm a blank optional ID creates a new auto-numbered record."""
    db_path = _create_temp_db(tmp_path)
    csv_path = tmp_path / "faculties.csv"
    _write_csv(
        csv_path,
        ["id", "name", "description", "building", "dean_name"],
        [["", "Engineering", "Programs", "Building A", "Dean"]],
    )

    summary = import_faculties_from_csv(csv_path, db_path)

    assert summary["created"] == 1
    assert len(get_all_faculties(db_path)) == 1


def test_import_faculties_from_csv_skips_empty_name_rows(tmp_path) -> None:
    """Confirm row-level name validation reports and skips bad records."""
    db_path = _create_temp_db(tmp_path)
    csv_path = tmp_path / "faculties.csv"
    _write_csv(
        csv_path,
        ["name", "description", "building", "dean_name"],
        [["", "Programs", "Building A", "Dean"]],
    )

    summary = import_faculties_from_csv(csv_path, db_path)

    assert summary["skipped"] == 1
    assert len(summary["errors"]) == 1
    assert "Row 2" in summary["errors"][0]


def test_export_faculties_to_csv_writes_expected_columns_and_rows(tmp_path) -> None:
    """Confirm export uses the exact documented columns and current rows."""
    db_path = _create_temp_db(tmp_path)
    create_faculty("Engineering", db_path=db_path)
    create_faculty("Business", db_path=db_path)
    csv_path = tmp_path / "exported_faculties.csv"

    exported_count = export_faculties_to_csv(csv_path, db_path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.reader(csv_file))

    assert exported_count == 2
    assert rows[0] == EXPORT_COLUMNS
    assert len(rows) == 3
