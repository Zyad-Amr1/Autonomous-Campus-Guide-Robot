"""Headless test for the safe login-success transition signal."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from database.init_db import initialize_database
from ui.admin.login_window import LoginWindow


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_login_window_emits_safe_admin_on_success(tmp_path) -> None:
    """Confirm valid login emits one safe payload for app-level navigation."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    application = _get_application()
    window = LoginWindow(db_path=database_path)
    emitted_admins: list[dict] = []
    window.login_successful.connect(emitted_admins.append)
    try:
        assert application is not None
        window.username_input.setText("admin")
        window.password_input.setText("admin123")

        window.handle_login()

        assert len(emitted_admins) == 1
        assert emitted_admins[0]["username"] == "admin"
        assert "password_hash" not in emitted_admins[0]
    finally:
        window.close()
