"""Tests for strict event CSV import and export behavior."""

import csv
import pytest

from controllers.event_csv_controller import (
    EXPORT_COLUMNS, NEW_ONLY_COLUMNS, OPTIONAL_ID_COLUMNS,
    export_events_to_csv, import_events_from_csv, validate_events_csv_headers,
)
from database.init_db import initialize_database
from database.repositories.event_repository import create_event, get_all_events, get_event_by_id


def _db(tmp_path):
    path = tmp_path / "test.db"; initialize_database(path); return path


def _write(path, headers, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file); writer.writerow(headers); writer.writerows(rows)


def _row(): return ["Open Day", "Welcome", "Campus", "2026-07-01", "2026-07-01", "10:00", "14:00"]


def test_validate_events_csv_headers_accepts_new_only_format(): assert validate_events_csv_headers(NEW_ONLY_COLUMNS) == NEW_ONLY_COLUMNS
def test_validate_events_csv_headers_accepts_id_format(): assert validate_events_csv_headers(OPTIONAL_ID_COLUMNS) == OPTIONAL_ID_COLUMNS
def test_validate_events_csv_headers_rejects_extra_columns():
    with pytest.raises(ValueError, match="Expected exactly"): validate_events_csv_headers([*NEW_ONLY_COLUMNS, "extra"])
def test_validate_events_csv_headers_rejects_missing_required_columns():
    with pytest.raises(ValueError, match="Expected exactly"): validate_events_csv_headers(NEW_ONLY_COLUMNS[1:])


def test_import_events_from_csv_creates_new_rows(tmp_path):
    db = _db(tmp_path); path = tmp_path / "events.csv"; _write(path, NEW_ONLY_COLUMNS, [_row()])
    assert import_events_from_csv(path, db)["created"] == 1; assert get_all_events(db)[0]["title"] == "Open Day"


def test_import_events_from_csv_updates_existing_row(tmp_path):
    db = _db(tmp_path); event_id = create_event("Old", "", "", "2026-07-01", "2026-07-01", db_path=db)
    row = _row(); row[0] = "Updated"; path = tmp_path / "events.csv"; _write(path, OPTIONAL_ID_COLUMNS, [[event_id, *row]])
    assert import_events_from_csv(path, db)["updated"] == 1; assert get_event_by_id(event_id, db)["title"] == "Updated"


def test_import_events_from_csv_creates_when_id_missing(tmp_path):
    db = _db(tmp_path); path = tmp_path / "events.csv"; _write(path, OPTIONAL_ID_COLUMNS, [["", *_row()]])
    assert import_events_from_csv(path, db)["created"] == 1


def test_import_events_from_csv_skips_invalid_required_rows(tmp_path):
    db = _db(tmp_path); row = _row(); row[0] = ""; path = tmp_path / "events.csv"; _write(path, NEW_ONLY_COLUMNS, [row])
    summary = import_events_from_csv(path, db); assert summary["skipped"] == 1; assert get_all_events(db) == []


def test_import_events_from_csv_skips_invalid_id_rows(tmp_path):
    db = _db(tmp_path); path = tmp_path / "events.csv"; _write(path, OPTIONAL_ID_COLUMNS, [["bad", *_row()]])
    summary = import_events_from_csv(path, db); assert summary["skipped"] == 1; assert "integer" in summary["errors"][0]


def test_export_events_to_csv_writes_expected_columns_and_rows(tmp_path):
    db = _db(tmp_path); create_event("Open Day", "", "Campus", "2026-07-01", "2026-07-01", db_path=db)
    path = tmp_path / "export.csv"; assert export_events_to_csv(path, db) == 1
    with path.open("r", encoding="utf-8-sig", newline="") as file: rows = list(csv.reader(file))
    assert rows[0] == EXPORT_COLUMNS; assert rows[1][1] == "Open Day"
