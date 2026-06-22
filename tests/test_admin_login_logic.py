"""Headless UI tests for Admin Login Window authentication behavior."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from database.init_db import initialize_database
from ui.admin.login_window import LoginWindow


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_login_window_rejects_invalid_credentials(tmp_path) -> None:
    """Confirm failed login attempts display the expected inline error."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    application = _get_application()
    window = LoginWindow(db_path=database_path)
    try:
        assert application is not None
        window.username_input.setText("admin")
        window.password_input.setText("wrong-password")

        window.handle_login()

        assert window.current_admin is None
        assert window.error_label.text() == "Invalid username or password."
    finally:
        window.close()


def test_login_window_accepts_valid_credentials_without_exposing_password_hash(
    tmp_path,
    monkeypatch,
) -> None:
    """Confirm valid login stores safe admin data without blocking the test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    application = _get_application()
    window = LoginWindow(db_path=database_path)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    try:
        assert application is not None
        window.username_input.setText("admin")
        window.password_input.setText("admin123")

        window.handle_login()

        assert window.current_admin is not None
        assert window.current_admin["username"] == "admin"
        assert window.current_admin["role"] == "super_admin"
        assert "password_hash" not in window.current_admin
        assert window.error_label.text() == ""
    finally:
        window.close()
