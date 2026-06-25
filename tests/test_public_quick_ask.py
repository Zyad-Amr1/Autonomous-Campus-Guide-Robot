"""Headless tests for public Home quick ask chips."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from ui.public.main_window import PublicMainWindow
from ui.public.screens.home_screen import HomeScreen


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_quick_ask_section_exists() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        assert screen.findChild(QWidget, "quick_ask_section") is not None
    finally:
        screen.close()


def test_all_quick_ask_chips_exist() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        for index, question in enumerate(HomeScreen.QUICK_ASK_QUESTIONS, start=1):
            chip = screen.findChild(QPushButton, f"quick_ask_chip_{index}")
            assert chip is not None
            assert chip.text() == question
    finally:
        screen.close()


def test_quick_ask_chips_are_touch_friendly() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        for index in range(1, 5):
            chip = screen.findChild(QPushButton, f"quick_ask_chip_{index}")
            assert chip is not None
            assert chip.minimumHeight() >= 56
    finally:
        screen.close()


def test_clicking_quick_ask_chip_switches_to_chat_and_stores_question() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert window.pending_chat_question is None

        window.home_screen.quick_ask_chip_2.click()

        assert window.public_page_stack.currentIndex() == 6
        assert (
            window.pending_chat_question
            == "How can I find my classroom?"
        )
    finally:
        window.close()


def test_each_quick_ask_chip_stores_its_question() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        for index, question in enumerate(HomeScreen.QUICK_ASK_QUESTIONS, start=1):
            window.show_home()
            getattr(window.home_screen, f"quick_ask_chip_{index}").click()
            assert window.public_page_stack.currentIndex() == 6
            assert window.pending_chat_question == question
    finally:
        window.close()


def test_home_screen_without_parent_window_quick_ask_clicks_do_not_crash() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        for index in range(1, 5):
            getattr(screen, f"quick_ask_chip_{index}").click()
    finally:
        screen.close()
