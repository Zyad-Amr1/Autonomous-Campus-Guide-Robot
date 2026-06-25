"""Headless tests for public dashboard language switching."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel

from ui.public.main_window import PublicMainWindow
from ui.public.translations import TRANSLATIONS


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_translations_module_imports_with_required_keys() -> None:
    required_keys = {
        "app_title",
        "app_subtitle",
        "home",
        "map",
        "staff",
        "schedule",
        "news",
        "about",
        "chat",
        "ask_me",
        "language_toggle",
        "placeholder_message",
    }

    assert set(TRANSLATIONS) == {"en", "ar"}
    for language in ("en", "ar"):
        assert required_keys <= set(TRANSLATIONS[language])
        for key in ("home", "map", "staff", "schedule", "news", "about", "chat"):
            assert f"placeholder_{key}_title" in TRANSLATIONS[language]
            assert f"placeholder_{key}_subtitle" in TRANSLATIONS[language]


def test_public_main_window_starts_in_english() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert window.current_language == "en"
        assert window.layoutDirection() == Qt.LayoutDirection.LeftToRight
        assert window.sidebar_home_button.text() == TRANSLATIONS["en"]["home"]
        assert window.language_toggle_button.text() == "العربية"
    finally:
        window.close()


def test_language_toggle_switches_between_arabic_and_english() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None

        window.language_toggle_button.click()
        assert window.current_language == "ar"
        assert window.layoutDirection() == Qt.LayoutDirection.RightToLeft
        assert window.sidebar_home_button.text() == TRANSLATIONS["ar"]["home"]
        assert window.sidebar_map_button.text() == TRANSLATIONS["ar"]["map"]
        assert window.language_toggle_button.text() == "English"

        window.language_toggle_button.click()
        assert window.current_language == "en"
        assert window.layoutDirection() == Qt.LayoutDirection.LeftToRight
        assert window.sidebar_home_button.text() == TRANSLATIONS["en"]["home"]
        assert window.sidebar_map_button.text() == TRANSLATIONS["en"]["map"]
        assert window.language_toggle_button.text() == "العربية"
    finally:
        window.close()


def test_page_labels_and_navigation_survive_language_toggle() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None

        window.show_map()
        assert window.public_page_stack.currentIndex() == 1
        window.language_toggle_button.click()
        assert window.public_page_stack.currentIndex() == 1
        assert window.sidebar_map_button.isChecked()

        title_label = window.public_page_stack.currentWidget().findChild(
            QLabel,
            "placeholder_title_label",
        )
        assert title_label is not None
        assert title_label.text() == TRANSLATIONS["ar"]["placeholder_map_title"]
        assert window.map_screen.map_title.text() == TRANSLATIONS["ar"]["map_title"]
        assert (
            window.home_screen.home_welcome_title.text()
            == TRANSLATIONS["ar"]["home_hero_title"]
        )

        window.sidebar_chat_button.click()
        assert window.public_page_stack.currentIndex() == 6
        window.floating_ask_button.click()
        assert window.public_page_stack.currentIndex() == 6
        window.sidebar_home_button.click()
        assert window.public_page_stack.currentIndex() == 0
    finally:
        window.close()
