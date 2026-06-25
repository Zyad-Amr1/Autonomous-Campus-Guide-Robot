"""Headless tests for the public dashboard Home screen layout."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSizePolicy

from ui.public.main_window import PublicMainWindow
from ui.public.screens.home_screen import HomeScreen


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
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
        assert screen.home_welcome_title.text() == "Welcome to ECU Smart Assistant"
        assert (
            screen.home_welcome_subtitle.text()
            == "Find your way, ask questions, and explore university information."
        )
        for object_name, widget_type in (
            ("home_welcome_title", QLabel),
            ("home_welcome_subtitle", QLabel),
            ("home_map_tile", QPushButton),
            ("home_chat_tile", QPushButton),
            ("home_info_tile", QPushButton),
            ("home_staff_tile", QPushButton),
            ("home_schedule_tile", QPushButton),
            ("home_news_tile", QPushButton),
            ("home_about_tile", QPushButton),
        ):
            assert screen.findChild(widget_type, object_name) is not None
    finally:
        screen.close()


def test_home_screen_main_tiles_are_touch_friendly() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        for tile in (
            screen.home_map_tile,
            screen.home_chat_tile,
            screen.home_info_tile,
        ):
            assert tile.minimumHeight() >= 100
            assert (
                tile.sizePolicy().horizontalPolicy()
                == QSizePolicy.Policy.Expanding
            )
    finally:
        screen.close()


def test_public_main_window_index_zero_is_home_screen() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert isinstance(window.public_page_stack.widget(0), HomeScreen)
        assert window.public_page_stack.currentIndex() == 0
    finally:
        window.close()


def test_home_tile_navigation_uses_existing_public_pages() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.home_screen.home_map_tile.click()
        assert window.public_page_stack.currentIndex() == 1
        window.show_home()
        window.home_screen.home_chat_tile.click()
        assert window.public_page_stack.currentIndex() == 6
        window.show_home()
        window.home_screen.home_staff_tile.click()
        assert window.public_page_stack.currentIndex() == 2
    finally:
        window.close()


def test_existing_navigation_still_works_with_home_screen() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.sidebar_schedule_button.click()
        assert window.public_page_stack.currentIndex() == 3
        window.floating_ask_button.click()
        assert window.public_page_stack.currentIndex() == 6
        window.sidebar_home_button.click()
        assert window.public_page_stack.currentIndex() == 0
    finally:
        window.close()
