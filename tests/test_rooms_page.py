"""Headless tests for the read-only Admin Rooms table page."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QAbstractItemView, QPushButton

from database.init_db import initialize_database
from database.repositories.room_repository import create_room, delete_room
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


def _create_room(db_path, name="Lecture Hall", number="A101") -> int:
    """Create a complete room row for page tests."""
    return create_room(
        name,
        number,
        "Main Building",
        1,
        "Classroom",
        "Teaching room",
        10.5,
        20.25,
        db_path,
    )


def test_rooms_page_can_be_instantiated(tmp_path) -> None:
    """Confirm the Rooms page can be constructed safely."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        assert page is not None
    finally:
        page.close()


def test_rooms_page_shows_empty_table_for_empty_database(tmp_path) -> None:
    """Confirm an empty database displays an empty table and zero status."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        assert page.rooms_table.rowCount() == 0
        assert "0" in page.rooms_status_label.text()
    finally:
        page.close()


def test_rooms_page_loads_room_rows(tmp_path) -> None:
    """Confirm room identity, location, and category values appear."""
    db_path = _create_temp_db(tmp_path)
    _create_room(db_path)
    _create_room(db_path, "Computer Lab", "B202")
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        assert page.rooms_table.rowCount() == 2
        names = {page.rooms_table.item(row, 1).text() for row in range(2)}
        numbers = {page.rooms_table.item(row, 2).text() for row in range(2)}
        buildings = {page.rooms_table.item(row, 3).text() for row in range(2)}
        categories = {page.rooms_table.item(row, 5).text() for row in range(2)}
        assert names == {"Lecture Hall", "Computer Lab"}
        assert numbers == {"A101", "B202"}
        assert buildings == {"Main Building"}
        assert categories == {"Classroom"}
    finally:
        page.close()


def test_rooms_page_refresh_updates_table(tmp_path) -> None:
    """Confirm reloading retrieves rooms created after page startup."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        assert page.rooms_table.rowCount() == 0
        _create_room(db_path)
        page.load_rooms()
        assert page.rooms_table.rowCount() == 1
    finally:
        page.close()


def test_rooms_page_table_supports_controlled_editing(tmp_path) -> None:
    """Confirm room business cells are editable while No. remains read-only."""
    db_path = _create_temp_db(tmp_path)
    _create_room(db_path)
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        assert page.rooms_table.editTriggers() != (
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        read_only_flags = (
            Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        )
        editable_flags = read_only_flags | Qt.ItemFlag.ItemIsEditable
        assert page.rooms_table.item(0, 0).flags() == read_only_flags
        for column in range(1, 9):
            assert page.rooms_table.item(0, column).flags() == editable_flags
    finally:
        page.close()


def test_rooms_page_has_refresh_button(tmp_path) -> None:
    """Confirm the Rooms page exposes its manual refresh action."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        assert isinstance(page.refresh_rooms_button, QPushButton)
        assert page.refresh_rooms_button.objectName() == "refresh_rooms_button"
        assert page.refresh_rooms_button.text() == "Refresh"
    finally:
        page.close()


def test_rooms_page_uses_row_numbers_not_database_ids(tmp_path) -> None:
    """Confirm sequential numbers display while real room IDs remain internal."""
    db_path = _create_temp_db(tmp_path)
    deleted_id = _create_room(db_path, "Temporary Room", "A001")
    delete_room(deleted_id, db_path)
    first_id = _create_room(db_path)
    second_id = _create_room(db_path, "Computer Lab", "B202")
    application = _get_application()
    page = RoomsPage(db_path)
    try:
        assert application is not None
        assert page.rooms_table.horizontalHeaderItem(0).text() == "No."
        number_items = [page.rooms_table.item(row, 0) for row in range(2)]
        assert [item.text() for item in number_items] == ["1", "2"]
        assert [
            item.data(Qt.ItemDataRole.UserRole) for item in number_items
        ] == [first_id, second_id]
        assert [item.text() for item in number_items] != [
            str(first_id),
            str(second_id),
        ]
    finally:
        page.close()
