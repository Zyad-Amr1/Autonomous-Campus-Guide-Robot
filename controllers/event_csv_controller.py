"""Handle event CSV import/export separately from the PySide6 UI layer."""

import csv
import sqlite3
from pathlib import Path

from database.repositories.event_repository import (
    create_event,
    get_all_events,
    get_event_by_id,
    update_event,
)

REQUIRED_COLUMNS = {"title", "start_date"}
NEW_ONLY_COLUMNS = [
    "title", "description", "location", "start_date", "end_date", "start_time", "end_time",
]
OPTIONAL_ID_COLUMNS = ["id", *NEW_ONLY_COLUMNS]
EXPORT_COLUMNS = OPTIONAL_ID_COLUMNS.copy()


def validate_events_csv_headers(headers: list[str]) -> list[str]:
    """Validate and return normalized headers for either accepted CSV format."""
    normalized = [header.strip() for header in headers]
    if normalized not in (NEW_ONLY_COLUMNS, OPTIONAL_ID_COLUMNS):
        raise ValueError(
            "Invalid event CSV columns. Expected exactly either title,description,"
            "location,start_date,end_date,start_time,end_time or id,title,description,"
            "location,start_date,end_date,start_time,end_time."
        )
    return normalized


def _event_data(row: dict[str, str]) -> dict:
    """Build repository data, defaulting a blank end date to the start date."""
    return {
        "title": row["title"], "description": row["description"],
        "location": row["location"], "start_date": row["start_date"],
        "end_date": row["end_date"] or row["start_date"],
        "start_time": row["start_time"], "end_time": row["end_time"],
    }


def import_events_from_csv(csv_path: str | Path, db_path) -> dict:
    """Import valid event rows while reporting row-level failures."""
    source = Path(csv_path)
    if not source.is_file():
        raise FileNotFoundError(f"Event CSV file not found: {source}")
    summary = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    with source.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        try:
            headers = validate_events_csv_headers(next(reader))
        except StopIteration as error:
            raise ValueError("Event CSV file is empty and has no header row.") from error
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
                data = _event_data(row)
                raw_id = row.get("id", "")
                if raw_id:
                    try:
                        event_id = int(raw_id)
                    except ValueError as error:
                        raise ValueError("id must be an integer") from error
                    existing = get_event_by_id(event_id, db_path)
                    if existing is not None and update_event(event_id, db_path=db_path, **data):
                        summary["updated"] += 1
                    else:
                        create_event(db_path=db_path, **data)
                        summary["created"] += 1
                else:
                    create_event(db_path=db_path, **data)
                    summary["created"] += 1
            except (ValueError, sqlite3.Error) as error:
                summary["skipped"] += 1
                summary["errors"].append(f"Row {row_number}: {error}")
    return summary


def export_events_to_csv(csv_path: str | Path, db_path) -> int:
    """Export all current events in the documented column order."""
    events = get_all_events(db_path)
    with Path(csv_path).open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for event in events:
            writer.writerow({key: "" if event[key] is None else event[key] for key in EXPORT_COLUMNS})
    return len(events)
