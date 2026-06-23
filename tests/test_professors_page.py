"""Headless tests for the read-only Admin Professors table page."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QAbstractItemView, QPushButton

from database.init_db import initialize_database
from database.repositories.faculty_repository import create_faculty
from database.repositories.professor_repository import create_professor
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


def _create_professor_dependencies(db_path):
    """Create and return a faculty and office room for professor rows."""
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


def test_professors_page_can_be_instantiated(tmp_path) -> None:
    """Confirm the read-only Professors page can be constructed safely."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = ProfessorsPage(db_path=db_path)
    try:
        assert application is not None
        assert page is not None
    finally:
        page.close()


def test_professors_page_shows_empty_table_for_empty_database(tmp_path) -> None:
    """Confirm an empty database displays an empty table and zero status."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = ProfessorsPage(db_path=db_path)
    try:
        assert application is not None
        assert page.professors_table.rowCount() == 0
        assert "0" in page.professors_status_label.text()
    finally:
        page.close()


def test_professors_page_loads_professor_rows_with_joined_data(tmp_path) -> None:
    """Confirm professor rows include joined faculty and office information."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_professor_dependencies(db_path)
    create_professor(
        "Dr. Mona Hassan",
        "Professor",
        faculty_id,
        room_id,
        db_path=db_path,
    )
    create_professor(
        "Dr. Ahmed Ali",
        "Lecturer",
        faculty_id,
        room_id,
        db_path=db_path,
    )
    application = _get_application()
    page = ProfessorsPage(db_path=db_path)
    try:
        assert application is not None
        assert page.professors_table.rowCount() == 2
        names = {
            page.professors_table.item(row, 1).text()
            for row in range(page.professors_table.rowCount())
        }
        faculties = {
            page.professors_table.item(row, 3).text()
            for row in range(page.professors_table.rowCount())
        }
        office_rooms = {
            page.professors_table.item(row, 4).text()
            for row in range(page.professors_table.rowCount())
        }
        assert names == {"Dr. Mona Hassan", "Dr. Ahmed Ali"}
        assert faculties == {"Engineering"}
        assert office_rooms == {"Academic Office - A101"}
    finally:
        page.close()


def test_professors_page_refresh_updates_table(tmp_path) -> None:
    """Confirm reloading retrieves professor rows created after page startup."""
    db_path = _create_temp_db(tmp_path)
    faculty_id = create_faculty("Engineering", db_path=db_path)
    application = _get_application()
    page = ProfessorsPage(db_path=db_path)
    try:
        assert application is not None
        assert page.professors_table.rowCount() == 0
        create_professor(
            "Dr. Mona Hassan",
            "Professor",
            faculty_id,
            db_path=db_path,
        )

        page.load_professors()

        assert page.professors_table.rowCount() == 1
    finally:
        page.close()


def test_professors_page_table_supports_controlled_editing(tmp_path) -> None:
    """Confirm only supported professor business cells can be edited."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_professor_dependencies(db_path)
    create_professor(
        "Dr. Mona Hassan",
        "Professor",
        faculty_id,
        room_id,
        db_path=db_path,
    )
    application = _get_application()
    page = ProfessorsPage(db_path=db_path)
    try:
        assert application is not None
        assert page.professors_table.editTriggers() != (
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        for column in (1, 2, 5, 6, 7, 8, 9):
            assert page.professors_table.item(0, column).flags() & (
                Qt.ItemFlag.ItemIsEditable
            )
        for column in (0, 3, 4):
            assert not (
                page.professors_table.item(0, column).flags()
                & Qt.ItemFlag.ItemIsEditable
            )
    finally:
        page.close()


def test_professors_page_has_refresh_button(tmp_path) -> None:
    """Confirm the page exposes its manual table-refresh action."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = ProfessorsPage(db_path=db_path)
    try:
        assert application is not None
        assert isinstance(page.refresh_professors_button, QPushButton)
        assert page.refresh_professors_button.objectName() == "refresh_professors_button"
        assert page.refresh_professors_button.text() == "Refresh"
    finally:
        page.close()
