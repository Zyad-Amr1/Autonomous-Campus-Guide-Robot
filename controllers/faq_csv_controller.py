"""Handle FAQ CSV import/export separately from the PySide6 UI layer."""

import csv
import sqlite3
from pathlib import Path

from database.repositories.faq_repository import (
    create_faq,
    get_all_faqs,
    get_faq_by_id,
    update_faq,
)

REQUIRED_COLUMNS = {"question", "answer"}
NEW_ONLY_COLUMNS = ["question", "answer", "keywords", "category"]
OPTIONAL_ID_COLUMNS = ["id", *NEW_ONLY_COLUMNS]
EXPORT_COLUMNS = OPTIONAL_ID_COLUMNS.copy()


def validate_faq_csv_headers(headers: list[str]) -> list[str]:
    """Validate and return normalized headers for either accepted CSV format."""
    normalized = [header.strip() for header in headers]
    if normalized not in (NEW_ONLY_COLUMNS, OPTIONAL_ID_COLUMNS):
        raise ValueError(
            "Invalid FAQ CSV columns. Expected exactly either question,answer,"
            "keywords,category or id,question,answer,keywords,category."
        )
    return normalized


def import_faq_from_csv(csv_path: str | Path, db_path) -> dict:
    """Import valid FAQ rows while reporting row-level failures."""
    source = Path(csv_path)
    if not source.is_file():
        raise FileNotFoundError(f"FAQ CSV file not found: {source}")
    summary = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    with source.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        try:
            headers = validate_faq_csv_headers(next(reader))
        except StopIteration as error:
            raise ValueError("FAQ CSV file is empty and has no header row.") from error
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
            data = {key: row[key] for key in NEW_ONLY_COLUMNS}
            try:
                raw_id = row.get("id", "")
                if raw_id:
                    try:
                        faq_id = int(raw_id)
                    except ValueError as error:
                        raise ValueError("id must be an integer") from error
                    existing = get_faq_by_id(faq_id, db_path)
                    if existing is not None and update_faq(faq_id, db_path=db_path, **data):
                        summary["updated"] += 1
                    else:
                        create_faq(db_path=db_path, **data)
                        summary["created"] += 1
                else:
                    create_faq(db_path=db_path, **data)
                    summary["created"] += 1
            except (ValueError, sqlite3.Error) as error:
                summary["skipped"] += 1
                summary["errors"].append(f"Row {row_number}: {error}")
    return summary


def export_faq_to_csv(csv_path: str | Path, db_path) -> int:
    """Export all current FAQs in the documented column order."""
    faqs = get_all_faqs(db_path)
    with Path(csv_path).open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for faq in faqs:
            writer.writerow({key: "" if faq[key] is None else faq[key] for key in EXPORT_COLUMNS})
    return len(faqs)
