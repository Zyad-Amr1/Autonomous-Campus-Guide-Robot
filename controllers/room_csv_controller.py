"""Handle room CSV import/export separately from the PySide6 UI layer."""

import csv
import sqlite3
from pathlib import Path

from database.connection import get_connection
from database.repositories.room_repository import (
    create_room,
    get_all_rooms,
    get_room_by_id,
    update_room,
)

REQUIRED_COLUMNS = {"room_name", "room_number", "building", "floor", "category"}
NEW_ONLY_COLUMNS = [
    "room_name",
    "room_number",
    "building",
    "floor",
    "category",
    "description",
    "x_coord",
    "y_coord",
]
OPTIONAL_ID_COLUMNS = ["id", *NEW_ONLY_COLUMNS]
EXPORT_COLUMNS = OPTIONAL_ID_COLUMNS.copy()


def _insert_room_with_id(room_id: int, db_path, **room_data) -> None:
    """Insert a room while preserving its CSV-provided identifier."""
    connection = get_connection(db_path)
    try:
        connection.execute(
            """
            INSERT INTO rooms (
                id, room_name, room_number, building, floor, category,
                description, x_coord, y_coord
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                room_id,
                room_data["room_name"],
                room_data["room_number"],
                room_data["building"],
                room_data["floor"],
                room_data["category"],
                room_data["description"] or None,
                room_data["x_coord"],
                room_data["y_coord"],
            ),
        )
        connection.commit()
    finally:
        connection.close()


def validate_rooms_csv_headers(headers: list[str]) -> list[str]:
    """Validate and return normalized headers for either accepted CSV format."""
    normalized_headers = [header.strip() for header in headers]
    if normalized_headers not in (NEW_ONLY_COLUMNS, OPTIONAL_ID_COLUMNS):
        raise ValueError(
            "Invalid room CSV columns. Expected exactly either "
            "room_name,room_number,building,floor,category,description,"
            "x_coord,y_coord or id,room_name,room_number,building,floor,"
            "category,description,x_coord,y_coord."
        )
    return normalized_headers


def _required_integer(value: str, field_name: str) -> int:
    """Convert a required CSV value to an integer with a clear error."""
    if not value:
        raise ValueError(f"{field_name} is required")
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must be an integer") from error


def _optional_float(value: str, field_name: str) -> float | None:
    """Convert an optional CSV coordinate to a float when supplied."""
    if not value:
        return None
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must be numeric") from error


def import_rooms_from_csv(csv_path: str | Path, db_path) -> dict:
    """Import valid room rows while reporting row-level failures."""
    source_path = Path(csv_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Room CSV file not found: {source_path}")

    summary = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    with source_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        try:
            headers = validate_rooms_csv_headers(next(reader))
        except StopIteration as error:
            raise ValueError("Room CSV file is empty and has no header row.") from error

        for row_number, values in enumerate(reader, start=2):
            if len(values) != len(headers):
                summary["skipped"] += 1
                summary["errors"].append(
                    f"Row {row_number}: expected {len(headers)} values, "
                    f"received {len(values)}."
                )
                continue

            row = {
                header: value.strip()
                for header, value in zip(headers, values, strict=True)
            }
            missing_fields = [
                field_name
                for field_name in REQUIRED_COLUMNS
                if not row[field_name]
            ]
            if missing_fields:
                summary["skipped"] += 1
                summary["errors"].append(
                    f"Row {row_number}: required field(s) cannot be empty: "
                    f"{', '.join(sorted(missing_fields))}."
                )
                continue

            try:
                room_data = {
                    "room_name": row["room_name"],
                    "room_number": row["room_number"],
                    "building": row["building"],
                    "floor": _required_integer(row["floor"], "floor"),
                    "category": row["category"],
                    "description": row["description"],
                    "x_coord": _optional_float(row["x_coord"], "x_coord"),
                    "y_coord": _optional_float(row["y_coord"], "y_coord"),
                }
                raw_id = row.get("id", "")
                if raw_id:
                    room_id = _required_integer(raw_id, "id")
                    existing = get_room_by_id(room_id, db_path)
                    if existing is not None and update_room(
                        room_id,
                        db_path=db_path,
                        **room_data,
                    ):
                        summary["updated"] += 1
                    else:
                        _insert_room_with_id(room_id, db_path, **room_data)
                        summary["created"] += 1
                else:
                    create_room(db_path=db_path, **room_data)
                    summary["created"] += 1
            except (ValueError, sqlite3.Error) as error:
                summary["skipped"] += 1
                summary["errors"].append(f"Row {row_number}: {error}")

    return summary


def export_rooms_to_csv(csv_path: str | Path, db_path) -> int:
    """Export all current room records in the documented column order."""
    destination_path = Path(csv_path)
    rooms = get_all_rooms(db_path)
    with destination_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for room in rooms:
            writer.writerow(
                {
                    column: "" if room[column] is None else room[column]
                    for column in EXPORT_COLUMNS
                }
            )
    return len(rooms)
