"""Tests for the ECU Robot Admin Panel authentication repository."""

from database.init_db import initialize_database
from database.repositories.admin_repository import (
    authenticate_admin,
    get_admin_by_username,
    verify_password,
)


def test_get_admin_by_username_returns_default_admin(tmp_path) -> None:
    """Confirm the seeded administrator can be retrieved by username."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    admin = get_admin_by_username("admin", temp_db_path)

    assert admin is not None
    assert admin["username"] == "admin"
    assert admin["full_name"] == "System Administrator"
    assert admin["role"] == "super_admin"


def test_get_admin_by_username_returns_none_for_unknown_user(tmp_path) -> None:
    """Confirm an unknown username does not produce an admin record."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    assert get_admin_by_username("unknown", temp_db_path) is None


def test_verify_password_accepts_correct_password(tmp_path) -> None:
    """Confirm the seeded administrator's correct password is accepted."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)
    admin = get_admin_by_username("admin", temp_db_path)

    assert admin is not None
    assert verify_password("admin123", admin["password_hash"]) is True


def test_verify_password_rejects_wrong_password(tmp_path) -> None:
    """Confirm an incorrect password is rejected securely."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)
    admin = get_admin_by_username("admin", temp_db_path)

    assert admin is not None
    assert verify_password("wrong-password", admin["password_hash"]) is False


def test_verify_password_returns_false_for_invalid_hash() -> None:
    """Confirm malformed stored hashes fail authentication without exceptions."""
    assert verify_password("admin123", "invalid-hash-format") is False


def test_authenticate_admin_returns_safe_admin_dict_for_valid_credentials(
    tmp_path,
) -> None:
    """Confirm valid credentials return profile data without the password hash."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    admin = authenticate_admin("admin", "admin123", temp_db_path)

    assert admin is not None
    assert admin["username"] == "admin"
    assert admin["role"] == "super_admin"
    assert "password_hash" not in admin


def test_authenticate_admin_returns_none_for_wrong_password(tmp_path) -> None:
    """Confirm authentication fails when the password is incorrect."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    assert authenticate_admin("admin", "wrong-password", temp_db_path) is None


def test_authenticate_admin_returns_none_for_unknown_user(tmp_path) -> None:
    """Confirm authentication fails when the username does not exist."""
    temp_db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(temp_db_path)

    assert authenticate_admin("unknown", "admin123", temp_db_path) is None
