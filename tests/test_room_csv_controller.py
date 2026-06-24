"""Tests for strict room CSV import and export behavior."""

import csv

import pytest

from controllers.room_csv_controller import (
    EXPORT_COLUMNS,
    NEW_ONLY_COLUMNS,
    OPTIONAL_ID_COLUMNS,
    export_rooms_to_csv,
    import_rooms_from_csv,
    validate_rooms_csv_headers,
)
from database.init_db import initialize_database
from database.repositories.room_repository import (
    create_room,
    delete_room,
    get_all_rooms,
    get_room_by_id,
)


def _create_temp_db(tmp_path):
    """Initialize and return an isolated database for one CSV test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    return database_path


def _write_csv(csv_path, headers, rows) -> None:
    """Write a temporary UTF-8 CSV fixture with explicit headers."""
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        writer.writerows(rows)


def _new_row() -> list:
    """Return one complete new-room CSV row."""
    return [
        "Lecture Hall",
        "A101",
        "Main Building",
        "1",
        "Classroom",
        "Teaching room",
        "10.5",
        "20.25",
    ]


def test_validate_rooms_csv_headers_accepts_new_only_format() -> None:
    """Confirm the documented new-room format is accepted."""
    assert validate_rooms_csv_headers(NEW_ONLY_COLUMNS) == NEW_ONLY_COLUMNS


def test_validate_rooms_csv_headers_accepts_id_format() -> None:
    """Confirm the documented update/create format is accepted."""
    assert validate_rooms_csv_headers(OPTIONAL_ID_COLUMNS) == OPTIONAL_ID_COLUMNS


def test_validate_rooms_csv_headers_rejects_extra_columns() -> None:
    """Confirm undocumented columns are rejected rather than mapped."""
    with pytest.raises(ValueError, match="Expected exactly"):
        validate_rooms_csv_headers([*NEW_ONLY_COLUMNS, "extra"])


def test_validate_rooms_csv_headers_rejects_missing_required_columns() -> None:
    """Confirm headers without required fields are rejected."""
    with pytest.raises(ValueError, match="Expected exactly"):
        validate_rooms_csv_headers(NEW_ONLY_COLUMNS[1:])


def test_import_rooms_from_csv_creates_new_rooms(tmp_path) -> None:
    """Confirm new-only CSV rows create room records."""
    db_path = _create_temp_db(tmp_path)
    csv_path = tmp_path / "rooms.csv"
    _write_csv(csv_path, NEW_ONLY_COLUMNS, [_new_row()])

    summary = import_rooms_from_csv(csv_path, db_path)

    assert summary["created"] == 1
    assert summary["updated"] == 0
    assert get_all_rooms(db_path)[0]["room_name"] == "Lecture Hall"


def test_import_rooms_from_csv_updates_existing_room_when_id_exists(
    tmp_path,
) -> None:
    """Confirm a valid existing ID updates its room record."""
    db_path = _create_temp_db(tmp_path)
    room_id = create_room(
        "Old Room",
        "A100",
        "Old Building",
        0,
        "Office",
        db_path=db_path,
    )
    row = _new_row()
    row[0] = "Updated Hall"
    csv_path = tmp_path / "rooms.csv"
    _write_csv(csv_path, OPTIONAL_ID_COLUMNS, [[room_id, *row]])

    summary = import_rooms_from_csv(csv_path, db_path)
    room = get_room_by_id(room_id, db_path)

    assert summary["updated"] == 1
    assert room is not None
    assert room["room_name"] == "Updated Hall"
    assert room["building"] == "Main Building"


def test_import_rooms_from_csv_creates_when_id_missing(tmp_path) -> None:
    """Confirm a blank optional ID creates a new room."""
    db_path = _create_temp_db(tmp_path)
    csv_path = tmp_path / "rooms.csv"
    _write_csv(csv_path, OPTIONAL_ID_COLUMNS, [["", *_new_row()]])

    summary = import_rooms_from_csv(csv_path, db_path)

    assert summary["created"] == 1
    assert len(get_all_rooms(db_path)) == 1


def test_import_rooms_from_csv_preserves_explicit_id(tmp_path) -> None:
    """Confirm a new room keeps the identifier supplied by CSV."""
    db_path = _create_temp_db(tmp_path)
    old_id = create_room(
        "Temporary",
        "T1",
        "Temporary Building",
        1,
        "Office",
        db_path=db_path,
    )
    delete_room(old_id, db_path)
    csv_path = tmp_path / "rooms.csv"
    _write_csv(csv_path, OPTIONAL_ID_COLUMNS, [[1, *_new_row()]])

    summary = import_rooms_from_csv(csv_path, db_path)

    assert summary == {"created": 1, "updated": 0, "skipped": 0, "errors": []}
    assert get_room_by_id(1, db_path) is not None


def test_import_rooms_from_csv_skips_missing_required_rows(tmp_path) -> None:
    """Confirm rows with blank required fields are reported and skipped."""
    db_path = _create_temp_db(tmp_path)
    row = _new_row()
    row[0] = ""
    csv_path = tmp_path / "rooms.csv"
    _write_csv(csv_path, NEW_ONLY_COLUMNS, [row])

    summary = import_rooms_from_csv(csv_path, db_path)

    assert summary["skipped"] == 1
    assert "Row 2" in summary["errors"][0]
    assert get_all_rooms(db_path) == []


def test_import_rooms_from_csv_skips_invalid_numeric_rows(tmp_path) -> None:
    """Confirm invalid floor or coordinate values are reported and skipped."""
    db_path = _create_temp_db(tmp_path)
    bad_floor_row = _new_row()
    bad_floor_row[3] = "first"
    bad_coordinate_row = _new_row()
    bad_coordinate_row[6] = "east"
    csv_path = tmp_path / "rooms.csv"
    _write_csv(
        csv_path,
        NEW_ONLY_COLUMNS,
        [bad_floor_row, bad_coordinate_row],
    )

    summary = import_rooms_from_csv(csv_path, db_path)

    assert summary["skipped"] == 2
    assert len(summary["errors"]) == 2
    assert get_all_rooms(db_path) == []


def test_export_rooms_to_csv_writes_expected_columns_and_rows(tmp_path) -> None:
    """Confirm export uses exact documented columns and current rows."""
    db_path = _create_temp_db(tmp_path)
    create_room(
        "Lecture Hall",
        "A101",
        "Main Building",
        1,
        "Classroom",
        db_path=db_path,
    )
    csv_path = tmp_path / "exported_rooms.csv"

    exported_count = export_rooms_to_csv(csv_path, db_path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.reader(csv_file))

    assert exported_count == 1
    assert rows[0] == EXPORT_COLUMNS
    assert rows[1][1] == "Lecture Hall"
