"""Tests for the initial ECU Guidance Robot project structure."""

from apps import admin_app, public_app
from database import connection
from ui.shared import theme


def test_placeholder_modules_can_be_imported() -> None:
    """Confirm the current application and infrastructure modules are importable."""
    assert admin_app is not None
    assert public_app is not None
    assert connection is not None
    assert theme is not None


def test_database_name() -> None:
    """Confirm the planned shared database filename remains stable."""
    assert connection.DB_NAME == "ecu_robot.db"


def test_shared_theme_constants_exist() -> None:
    """Confirm all placeholder theme constants are available."""
    expected_constants = (
        "PRIMARY_COLOR",
        "SECONDARY_COLOR",
        "BACKGROUND_COLOR",
        "TEXT_COLOR",
    )

    for constant_name in expected_constants:
        assert hasattr(theme, constant_name)


def test_application_entry_points_are_callable() -> None:
    """Confirm both placeholder applications expose callable entry points."""
    assert callable(admin_app.main)
    assert callable(public_app.main)
