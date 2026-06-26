"""Headless tests for the public dashboard Home screen layout."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSizePolicy

from ui.public.main_window import PublicMainWindow
from ui.public.screens.home_screen import HomeScreen


def _get_application() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_home_screen_can_be_created() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        assert screen.objectName() == "public_home_screen"
    finally:
        screen.close()


def test_home_screen_has_required_object_names() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        assert screen.findChild(QLabel, "home_title") is not None
        assert screen.findChild(QLabel, "home_subtitle") is not None
        assert screen.findChild(QPushButton, "home_info_card") is not None
        assert screen.findChild(QPushButton, "home_chatbot_card") is not None
        assert screen.findChild(QPushButton, "home_map_card") is not None
    finally:
        screen.close()


def test_home_has_exactly_three_main_cards() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        cards = screen.findChildren(QPushButton)
        assert [card.objectName() for card in cards] == [
            "home_info_card",
            "home_chatbot_card",
            "home_map_card",
        ]
    finally:
        screen.close()


def test_home_cards_are_touch_friendly() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        for card in (
            screen.home_info_card,
            screen.home_chatbot_card,
            screen.home_map_card,
        ):
            assert card.minimumHeight() >= 240
            assert (
                card.sizePolicy().horizontalPolicy()
                == QSizePolicy.Policy.Expanding
            )
    finally:
        screen.close()


def test_public_main_window_index_one_is_home_screen() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert isinstance(window.public_page_stack.widget(1), HomeScreen)
        window.select_language("en")
        assert window.public_page_stack.currentIndex() == 1
    finally:
        window.close()


def test_home_card_navigation_uses_public_pages() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.select_language("en")
        window.home_screen.home_info_card.click()
        assert window.public_page_stack.currentIndex() == 3
        window.show_home()
        window.home_screen.home_chatbot_card.click()
        assert window.public_page_stack.currentIndex() == 4
        window.show_home()
        window.home_screen.home_map_card.click()
        assert window.public_page_stack.currentIndex() == 2
    finally:
        window.close()
