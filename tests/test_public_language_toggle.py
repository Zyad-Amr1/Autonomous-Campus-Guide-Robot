"""Focused tests for full public dashboard language toggling."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ui.public.main_window import PublicMainWindow
from ui.public.translations import TRANSLATIONS


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_language_toggle_updates_public_dashboard_text_and_direction() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert window.current_language == "en"
        assert window.layoutDirection() == Qt.LayoutDirection.LeftToRight
        assert window.language_toggle_button.text() == "العربية"
        assert window.header_home_button.text() == TRANSLATIONS["en"]["header_home"]
        assert window.floating_ask_button.text() == TRANSLATIONS["en"]["ask_me"]
        assert window.emergency_help_button.text() == TRANSLATIONS["en"]["help"]

        window.language_toggle_button.click()
        assert window.current_language == "ar"
        assert window.layoutDirection() == Qt.LayoutDirection.RightToLeft
        assert window.sidebar_map_button.text() == TRANSLATIONS["ar"]["map"]
        assert window.header_home_button.text() == TRANSLATIONS["ar"]["header_home"]
        assert window.home_screen.home_map_tile.text() == TRANSLATIONS["ar"]["home_tile_map"]
        assert window.map_screen.map_find_route_button.text() == TRANSLATIONS["ar"]["map_find_route"]
        assert window.admin_gate_screen.admin_unlock_button.text() == TRANSLATIONS["ar"]["admin_unlock"]

        window.language_toggle_button.click()
        assert window.current_language == "en"
        assert window.layoutDirection() == Qt.LayoutDirection.LeftToRight
        assert window.sidebar_map_button.text() == TRANSLATIONS["en"]["map"]
        assert window.header_home_button.text() == TRANSLATIONS["en"]["header_home"]
        assert window.home_screen.home_map_tile.text() == TRANSLATIONS["en"]["home_tile_map"]
        assert window.map_screen.map_find_route_button.text() == TRANSLATIONS["en"]["map_find_route"]
    finally:
        window.close()
