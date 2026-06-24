"""Handle course CSV import/export separately from the PySide6 UI layer."""

import csv
import sqlite3
from pathlib import Path

from database.connection import get_connection
from database.repositories.course_repository import (
    create_course,
    get_all_courses,
    get_course_by_id,
    update_course,
)
from database.repositories.faculty_repository import get_faculty_by_id
from database.repositories.professor_repository import get_professor_by_id
from database.repositories.room_repository import get_room_by_id

REQUIRED_COLUMNS = {"course_code", "course_name", "faculty_id"}
NEW_ONLY_COLUMNS = [
    "course_code", "course_name", "faculty_id", "professor_id", "room_id",
    "schedule_day", "start_time", "end_time", "semester",
]
OPTIONAL_ID_COLUMNS = ["id", *NEW_ONLY_COLUMNS]
EXPORT_COLUMNS = OPTIONAL_ID_COLUMNS.copy()


def _insert_course_with_id(course_id: int, db_path, **course_data) -> None:
    """Insert a course while preserving its CSV-provided identifier."""
    required_text = {
        "course_code": "Course code",
        "course_name": "Course name",
        "schedule_day": "Schedule day",
        "start_time": "Start time",
        "end_time": "End time",
    }
    for field_name, display_name in required_text.items():
        if not course_data[field_name]:
            raise ValueError(f"{display_name} cannot be empty.")

    connection = get_connection(db_path)
    try:
        connection.execute(
            """
            INSERT INTO courses (
                id, course_code, course_name, faculty_id, professor_id,
                room_id, schedule_day, start_time, end_time, semester
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                course_id,
                course_data["course_code"],
                course_data["course_name"],
                course_data["faculty_id"],
                course_data["professor_id"],
                course_data["room_id"],
                course_data["schedule_day"],
                course_data["start_time"],
                course_data["end_time"],
                course_data["semester"] or None,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def validate_courses_csv_headers(headers: list[str]) -> list[str]:
    """Validate and return normalized headers for either accepted CSV format."""
    normalized = [header.strip() for header in headers]
    if normalized not in (NEW_ONLY_COLUMNS, OPTIONAL_ID_COLUMNS):
        raise ValueError(
            "Invalid course CSV columns. Expected exactly either "
            "course_code,course_name,faculty_id,professor_id,room_id,"
            "schedule_day,start_time,end_time,semester or id,course_code,"
            "course_name,faculty_id,professor_id,room_id,schedule_day,"
            "start_time,end_time,semester."
        )
    return normalized


def _integer(value: str, field_name: str, required: bool = False) -> int | None:
    """Convert a required or optional identifier to an integer."""
    if not value:
        if required:
            raise ValueError(f"{field_name} is required")
        return None
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must be an integer") from error


def import_courses_from_csv(csv_path: str | Path, db_path) -> dict:
    """Import valid course rows while reporting row-level failures."""
    source = Path(csv_path)
    if not source.is_file():
        raise FileNotFoundError(f"Course CSV file not found: {source}")
    summary = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    with source.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        try:
            headers = validate_courses_csv_headers(next(reader))
        except StopIteration as error:
            raise ValueError("Course CSV file is empty and has no header row.") from error
        for row_number, values in enumerate(reader, start=2):
            if len(values) != len(headers):
                summary["skipped"] += 1
                summary["errors"].append(
                    f"Row {row_number}: expected {len(headers)} values, received {len(values)}."
                )
                continue
            row = {key: value.strip() for key, value in zip(headers, values, strict=True)}
            missing = [key for key in REQUIRED_COLUMNS if not row[key]]
            if missing:
                summary["skipped"] += 1
                summary["errors"].append(
                    f"Row {row_number}: required field(s) cannot be empty: {', '.join(sorted(missing))}."
                )
                continue
            try:
                data = {
                    "course_code": row["course_code"],
                    "course_name": row["course_name"],
                    "faculty_id": _integer(row["faculty_id"], "faculty_id", True),
                    "professor_id": _integer(row["professor_id"], "professor_id"),
                    "room_id": _integer(row["room_id"], "room_id"),
                    "schedule_day": row["schedule_day"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "semester": row["semester"],
                }
                faculty_id = data["faculty_id"]
                if get_faculty_by_id(faculty_id, db_path) is None:
                    raise ValueError(f"faculty_id {faculty_id} does not exist")
                professor_id = data["professor_id"]
                if (
                    professor_id is not None
                    and get_professor_by_id(professor_id, db_path) is None
                ):
                    raise ValueError(
                        f"professor_id {professor_id} does not exist"
                    )
                room_id = data["room_id"]
                if room_id is not None and get_room_by_id(room_id, db_path) is None:
                    raise ValueError(f"room_id {room_id} does not exist")
                raw_id = row.get("id", "")
                if raw_id:
                    course_id = _integer(raw_id, "id", True)
                    existing = get_course_by_id(course_id, db_path)
                    if existing is not None and update_course(course_id, db_path=db_path, **data):
                        summary["updated"] += 1
                    else:
                        _insert_course_with_id(course_id, db_path, **data)
                        summary["created"] += 1
                else:
                    create_course(db_path=db_path, **data)
                    summary["created"] += 1
            except (ValueError, sqlite3.Error) as error:
                summary["skipped"] += 1
                summary["errors"].append(f"Row {row_number}: {error}")
    return summary


def export_courses_to_csv(csv_path: str | Path, db_path) -> int:
    """Export all current courses in the documented column order."""
    courses = get_all_courses(db_path)
    with Path(csv_path).open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for course in courses:
            writer.writerow({key: "" if course[key] is None else course[key] for key in EXPORT_COLUMNS})
    return len(courses)
