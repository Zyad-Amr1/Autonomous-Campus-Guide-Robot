"""Headless tests for Faculties page CSV import/export actions."""

import csv
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from database.init_db import initialize_database
from database.repositories.faculty_repository import create_faculty, get_all_faculties
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


def test_faculties_page_has_csv_buttons(tmp_path) -> None:
    """Confirm the clean toolbar exposes upload and export without clear/reload."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    try:
        assert application is not None
        assert page.upload_faculties_csv_button is not None
        assert page.export_faculties_csv_button is not None
        assert not hasattr(page, "clear_faculties_csv_button")
        assert not hasattr(page, "import_faculties_csv_button")
    finally:
        page.close()


def test_faculties_page_upload_csv_automatically_imports_rows(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm Upload immediately imports into SQLite and reloads the table."""
    db_path = _create_temp_db(tmp_path)
    csv_path = tmp_path / "faculties.csv"
    csv_path.write_text(
        "name,description,building,dean_name\n"
        "Engineering,Engineering programs,Building A,Dean One\n",
        encoding="utf-8",
    )
    application = _get_application()
    page = FacultiesPage(db_path)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(csv_path), "CSV Files (*.csv)"),
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    try:
        assert application is not None
        page.upload_csv()

        assert page.faculties_table.rowCount() == 1
        assert page.faculties_table.item(0, 1).text() == "Engineering"
        assert [faculty["name"] for faculty in get_all_faculties(db_path)] == [
            "Engineering"
        ]
    finally:
        page.close()


def test_faculties_page_export_csv_writes_file(tmp_path, monkeypatch) -> None:
    """Confirm the Export action creates a CSV containing current faculty data."""
    db_path = _create_temp_db(tmp_path)
    create_faculty("Engineering", db_path=db_path)
    output_path = tmp_path / "faculty_export"
    application = _get_application()
    page = FacultiesPage(db_path)
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(output_path), "CSV Files (*.csv)"),
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    try:
        assert application is not None
        page.export_csv()

        exported_path = tmp_path / "faculty_export.csv"
        assert exported_path.is_file()
        assert "Engineering" in exported_path.read_text(encoding="utf-8-sig")
        with exported_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            assert next(csv.reader(csv_file)) == [
                "id",
                "name",
                "description",
                "building",
                "dean_name",
            ]
    finally:
        page.close()


def test_faculties_page_upload_csv_cancel_does_nothing(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm cancelling the upload chooser leaves the page unchanged."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: ("", ""),
    )
    try:
        assert application is not None
        page.upload_csv()
        assert page.faculties_table.rowCount() == 0
    finally:
        page.close()


def test_faculties_page_export_csv_cancel_does_nothing(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm cancelling the export chooser creates no output file."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: ("", ""),
    )
    try:
        assert application is not None
        page.export_csv()
        assert list(tmp_path.glob("*.csv")) == []
    finally:
        page.close()


def test_faculties_page_toolbar_button_order(tmp_path) -> None:
    """Confirm the four visible toolbar actions use the requested left-to-right order."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = FacultiesPage(db_path)
    try:
        assert application is not None
        visible_button_names = [
            page.faculties_toolbar_layout.itemAt(index).widget().objectName()
            for index in range(4)
        ]
        assert visible_button_names == [
            "upload_faculties_csv_button",
            "delete_faculty_button",
            "export_faculties_csv_button",
            "save_faculties_table_button",
        ]
    finally:
        page.close()
