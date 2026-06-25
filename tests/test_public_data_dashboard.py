"""Headless tests for the unified public Data Management screen."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QPushButton,
    QTableWidget,
)

from database.init_db import initialize_database
from ui.public.main_window import PublicMainWindow
from ui.public.screens.data_dashboard_screen import DataDashboardScreen


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _create_temp_db(tmp_path):
    """Initialize and return an isolated database path for one test."""
    db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(db_path)
    return db_path


def test_data_dashboard_screen_can_be_created(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        assert screen.objectName() == "data_dashboard_screen"
    finally:
        screen.close()


def test_required_widgets_exist(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        for object_name, widget_type in (
            ("data_dataset_selector", QComboBox),
            ("data_table", QTableWidget),
            ("data_status_label", QLabel),
            ("data_upload_csv_button", QPushButton),
            ("data_delete_row_button", QPushButton),
            ("data_export_csv_button", QPushButton),
            ("data_save_edits_button", QPushButton),
        ):
            assert screen.findChild(widget_type, object_name) is not None
    finally:
        screen.close()


def test_dataset_selector_contains_required_datasets(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        selector = screen.data_dataset_selector
        assert [selector.itemText(index) for index in range(selector.count())] == [
            "Faculties",
            "Rooms",
            "Professors",
            "Courses",
            "Events",
            "FAQ",
        ]
    finally:
        screen.close()


def test_selecting_each_dataset_loads_table_without_crashing(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        for dataset in ("Faculties", "Rooms", "Professors", "Courses", "Events", "FAQ"):
            screen.data_dataset_selector.setCurrentText(dataset)
            screen.load_selected_dataset()
            assert screen.data_table.columnCount() >= 1
    finally:
        screen.close()


def test_action_buttons_exist_in_required_order(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        buttons = (
            screen.data_upload_csv_button,
            screen.data_delete_row_button,
            screen.data_export_csv_button,
            screen.data_save_edits_button,
        )
        assert [button.text() for button in buttons] == [
            "Upload CSV",
            "Delete Selected Row",
            "Export CSV",
            "Save Edits",
        ]
    finally:
        screen.close()


def test_admin_gate_correct_password_switches_to_data_dashboard() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.show_data()
        window.admin_gate_screen.admin_password_input.setText("admin123")
        window.admin_gate_screen.admin_unlock_button.click()
        assert window.public_page_stack.currentIndex() == 8
        assert window.public_page_stack.currentWidget() is window.data_dashboard_screen
    finally:
        window.close()


def test_public_navigation_still_works_after_adding_data_dashboard() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.show_data_dashboard()
        assert window.public_page_stack.currentIndex() == 8
        window.sidebar_map_button.click()
        assert window.public_page_stack.currentIndex() == 1
        window.sidebar_home_button.click()
        assert window.public_page_stack.currentIndex() == 0
        window.floating_ask_button.click()
        assert window.public_page_stack.currentIndex() == 6
    finally:
        window.close()
