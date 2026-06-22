"""Handle faculty CSV import/export separately from the PySide6 UI layer."""

import csv
import sqlite3
from pathlib import Path

from database.repositories.faculty_repository import (
    create_faculty,
    get_all_faculties,
    get_faculty_by_id,
    update_faculty,
)

REQUIRED_COLUMNS = {"name"}
BUSINESS_COLUMNS = ["name", "description", "building", "dean_name"]
OPTIONAL_ID_COLUMNS = ["id", "name", "description", "building", "dean_name"]
NEW_ONLY_COLUMNS = ["name", "description", "building", "dean_name"]
EXPORT_COLUMNS = [
    "id",
    "name",
    "description",
    "building",
    "dean_name",
    "created_at",
    "updated_at",
]


def validate_faculties_csv_headers(headers: list[str]) -> list[str]:
    """Validate and return normalized headers for either accepted CSV format."""
    normalized_headers = [header.strip() for header in headers]
    accepted_formats = (NEW_ONLY_COLUMNS, OPTIONAL_ID_COLUMNS)
    if normalized_headers not in accepted_formats:
        raise ValueError(
            "Invalid faculty CSV columns. Expected exactly either "
            "name,description,building,dean_name or "
            "id,name,description,building,dean_name."
        )
    return normalized_headers


def import_faculties_from_csv(csv_path: str | Path, db_path) -> dict:
    """Import valid faculty rows while reporting row-level failures."""
    source_path = Path(csv_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Faculty CSV file not found: {source_path}")

    summary = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    with source_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        try:
            headers = validate_faculties_csv_headers(next(reader))
        except StopIteration as error:
            raise ValueError("Faculty CSV file is empty and has no header row.") from error

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
            if not row["name"]:
                summary["skipped"] += 1
                summary["errors"].append(
                    f"Row {row_number}: faculty name cannot be empty."
                )
                continue

            faculty_data = {column: row.get(column, "") for column in BUSINESS_COLUMNS}
            try:
                raw_id = row.get("id", "")
                if raw_id:
                    try:
                        faculty_id = int(raw_id)
                    except ValueError as error:
                        raise ValueError("faculty id must be an integer") from error

                    existing_faculty = get_faculty_by_id(faculty_id, db_path)
                    if existing_faculty is not None and update_faculty(
                        faculty_id,
                        db_path=db_path,
                        **faculty_data,
                    ):
                        summary["updated"] += 1
                    else:
                        create_faculty(db_path=db_path, **faculty_data)
                        summary["created"] += 1
                else:
                    create_faculty(db_path=db_path, **faculty_data)
                    summary["created"] += 1
            except (ValueError, sqlite3.Error) as error:
                summary["skipped"] += 1
                summary["errors"].append(f"Row {row_number}: {error}")

    return summary


def export_faculties_to_csv(csv_path: str | Path, db_path) -> int:
    """Export all current faculty records using the documented column order."""
    destination_path = Path(csv_path)
    faculties = get_all_faculties(db_path)

    with destination_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for faculty in faculties:
            writer.writerow(
                {
                    column: "" if faculty[column] is None else faculty[column]
                    for column in EXPORT_COLUMNS
                }
            )

    return len(faculties)
