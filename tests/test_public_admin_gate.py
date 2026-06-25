"""Headless tests for protected Data access in the public dashboard."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton

from ui.public.main_window import PublicMainWindow
from ui.public.screens.admin_gate_screen import AdminGateScreen
from ui.public.screens.data_dashboard_screen import DataDashboardScreen


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_sidebar_data_button_exists() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        button = window.findChild(QPushButton, "sidebar_data_button")
        assert button is not None
        assert "Data" in button.text()
    finally:
        window.close()


def test_clicking_data_opens_admin_gate_screen() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.sidebar_data_button.click()
        assert window.public_page_stack.currentIndex() == 7
        assert isinstance(window.public_page_stack.currentWidget(), AdminGateScreen)
    finally:
        window.close()


def test_admin_gate_form_widgets_exist() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.show_data()
        screen = window.public_page_stack.currentWidget()
        assert screen.findChild(QLineEdit, "admin_password_input") is not None
        assert screen.findChild(QPushButton, "admin_unlock_button") is not None
        assert screen.findChild(QLabel, "admin_gate_status_label") is not None
    finally:
        window.close()


def test_wrong_password_shows_error() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.show_data()
        window.admin_gate_screen.admin_password_input.setText("wrong")
        window.admin_gate_screen.admin_unlock_button.click()
        assert (
            window.admin_gate_screen.admin_gate_status_label.text()
            == "Incorrect password. Please try again."
        )
    finally:
        window.close()


def test_correct_password_shows_access_granted() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.show_data()
        window.admin_gate_screen.admin_password_input.setText("admin123")
        window.admin_gate_screen.admin_unlock_button.click()
        assert (
            window.admin_gate_screen.admin_gate_status_label.text()
            == "Access granted. Opening data dashboard."
        )
        assert isinstance(window.public_page_stack.currentWidget(), DataDashboardScreen)
    finally:
        window.close()


def test_public_navigation_still_works_with_data_gate() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.sidebar_data_button.click()
        assert window.public_page_stack.currentIndex() == 7
        window.sidebar_map_button.click()
        assert window.public_page_stack.currentIndex() == 1
        window.floating_ask_button.click()
        assert window.public_page_stack.currentIndex() == 6
        window.sidebar_home_button.click()
        assert window.public_page_stack.currentIndex() == 0
    finally:
        window.close()
