"""Headless tests for the Professors CSV and inline-editing workflow."""

import csv
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from database.init_db import initialize_database
from database.repositories.faculty_repository import create_faculty
from database.repositories.professor_repository import (
    create_professor as create_professor_record,
    delete_professor,
    get_all_professors,
    get_professor_by_id,
)
from database.repositories.room_repository import create_room
from ui.admin.pages.professors_page import ProfessorsPage


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _create_temp_db(tmp_path):
    """Initialize and return an isolated database for one widget test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    return database_path


def _create_dependencies(db_path) -> tuple[int, int]:
    """Create and return valid faculty and office-room identifiers."""
    faculty_id = create_faculty("Engineering", db_path=db_path)
    room_id = create_room(
        "Academic Office",
        "A101",
        "Engineering Building",
        1,
        "Office",
        db_path=db_path,
    )
    return faculty_id, room_id


def _create_professor(db_path, faculty_id: int, room_id: int) -> int:
    """Create one complete professor for page workflow tests."""
    return create_professor_record(
        "Dr. Mona Hassan",
        "Professor",
        faculty_id,
        room_id,
        "mona@example.edu",
        db_path=db_path,
    )


def test_professors_page_has_faculty_style_toolbar_buttons(tmp_path) -> None:
    """Confirm the four visible toolbar actions use the required order."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        visible_button_names = [
            page.professors_toolbar_layout.itemAt(index).widget().objectName()
            for index in range(4)
        ]
        assert visible_button_names == [
            "upload_professors_csv_button",
            "delete_professor_button",
            "export_professors_csv_button",
            "save_professors_table_button",
        ]
        assert page.add_professor_button.isHidden()
        assert page.edit_professor_button.isHidden()
        assert page.refresh_professors_button.isHidden()
    finally:
        page.close()


def test_professors_page_visible_columns_match_expected(tmp_path) -> None:
    """Confirm the table exposes only the clean professor columns."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        assert [
            page.professors_table.horizontalHeaderItem(column).text()
            for column in range(page.professors_table.columnCount())
        ] == [
            "No.",
            "Full Name",
            "Title",
            "Faculty",
            "Office Room",
            "Email",
            "Phone",
            "Office Hours",
            "Photo Path",
            "Bio",
        ]
    finally:
        page.close()


def test_professors_page_upload_csv_automatically_imports_rows(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm Upload immediately imports into SQLite and reloads the table."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    csv_path = tmp_path / "professors.csv"
    csv_path.write_text(
        "full_name,title,faculty_id,office_room_id,email,phone,office_hours,"
        "photo_path,bio\n"
        f"Dr. Mona Hassan,Professor,{faculty_id},{room_id},mona@example.edu,"
        ",,,Engineering professor\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(csv_path), "CSV Files (*.csv)"),
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        page.upload_csv()
        assert page.professors_table.rowCount() == 1
        assert get_all_professors(db_path)[0]["full_name"] == "Dr. Mona Hassan"
    finally:
        page.close()


def test_professors_page_upload_csv_reports_missing_relationships(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm skipped foreign keys produce clear import-order guidance."""
    db_path = _create_temp_db(tmp_path)
    csv_path = tmp_path / "professors.csv"
    csv_path.write_text(
        "full_name,title,faculty_id,office_room_id,email,phone,office_hours,"
        "photo_path,bio\nDr. Missing,Professor,9999,,,,,,\n",
        encoding="utf-8",
    )
    messages: list[str] = []
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(csv_path), "CSV Files (*.csv)"),
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: messages.append(args[2]),
    )
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        page.upload_csv()
        assert page.professors_table.rowCount() == 0
        assert "Skipped: 1" in messages[0]
        assert (
            "Some rows were skipped because their faculty_id or "
            "office_room_id does not exist."
        ) in messages[0]
        assert "Recommended import order:" in messages[0]
        assert "faculties.csv → rooms.csv → professors.csv" in messages[0]
        assert "FOREIGN KEY constraint failed" not in messages[0]
    finally:
        page.close()


def test_professors_page_export_csv_writes_file(tmp_path, monkeypatch) -> None:
    """Confirm Export writes the documented professor CSV."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    _create_professor(db_path, faculty_id, room_id)
    output_path = tmp_path / "professor_export"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(output_path), "CSV Files (*.csv)"),
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        page.export_csv()
        exported_path = tmp_path / "professor_export.csv"
        assert exported_path.is_file()
        with exported_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as csv_file:
            rows = list(csv.reader(csv_file))
        assert rows[1][1] == "Dr. Mona Hassan"
    finally:
        page.close()


def test_professors_page_save_edits_updates_database(tmp_path) -> None:
    """Confirm Save Edits persists editable fields with relationship IDs."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    professor_id = _create_professor(db_path, faculty_id, room_id)
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        page.professors_table.item(0, 1).setText("Dr. Mona Updated")
        page.professors_table.item(0, 5).setText("updated@example.edu")
        page.save_table_changes()
        professor = get_professor_by_id(professor_id, db_path)
        assert professor is not None
        assert professor["full_name"] == "Dr. Mona Updated"
        assert professor["email"] == "updated@example.edu"
        assert professor["faculty_id"] == faculty_id
        assert professor["office_room_id"] == room_id
        assert page.professors_status_label.text() == "Changes saved successfully."
    finally:
        page.close()


def test_professors_page_delete_selected_row_removes_professor(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm Delete Selected Row removes the internally identified record."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    professor_id = _create_professor(db_path, faculty_id, room_id)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        page.professors_table.selectRow(0)
        page.delete_selected_professor()
        assert page.professors_table.rowCount() == 0
        assert get_professor_by_id(professor_id, db_path) is None
    finally:
        page.close()


def test_professors_page_uses_row_numbers_not_database_ids(tmp_path) -> None:
    """Confirm clean row numbers display while real IDs remain internal."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    deleted_id = _create_professor(db_path, faculty_id, room_id)
    delete_professor(deleted_id, db_path)
    professor_id = _create_professor(db_path, faculty_id, room_id)
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        number_item = page.professors_table.item(0, 0)
        assert page.professors_table.horizontalHeaderItem(0).text() == "No."
        assert number_item.text() == "1"
        assert number_item.data(Qt.ItemDataRole.UserRole) == professor_id
        assert number_item.text() != str(professor_id)
    finally:
        page.close()
