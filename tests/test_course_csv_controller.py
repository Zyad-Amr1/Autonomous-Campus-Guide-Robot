"""Tests for strict course CSV import and export behavior."""

import csv
import pytest

from controllers.course_csv_controller import (
    EXPORT_COLUMNS, NEW_ONLY_COLUMNS, OPTIONAL_ID_COLUMNS,
    export_courses_to_csv, import_courses_from_csv, validate_courses_csv_headers,
)
from database.init_db import initialize_database
from database.repositories.course_repository import create_course, get_all_courses, get_course_by_id
from database.repositories.faculty_repository import create_faculty


def _db(tmp_path):
    path = tmp_path / "test.db"; initialize_database(path); return path


def _write(path, headers, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file); writer.writerow(headers); writer.writerows(rows)


def _row(faculty_id):
    return ["CS101", "Programming", faculty_id, "", "", "Monday", "09:00", "10:30", "Fall"]


def test_validate_courses_csv_headers_accepts_new_only_format():
    assert validate_courses_csv_headers(NEW_ONLY_COLUMNS) == NEW_ONLY_COLUMNS


def test_validate_courses_csv_headers_accepts_id_format():
    assert validate_courses_csv_headers(OPTIONAL_ID_COLUMNS) == OPTIONAL_ID_COLUMNS


def test_validate_courses_csv_headers_rejects_extra_columns():
    with pytest.raises(ValueError, match="Expected exactly"):
        validate_courses_csv_headers([*NEW_ONLY_COLUMNS, "extra"])


def test_validate_courses_csv_headers_rejects_missing_required_columns():
    with pytest.raises(ValueError, match="Expected exactly"):
        validate_courses_csv_headers(NEW_ONLY_COLUMNS[1:])


def test_import_courses_from_csv_creates_new_rows(tmp_path):
    db = _db(tmp_path); faculty = create_faculty("Engineering", db_path=db); path = tmp_path / "courses.csv"
    _write(path, NEW_ONLY_COLUMNS, [_row(faculty)])
    summary = import_courses_from_csv(path, db)
    assert summary["created"] == 1; assert get_all_courses(db)[0]["course_code"] == "CS101"


def test_import_courses_from_csv_updates_existing_row(tmp_path):
    db = _db(tmp_path); faculty = create_faculty("Engineering", db_path=db)
    course_id = create_course("CS100", "Old", faculty, None, None, "Monday", "08:00", "09:00", db_path=db)
    row = _row(faculty); row[1] = "Updated"; path = tmp_path / "courses.csv"; _write(path, OPTIONAL_ID_COLUMNS, [[course_id, *row]])
    summary = import_courses_from_csv(path, db)
    assert summary["updated"] == 1; assert get_course_by_id(course_id, db)["course_name"] == "Updated"


def test_import_courses_from_csv_creates_when_id_missing(tmp_path):
    db = _db(tmp_path); faculty = create_faculty("Engineering", db_path=db); path = tmp_path / "courses.csv"
    _write(path, OPTIONAL_ID_COLUMNS, [["", *_row(faculty)]])
    assert import_courses_from_csv(path, db)["created"] == 1


def test_import_courses_from_csv_skips_invalid_required_rows(tmp_path):
    db = _db(tmp_path); faculty = create_faculty("Engineering", db_path=db); row = _row(faculty); row[0] = ""
    path = tmp_path / "courses.csv"; _write(path, NEW_ONLY_COLUMNS, [row]); summary = import_courses_from_csv(path, db)
    assert summary["skipped"] == 1; assert get_all_courses(db) == []


def test_import_courses_from_csv_skips_invalid_numeric_rows(tmp_path):
    db = _db(tmp_path); row = _row("bad-id"); path = tmp_path / "courses.csv"; _write(path, NEW_ONLY_COLUMNS, [row])
    summary = import_courses_from_csv(path, db)
    assert summary["skipped"] == 1; assert "faculty_id" in summary["errors"][0]


def test_export_courses_to_csv_writes_expected_columns_and_rows(tmp_path):
    db = _db(tmp_path); faculty = create_faculty("Engineering", db_path=db)
    create_course("CS101", "Programming", faculty, None, None, "Monday", "09:00", "10:30", db_path=db)
    path = tmp_path / "export.csv"; assert export_courses_to_csv(path, db) == 1
    with path.open("r", encoding="utf-8-sig", newline="") as file: rows = list(csv.reader(file))
    assert rows[0] == EXPORT_COLUMNS; assert rows[1][1] == "CS101"
