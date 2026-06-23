"""Headless tests for Faculty form and CRUD page actions."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from database.init_db import initialize_database
from database.repositories.faculty_repository import (
    create_faculty,
    delete_faculty,
    get_faculty_by_id,
)
from ui.admin.pages import faculties_page as faculties_page_module
from ui.admin.pages.faculties_page import FacultiesPage, FacultyFormDialog


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


class _AcceptedFacultyDialog:
    """Non-visual accepted form replacement used by CRUD action tests."""

    form_data = {
        "name": "Engineering",
        "description": "Engineering programs",
        "building": "Building A",
        "dean_name": "Dr. Ahmed Hassan",
    }

    def __init__(self, *args, **kwargs) -> None:
        """Accept the same constructor inputs as the real dialog."""

    def exec(self) -> QDialog.DialogCode:
        """Simulate a user accepting the faculty form."""
        return QDialog.DialogCode.Accepted

    def get_form_data(self) -> dict:
        """Return deterministic repository-ready faculty values."""
        return self.form_data.copy()


def test_faculty_form_dialog_can_be_instantiated_empty() -> None:
    """Confirm the faculty form exposes every required control."""
    application = _get_application()
    dialog = FacultyFormDialog()
    try:
        assert application is not None
        assert dialog.faculty_name_input is not None
        assert dialog.faculty_description_input is not None
        assert dialog.faculty_building_input is not None
        assert dialog.faculty_dean_name_input is not None
        assert dialog.save_faculty_button is not None
        assert dialog.cancel_faculty_button is not None
    finally:
        dialog.close()


def test_faculty_form_dialog_prefills_data_for_editing() -> None:
    """Confirm edit forms show the selected faculty's existing values."""
    application = _get_application()
    faculty_data = {
        "name": "Engineering",
        "description": "Engineering programs",
        "building": "Building A",
        "dean_name": "Dr. Ahmed Hassan",
    }
    dialog = FacultyFormDialog(faculty_data=faculty_data)
    try:
        assert application is not None
        assert dialog.faculty_name_input.text() == "Engineering"
        assert dialog.faculty_description_input.toPlainText() == "Engineering programs"
        assert dialog.faculty_building_input.text() == "Building A"
        assert dialog.faculty_dean_name_input.text() == "Dr. Ahmed Hassan"
    finally:
        dialog.close()


def test_faculty_form_dialog_get_form_data_returns_expected_values() -> None:
    """Confirm form controls produce the expected repository dictionary."""
    application = _get_application()
    dialog = FacultyFormDialog()
    try:
        assert application is not None
        dialog.faculty_name_input.setText("Engineering")
        dialog.faculty_description_input.setPlainText("Engineering programs")
        dialog.faculty_building_input.setText("Building A")
        dialog.faculty_dean_name_input.setText("Dr. Ahmed Hassan")

        assert dialog.get_form_data() == _AcceptedFacultyDialog.form_data
    finally:
        dialog.close()


def test_faculties_page_has_crud_buttons(tmp_path) -> None:
    """Confirm the Faculties page exposes all three management actions."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    try:
        assert application is not None
        assert "Add" in page.add_faculty_button.text()
        assert "Edit" in page.edit_faculty_button.text()
        assert "Delete" in page.delete_faculty_button.text()
    finally:
        page.close()


def test_faculties_page_add_faculty_updates_table(tmp_path, monkeypatch) -> None:
    """Confirm an accepted Add form creates and displays a faculty."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    monkeypatch.setattr(
        faculties_page_module,
        "FacultyFormDialog",
        _AcceptedFacultyDialog,
    )
    try:
        assert application is not None
        page.add_faculty()

        assert page.faculties_table.rowCount() == 1
        assert page.faculties_table.item(0, 1).text() == "Engineering"
    finally:
        page.close()


def test_faculties_page_edit_selected_faculty_updates_row(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm an accepted Edit form updates the selected faculty row."""
    db_path = _create_temp_db(tmp_path)
    create_faculty("Old Faculty", db_path=db_path)
    application = _get_application()
    page = FacultiesPage(db_path)

    class UpdatedFacultyDialog(_AcceptedFacultyDialog):
        form_data = {
            **_AcceptedFacultyDialog.form_data,
            "name": "Updated Engineering",
        }

    monkeypatch.setattr(
        faculties_page_module,
        "FacultyFormDialog",
        UpdatedFacultyDialog,
    )
    try:
        assert application is not None
        page.faculties_table.selectRow(0)
        page.edit_selected_faculty()

        assert page.faculties_table.item(0, 1).text() == "Updated Engineering"
    finally:
        page.close()


def test_faculties_page_delete_selected_faculty_removes_row(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm a confirmed Delete action removes the selected faculty."""
    db_path = _create_temp_db(tmp_path)
    deleted_id = create_faculty("Temporary", db_path=db_path)
    delete_faculty(deleted_id, db_path)
    faculty_id = create_faculty("Engineering", db_path=db_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    try:
        assert application is not None
        assert page.faculties_table.item(0, 0).text() == "1"
        page.faculties_table.selectRow(0)
        page.delete_selected_faculty()

        assert page.faculties_table.rowCount() == 0
        assert get_faculty_by_id(faculty_id, db_path) is None
    finally:
        page.close()


def test_faculties_page_edit_without_selection_shows_warning(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm Edit provides guidance when no table row is selected."""
    db_path = _create_temp_db(tmp_path)
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
        page.edit_selected_faculty()

        assert len(warnings) == 1
        assert warnings[0][2] == "Please select a faculty to edit."
    finally:
        page.close()


def test_faculties_page_delete_without_selection_shows_warning(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm Delete provides guidance when no table row is selected."""
    db_path = _create_temp_db(tmp_path)
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
        page.delete_selected_faculty()

        assert len(warnings) == 1
        assert warnings[0][2] == "Please select a faculty to delete."
    finally:
        page.close()
