"""Headless tests for the Rooms CSV and inline-editing workflow."""

import csv
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from database.init_db import initialize_database
from database.repositories.room_repository import (
    create_room,
    delete_room,
    get_all_rooms,
    get_room_by_id,
)
from ui.admin.pages.rooms_page import RoomsPage


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


def _create_room(db_path) -> int:
    """Create one complete room for page workflow tests."""
    return create_room(
        "Lecture Hall",
        "A101",
        "Main Building",
        1,
        "Classroom",
        "Teaching room",
        10.5,
        20.25,
        db_path,
    )


def test_rooms_page_has_faculty_style_toolbar_buttons(tmp_path) -> None:
    """Confirm the four visible toolbar actions use the required order."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        visible_button_names = [
            page.rooms_toolbar_layout.itemAt(index).widget().objectName()
            for index in range(4)
        ]
        assert visible_button_names == [
            "upload_rooms_csv_button",
            "delete_room_button",
            "export_rooms_csv_button",
            "save_rooms_table_button",
        ]
        assert page.refresh_rooms_button.isHidden()
    finally:
        page.close()


def test_rooms_page_visible_columns_match_expected(tmp_path) -> None:
    """Confirm the table exposes exactly the clean room columns."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        assert [
            page.rooms_table.horizontalHeaderItem(column).text()
            for column in range(page.rooms_table.columnCount())
        ] == [
            "No.",
            "Room Name",
            "Room Number",
            "Building",
            "Floor",
            "Category",
            "Description",
            "X Coord",
            "Y Coord",
        ]
    finally:
        page.close()


def test_rooms_page_upload_csv_automatically_imports_rows(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm Upload immediately imports into SQLite and reloads the table."""
    db_path = _create_temp_db(tmp_path)
    csv_path = tmp_path / "rooms.csv"
    csv_path.write_text(
        "room_name,room_number,building,floor,category,description,x_coord,"
        "y_coord\nLecture Hall,A101,Main Building,1,Classroom,Teaching room,"
        "10.5,20.25\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(csv_path), "CSV Files (*.csv)"),
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        page.upload_csv()
        assert page.rooms_table.rowCount() == 1
        assert get_all_rooms(db_path)[0]["room_name"] == "Lecture Hall"
    finally:
        page.close()


def test_rooms_page_export_csv_writes_file(tmp_path, monkeypatch) -> None:
    """Confirm Export writes the documented room CSV."""
    db_path = _create_temp_db(tmp_path)
    _create_room(db_path)
    output_path = tmp_path / "room_export"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(output_path), "CSV Files (*.csv)"),
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        page.export_csv()
        exported_path = tmp_path / "room_export.csv"
        assert exported_path.is_file()
        with exported_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as csv_file:
            rows = list(csv.reader(csv_file))
        assert rows[1][1] == "Lecture Hall"
    finally:
        page.close()


def test_rooms_page_save_edits_updates_database(tmp_path) -> None:
    """Confirm Save Edits validates and persists room business fields."""
    db_path = _create_temp_db(tmp_path)
    room_id = _create_room(db_path)
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        page.rooms_table.item(0, 1).setText("Updated Hall")
        page.rooms_table.item(0, 3).setText("Updated Building")
        page.save_table_changes()
        room = get_room_by_id(room_id, db_path)
        assert room is not None
        assert room["room_name"] == "Updated Hall"
        assert room["building"] == "Updated Building"
        assert page.rooms_status_label.text() == "Changes saved successfully."
    finally:
        page.close()


def test_rooms_page_delete_selected_row_removes_room(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm Delete Selected Row removes the internally identified record."""
    db_path = _create_temp_db(tmp_path)
    room_id = _create_room(db_path)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        page.rooms_table.selectRow(0)
        page.delete_selected_room()
        assert page.rooms_table.rowCount() == 0
        assert get_room_by_id(room_id, db_path) is None
    finally:
        page.close()


def test_rooms_page_uses_row_numbers_not_database_ids(tmp_path) -> None:
    """Confirm clean row numbers display while real IDs remain internal."""
    db_path = _create_temp_db(tmp_path)
    deleted_id = _create_room(db_path)
    delete_room(deleted_id, db_path)
    room_id = _create_room(db_path)
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        number_item = page.rooms_table.item(0, 0)
        assert page.rooms_table.horizontalHeaderItem(0).text() == "No."
        assert number_item.text() == "1"
        assert number_item.data(Qt.ItemDataRole.UserRole) == room_id
        assert number_item.text() != str(room_id)
    finally:
        page.close()
