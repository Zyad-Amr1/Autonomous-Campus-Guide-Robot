"""Headless tests for professor form and CRUD page actions."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox

from database.init_db import initialize_database
from database.repositories.faculty_repository import create_faculty
from database.repositories.professor_repository import (
    create_professor,
    get_professor_by_id,
)
from database.repositories.room_repository import create_room
from ui.admin.pages import professors_page as professors_page_module
from ui.admin.pages.professors_page import ProfessorFormDialog, ProfessorsPage


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
    """Create and return one faculty and one professor office room."""
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


def _professor_data(faculty_id: int, room_id: int) -> dict:
    """Return complete repository-ready data for CRUD action tests."""
    return {
        "full_name": "Dr. Mona Hassan",
        "title": "Professor",
        "faculty_id": faculty_id,
        "office_room_id": room_id,
        "email": "mona@example.edu",
        "phone": "01000000000",
        "office_hours": "Sunday 10:00-12:00",
        "photo_path": "photos/mona.jpg",
        "bio": "Engineering professor.",
    }


class _AcceptedProfessorDialog:
    """Accepted form replacement whose values can be set by each test."""

    form_data: dict = {}

    def __init__(self, *args, **kwargs) -> None:
        """Accept the same constructor arguments as the real form."""

    def exec(self) -> QDialog.DialogCode:
        """Simulate acceptance without displaying a window."""
        return QDialog.DialogCode.Accepted

    def get_form_data(self) -> dict:
        """Return deterministic professor values for repository calls."""
        return self.form_data.copy()


def test_professor_form_dialog_can_be_instantiated(tmp_path) -> None:
    """Confirm the form exposes all required professor controls."""
    db_path = _create_temp_db(tmp_path)
    _create_dependencies(db_path)
    application = _get_application()
    dialog = ProfessorFormDialog(db_path=db_path)
    try:
        assert application is not None
        assert dialog.professor_full_name_input is not None
        assert dialog.professor_title_input is not None
        assert dialog.professor_faculty_combo is not None
        assert dialog.professor_office_room_combo is not None
        assert dialog.professor_email_input is not None
        assert dialog.professor_phone_input is not None
        assert dialog.professor_office_hours_input is not None
        assert dialog.professor_photo_path_input is not None
        assert dialog.browse_professor_photo_button is not None
        assert dialog.professor_bio_input is not None
        assert dialog.save_professor_button is not None
        assert dialog.cancel_professor_button is not None
    finally:
        dialog.close()


def test_professor_form_dialog_loads_faculty_and_room_options(tmp_path) -> None:
    """Confirm related records appear with their real IDs as combo data."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    application = _get_application()
    dialog = ProfessorFormDialog(db_path=db_path)
    try:
        assert application is not None
        faculty_index = dialog.professor_faculty_combo.findData(faculty_id)
        room_index = dialog.professor_office_room_combo.findData(room_id)
        assert faculty_index >= 0
        assert dialog.professor_faculty_combo.itemText(faculty_index) == "Engineering"
        assert room_index >= 0
        assert "A101" in dialog.professor_office_room_combo.itemText(room_index)
        assert dialog.professor_office_room_combo.itemData(0) is None
    finally:
        dialog.close()


