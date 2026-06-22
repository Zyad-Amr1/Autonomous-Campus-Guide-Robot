"""Headless tests for controlled inline editing of faculty business fields."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from database.init_db import initialize_database
from database.repositories.faculty_repository import (
    create_faculty,
    get_faculty_by_id,
)
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


def _create_faculty(db_path) -> int:
    """Create a complete faculty record for inline-editing tests."""
    return create_faculty(
        "Engineering",
        "Engineering programs",
        "Building A",
        "Dr. Ahmed Hassan",
        db_path,
    )


def test_faculties_table_business_columns_are_editable(tmp_path) -> None:
    """Confirm only the four business-value cells permit inline editing."""
    db_path = _create_temp_db(tmp_path)
    _create_faculty(db_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    try:
        assert application is not None
        for column_index in (1, 2, 3, 4):
            assert page.faculties_table.item(0, column_index).flags() & (
                Qt.ItemFlag.ItemIsEditable
            )
    finally:
        page.close()


def test_faculties_table_system_columns_are_read_only(tmp_path) -> None:
    """Confirm the visible identifier column cannot be edited inline."""
    db_path = _create_temp_db(tmp_path)
    _create_faculty(db_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    try:
        assert application is not None
        assert not (
            page.faculties_table.item(0, 0).flags()
            & Qt.ItemFlag.ItemIsEditable
        )
    finally:
        page.close()


def test_faculties_page_has_save_and_revert_buttons(tmp_path) -> None:
    """Confirm the table exposes explicit persistence and discard actions."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    try:
        assert application is not None
        assert page.save_faculties_table_button is not None
        assert page.revert_faculties_table_button is not None
    finally:
        page.close()


def test_editing_cell_marks_unsaved_changes(tmp_path) -> None:
    """Confirm a business-cell edit activates unsaved-change state."""
    db_path = _create_temp_db(tmp_path)
    _create_faculty(db_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    try:
        assert application is not None
        page.faculties_table.item(0, 1).setText("Applied Engineering")

        assert page.has_unsaved_changes is True
        assert page.faculties_status_label.text() == "Unsaved changes"
    finally:
        page.close()


def test_save_table_changes_updates_database(tmp_path) -> None:
    """Confirm saving inline edits persists all business fields."""
    db_path = _create_temp_db(tmp_path)
    faculty_id = _create_faculty(db_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    try:
        assert application is not None
        page.faculties_table.item(0, 1).setText("Applied Engineering")
        page.faculties_table.item(0, 2).setText("Updated programs")
        page.faculties_table.item(0, 3).setText("Building B")
        page.faculties_table.item(0, 4).setText("Dr. Mona Ali")

        page.save_table_changes()
        faculty = get_faculty_by_id(faculty_id, db_path)

        assert faculty is not None
        assert faculty["name"] == "Applied Engineering"
        assert faculty["description"] == "Updated programs"
        assert faculty["building"] == "Building B"
        assert faculty["dean_name"] == "Dr. Mona Ali"
        assert page.has_unsaved_changes is False
        assert page.faculties_status_label.text() == "Changes saved successfully."
    finally:
        page.close()


def test_save_table_changes_rejects_empty_name(tmp_path, monkeypatch) -> None:
    """Confirm inline persistence rejects an empty required faculty name."""
    db_path = _create_temp_db(tmp_path)
    _create_faculty(db_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    warnings: list[tuple] = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: warnings.append(args),
    )
    try:
        assert application is not None
        page.faculties_table.item(0, 1).setText("")

        page.save_table_changes()

        assert len(warnings) == 1
        assert page.has_unsaved_changes is True
    finally:
        page.close()


def test_revert_table_changes_restores_database_values(tmp_path) -> None:
    """Confirm reverting discards inline edits and reloads repository data."""
    db_path = _create_temp_db(tmp_path)
    _create_faculty(db_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    try:
        assert application is not None
        page.faculties_table.item(0, 1).setText("Temporary Name")

        page.revert_table_changes()

        assert page.faculties_table.item(0, 1).text() == "Engineering"
        assert page.has_unsaved_changes is False
        assert page.faculties_status_label.text() == "Changes reverted."
    finally:
        page.close()
