"""Headless tests for the public language onboarding screen."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton

from ui.public.main_window import PublicMainWindow
from ui.public.screens.home_screen import HomeScreen
from ui.public.screens.language_screen import LanguageSelectionScreen


def _get_application() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_language_screen_exists() -> None:
    application = _get_application()
    screen = LanguageSelectionScreen()
    try:
        assert application is not None
        assert screen.objectName() == "language_screen"
        assert screen.findChild(QPushButton, "choose_english_button") is not None
        assert screen.findChild(QPushButton, "choose_arabic_button") is not None
    finally:
        screen.close()


def test_public_app_starts_on_language_screen() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert isinstance(window.public_page_stack.widget(0), LanguageSelectionScreen)
        assert isinstance(window.public_page_stack.widget(1), HomeScreen)
        assert window.public_page_stack.currentIndex() == 0
        assert window.sidebar.isHidden()
        assert window.header.isHidden()
    finally:
        window.close()


def test_english_button_goes_to_home_in_english() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.language_screen.choose_english_button.click()
        assert window.current_language == "en"
        assert window.layoutDirection() == Qt.LayoutDirection.LeftToRight
        assert window.public_page_stack.currentIndex() == 1
        assert window.home_screen.home_info_card.text().startswith(
            "University Information"
        )
    finally:
        window.close()


def test_arabic_button_goes_to_home_in_arabic_and_rtl() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.language_screen.choose_arabic_button.click()
        assert window.current_language == "ar"
        assert window.layoutDirection() == Qt.LayoutDirection.RightToLeft
        assert window.public_page_stack.currentIndex() == 1
        assert window.home_screen.layoutDirection() == Qt.LayoutDirection.RightToLeft
        assert window.home_screen.home_info_card.text().startswith("معلومات الجامعة")
    finally:
        window.close()
