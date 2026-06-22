"""Tests for the controller bridging login UI and repository logic."""

from controllers.auth_controller import AuthController
from database.init_db import initialize_database


def test_auth_controller_login_accepts_valid_default_admin(tmp_path) -> None:
    """Confirm valid seeded credentials return only safe admin fields."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    controller = AuthController(database_path)

    admin = controller.login("admin", "admin123")

    assert admin is not None
    assert admin["username"] == "admin"
    assert admin["role"] == "super_admin"
    assert "password_hash" not in admin


def test_auth_controller_login_rejects_wrong_password(tmp_path) -> None:
    """Confirm the controller rejects an incorrect password."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    controller = AuthController(database_path)

    assert controller.login("admin", "wrong-password") is None


def test_auth_controller_login_rejects_unknown_user(tmp_path) -> None:
    """Confirm the controller rejects an unknown administrator."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    controller = AuthController(database_path)

    assert controller.login("unknown", "admin123") is None


def test_auth_controller_login_rejects_empty_fields(tmp_path) -> None:
    """Confirm incomplete credential forms are rejected before repository access."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    controller = AuthController(database_path)

    assert controller.login("", "admin123") is None
    assert controller.login("   ", "admin123") is None
    assert controller.login("admin", "") is None
