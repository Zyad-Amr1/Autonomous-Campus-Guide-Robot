"""Handle professor CSV import/export separately from the PySide6 UI layer."""

import csv
import sqlite3
from pathlib import Path

from database.repositories.professor_repository import (
    create_professor,
    get_all_professors,
    get_professor_by_id,
    update_professor,
)

REQUIRED_COLUMNS = {"full_name", "faculty_id"}
NEW_ONLY_COLUMNS = [
    "full_name",
    "title",
    "faculty_id",
    "office_room_id",
    "email",
    "phone",
    "office_hours",
    "photo_path",
    "bio",
]
OPTIONAL_ID_COLUMNS = ["id", *NEW_ONLY_COLUMNS]
EXPORT_COLUMNS = OPTIONAL_ID_COLUMNS.copy()


def validate_professors_csv_headers(headers: list[str]) -> list[str]:
    """Validate and return normalized headers for either accepted CSV format."""
    normalized_headers = [header.strip() for header in headers]
    if normalized_headers not in (NEW_ONLY_COLUMNS, OPTIONAL_ID_COLUMNS):
        raise ValueError(
            "Invalid professor CSV columns. Expected exactly either "
            "full_name,title,faculty_id,office_room_id,email,phone,"
            "office_hours,photo_path,bio or id,full_name,title,faculty_id,"
            "office_room_id,email,phone,office_hours,photo_path,bio."
        )
    return normalized_headers


def _required_integer(value: str, field_name: str) -> int:
    """Convert a required CSV identifier to an integer with a clear error."""
    if not value:
        raise ValueError(f"{field_name} is required")
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must be an integer") from error


def _optional_integer(value: str, field_name: str) -> int | None:
    """Convert an optional CSV identifier to an integer when supplied."""
    if not value:
        return None
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must be an integer") from error


def import_professors_from_csv(csv_path: str | Path, db_path) -> dict:
    """Import valid professor rows while reporting row-level failures."""
    source_path = Path(csv_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Professor CSV file not found: {source_path}")

    summary = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    with source_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        try:
            headers = validate_professors_csv_headers(next(reader))
        except StopIteration as error:
            raise ValueError(
                "Professor CSV file is empty and has no header row."
            ) from error

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
            if not row["full_name"]:
                summary["skipped"] += 1
                summary["errors"].append(
                    f"Row {row_number}: professor full name cannot be empty."
                )
                continue

            try:
                professor_data = {
                    "full_name": row["full_name"],
                    "title": row["title"],
                    "faculty_id": _required_integer(
                        row["faculty_id"], "faculty_id"
                    ),
                    "office_room_id": _optional_integer(
                        row["office_room_id"], "office_room_id"
                    ),
                    "email": row["email"],
                    "phone": row["phone"],
                    "office_hours": row["office_hours"],
                    "photo_path": row["photo_path"],
                    "bio": row["bio"],
                }
                raw_id = row.get("id", "")
                if raw_id:
                    professor_id = _required_integer(raw_id, "id")
                    existing = get_professor_by_id(professor_id, db_path)
                    if existing is not None and update_professor(
                        professor_id,
                        db_path=db_path,
                        **professor_data,
                    ):
                        summary["updated"] += 1
                    else:
                        create_professor(db_path=db_path, **professor_data)
                        summary["created"] += 1
                else:
                    create_professor(db_path=db_path, **professor_data)
                    summary["created"] += 1
            except (ValueError, sqlite3.Error) as error:
                summary["skipped"] += 1
                summary["errors"].append(f"Row {row_number}: {error}")

    return summary


def export_professors_to_csv(csv_path: str | Path, db_path) -> int:
    """Export all current professor records in the documented column order."""
    destination_path = Path(csv_path)
    professors = get_all_professors(db_path)
    with destination_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for professor in professors:
            writer.writerow(
                {
                    column: "" if professor[column] is None else professor[column]
                    for column in EXPORT_COLUMNS
                }
            )
    return len(professors)
