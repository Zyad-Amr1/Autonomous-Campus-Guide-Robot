"""Headless tests for the read-only Admin Faculties table page."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QAbstractItemView, QPushButton

from database.init_db import initialize_database
from database.repositories.faculty_repository import create_faculty
from ui.admin.pages.faculties_page import FacultiesPage


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


def test_faculties_page_can_be_instantiated(tmp_path) -> None:
    """Confirm the read-only Faculties page can be constructed safely."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = FacultiesPage(db_path=db_path)
    try:
        assert application is not None
        assert page is not None
    finally:
        page.close()


def test_faculties_page_shows_empty_table_for_empty_database(tmp_path) -> None:
    """Confirm an empty database displays an empty table and zero status."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = FacultiesPage(db_path=db_path)
    try:
        assert application is not None
        assert page.faculties_table.rowCount() == 0
        assert "0" in page.faculties_status_label.text()
    finally:
        page.close()


def test_faculties_page_loads_faculty_rows(tmp_path) -> None:
    """Confirm repository faculty rows and names appear in the table."""
    db_path = _create_temp_db(tmp_path)
    create_faculty("Engineering", db_path=db_path)
    create_faculty("Business", db_path=db_path)
    application = _get_application()
    page = FacultiesPage(db_path=db_path)
    try:
        assert application is not None
        assert page.faculties_table.rowCount() == 2
        names = {
            page.faculties_table.item(row, 1).text()
            for row in range(page.faculties_table.rowCount())
        }
        assert names == {"Engineering", "Business"}
    finally:
        page.close()


def test_faculties_page_refresh_updates_table(tmp_path) -> None:
    """Confirm reloading retrieves faculty rows created after page startup."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = FacultiesPage(db_path=db_path)
    try:
        assert application is not None
        assert page.faculties_table.rowCount() == 0
        create_faculty("Engineering", db_path=db_path)

        page.load_faculties()

        assert page.faculties_table.rowCount() == 1
    finally:
        page.close()


def test_faculties_page_table_is_read_only(tmp_path) -> None:
    """Confirm table cells cannot be edited during this view-only phase."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = FacultiesPage(db_path=db_path)
    try:
        assert application is not None
        assert (
            page.faculties_table.editTriggers()
            == QAbstractItemView.EditTrigger.NoEditTriggers
        )
    finally:
        page.close()


def test_faculties_page_has_refresh_button(tmp_path) -> None:
    """Confirm the page exposes its manual table-refresh action."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = FacultiesPage(db_path=db_path)
    try:
        assert application is not None
        assert isinstance(page.refresh_faculties_button, QPushButton)
        assert page.refresh_faculties_button.objectName() == "refresh_faculties_button"
        assert page.refresh_faculties_button.text() == "Refresh"
    finally:
        page.close()
