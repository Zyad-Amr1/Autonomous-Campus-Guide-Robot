"""Headless tests for Home screen tile navigation."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui.public.main_window import PublicMainWindow
from ui.public.screens.home_screen import HomeScreen


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_map_tile_switches_to_map_page() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.home_screen.home_map_tile.click()
        assert window.public_page_stack.currentIndex() == 1
    finally:
        window.close()


def test_chat_tile_switches_to_chat_page() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.home_screen.home_chat_tile.click()
        assert window.public_page_stack.currentIndex() == 6
    finally:
        window.close()


def test_staff_tile_switches_to_staff_page() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.home_screen.home_staff_tile.click()
        assert window.public_page_stack.currentIndex() == 2
    finally:
        window.close()


def test_schedule_tile_switches_to_schedule_page() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.home_screen.home_schedule_tile.click()
        assert window.public_page_stack.currentIndex() == 3
    finally:
        window.close()


def test_news_tile_switches_to_news_page() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.home_screen.home_news_tile.click()
        assert window.public_page_stack.currentIndex() == 4
    finally:
        window.close()


def test_about_and_info_tiles_switch_to_about_page() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.home_screen.home_info_tile.click()
        assert window.public_page_stack.currentIndex() == 5
        window.show_home()
        window.home_screen.home_about_tile.click()
        assert window.public_page_stack.currentIndex() == 5
    finally:
        window.close()


def test_home_screen_without_parent_window_tile_clicks_do_not_crash() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        for tile in (
            screen.home_map_tile,
            screen.home_chat_tile,
            screen.home_info_tile,
            screen.home_staff_tile,
            screen.home_schedule_tile,
            screen.home_news_tile,
            screen.home_about_tile,
        ):
            tile.click()
    finally:
        screen.close()