def test_professor_form_dialog_prefills_data_for_editing(tmp_path) -> None:
    """Confirm an existing professor row pre-fills text and related IDs."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    professor_id = create_professor(
        db_path=db_path,
        **_professor_data(faculty_id, room_id),
    )
    professor = get_professor_by_id(professor_id, db_path)
    application = _get_application()
    dialog = ProfessorFormDialog(db_path=db_path, professor_data=professor)
    try:
        assert application is not None
        assert dialog.professor_full_name_input.text() == "Dr. Mona Hassan"
        assert dialog.professor_title_input.text() == "Professor"
        assert dialog.professor_faculty_combo.currentData() == faculty_id
        assert dialog.professor_office_room_combo.currentData() == room_id
        assert dialog.professor_email_input.text() == "mona@example.edu"
        assert dialog.professor_bio_input.toPlainText() == "Engineering professor."
    finally:
        dialog.close()


def test_professor_form_dialog_get_form_data_returns_expected_values(
    tmp_path,
) -> None:
    """Confirm form controls produce a complete repository dictionary."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    expected = _professor_data(faculty_id, room_id)
    application = _get_application()
    dialog = ProfessorFormDialog(db_path=db_path)
    try:
        assert application is not None
        dialog.professor_full_name_input.setText(expected["full_name"])
        dialog.professor_title_input.setText(expected["title"])
        dialog.professor_faculty_combo.setCurrentIndex(
            dialog.professor_faculty_combo.findData(faculty_id)
        )
        dialog.professor_office_room_combo.setCurrentIndex(
            dialog.professor_office_room_combo.findData(room_id)
        )
        dialog.professor_email_input.setText(expected["email"])
        dialog.professor_phone_input.setText(expected["phone"])
        dialog.professor_office_hours_input.setText(expected["office_hours"])
        dialog.professor_photo_path_input.setText(expected["photo_path"])
        dialog.professor_bio_input.setPlainText(expected["bio"])

        assert dialog.get_form_data() == expected
    finally:
        dialog.close()


def test_professors_page_has_crud_buttons(tmp_path) -> None:
    """Confirm the Professors page exposes all three management actions."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        assert "Add" in page.add_professor_button.text()
        assert "Edit" in page.edit_professor_button.text()
        assert "Delete" in page.delete_professor_button.text()
    finally:
        page.close()


def test_professors_page_add_professor_updates_table(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm an accepted Add form creates and displays a professor."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    _AcceptedProfessorDialog.form_data = _professor_data(faculty_id, room_id)
    monkeypatch.setattr(
        professors_page_module,
        "ProfessorFormDialog",
        _AcceptedProfessorDialog,
    )
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        page.add_professor()
        assert page.professors_table.rowCount() == 1
        assert page.professors_table.item(0, 1).text() == "Dr. Mona Hassan"
    finally:
        page.close()


def test_professors_page_edit_selected_professor_updates_row(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm an accepted Edit form updates the selected professor."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    create_professor(
        db_path=db_path,
        **_professor_data(faculty_id, room_id),
    )
    updated_data = _professor_data(faculty_id, room_id)
    updated_data["full_name"] = "Dr. Mona Updated"
    _AcceptedProfessorDialog.form_data = updated_data
    monkeypatch.setattr(
        professors_page_module,
        "ProfessorFormDialog",
        _AcceptedProfessorDialog,
    )
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        page.professors_table.selectRow(0)
        page.edit_selected_professor()
        assert page.professors_table.item(0, 1).text() == "Dr. Mona Updated"
    finally:
        page.close()


def test_professors_page_delete_selected_professor_removes_row(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm a confirmed Delete action removes the selected professor."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id = _create_dependencies(db_path)
    create_professor(
        db_path=db_path,
        **_professor_data(faculty_id, room_id),
    )
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
    finally:
        page.close()


def test_professors_page_edit_without_selection_shows_warning(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm Edit provides guidance when no professor is selected."""
    db_path = _create_temp_db(tmp_path)
    warnings: list[tuple] = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: warnings.append(args),
    )
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        page.edit_selected_professor()
        assert warnings[0][2] == "Please select a professor to edit."
    finally:
        page.close()


def test_professors_page_delete_without_selection_shows_warning(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm Delete provides guidance when no professor is selected."""
    db_path = _create_temp_db(tmp_path)
    warnings: list[tuple] = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: warnings.append(args),
    )
    application = _get_application()
    page = ProfessorsPage(db_path)
    try:
        assert application is not None
        page.delete_selected_professor()
        assert warnings[0][2] == "Please select a professor to delete."
    finally:
        page.close()


def test_professor_form_dialog_browse_photo_sets_path(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm the photo chooser copies its selected image path."""
    db_path = _create_temp_db(tmp_path)
    _create_dependencies(db_path)
    fake_path = str(tmp_path / "professor.jpg")
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (fake_path, "Image Files (*.jpg)"),
    )
    application = _get_application()
    dialog = ProfessorFormDialog(db_path=db_path)
    try:
        assert application is not None
        dialog.browse_photo()
        assert dialog.professor_photo_path_input.text() == fake_path
    finally:
        dialog.close()
