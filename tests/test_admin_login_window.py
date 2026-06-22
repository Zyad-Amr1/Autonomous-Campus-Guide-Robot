"""Lightweight widget tests for the Admin Panel login layout."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton

from ui.admin.login_window import LoginWindow


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_login_window_can_be_imported_and_instantiated() -> None:
    """Confirm the Admin Login Window is constructible with its title."""
    application = _get_application()
    window = LoginWindow()
    try:
        assert application is not None
        assert window.windowTitle() == "ECU Robot Admin Panel - Login"
    finally:
        window.close()


def test_login_window_contains_required_controls() -> None:
    """Confirm all controls needed by the future authentication step exist."""
    application = _get_application()
    window = LoginWindow()
    try:
        assert application is not None
        assert window.findChild(QLineEdit, "username_input") is window.username_input
        assert window.findChild(QLineEdit, "password_input") is window.password_input
        assert window.password_input.echoMode() == QLineEdit.EchoMode.Password
        assert window.findChild(QPushButton, "login_button") is window.login_button
        assert window.login_button.text() == "Login"
        assert window.findChild(QLabel, "error_label") is window.error_label
    finally:
        window.close()
