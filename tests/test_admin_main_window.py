"""Headless widget tests for the empty Admin Dashboard shell."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from database.init_db import initialize_database
from ui.admin.main_window import AdminMainWindow
from ui.admin.pages.dashboard_home_page import DashboardHomePage
from ui.admin.pages.faculties_page import FacultiesPage
from ui.admin.pages.professors_page import ProfessorsPage
from ui.admin.pages.rooms_page import RoomsPage


CURRENT_ADMIN = {
    "id": 1,
    "username": "admin",
    "full_name": "System Administrator",
    "role": "super_admin",
}

EXPECTED_NAVIGATION = {
    "dashboard_home": "nav_dashboard_home",
    "faculties": "nav_faculties",
    "professors": "nav_professors",
    "rooms": "nav_rooms",
    "courses": "nav_courses",
    "events": "nav_events",
    "faq": "nav_faq",
    "csv": "nav_csv",
    "logs": "nav_logs",
}


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_admin_main_window_contains_dashboard_shell(tmp_path) -> None:
    """Confirm the authenticated shell exposes all planned navigation pages."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    application = _get_application()
    window = AdminMainWindow(CURRENT_ADMIN, database_path)
    try:
        assert application is not None
        assert window.windowTitle() == "ECU Robot Admin Panel"
        assert window.page_stack is not None
        assert window.page_stack.count() == 9
        assert isinstance(window.page_stack.widget(0), DashboardHomePage)
        assert isinstance(window.page_stack.widget(1), FacultiesPage)
        assert isinstance(window.page_stack.widget(2), ProfessorsPage)
        assert isinstance(window.page_stack.widget(3), RoomsPage)
        assert set(window.nav_buttons) == set(EXPECTED_NAVIGATION)

        for key, object_name in EXPECTED_NAVIGATION.items():
            button = window.nav_buttons[key]
            assert isinstance(button, QPushButton)
            assert button.objectName() == object_name
            assert window.findChild(QPushButton, object_name) is button
    finally:
        window.close()


def test_admin_main_window_navigation_switches_placeholder_pages(tmp_path) -> None:
    """Confirm each sidebar button selects its matching placeholder page."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    application = _get_application()
    window = AdminMainWindow(CURRENT_ADMIN, database_path)
    try:
        assert application is not None
        for expected_index, key in enumerate(EXPECTED_NAVIGATION):
            window.nav_buttons[key].click()
            assert window.page_stack.currentIndex() == expected_index
    finally:
        window.close()
