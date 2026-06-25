"""Headless tests for public sidebar placeholder navigation."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QStackedWidget

from ui.public.main_window import PublicMainWindow
from ui.public.screens.placeholder_page import PlaceholderPage


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_public_main_window_has_page_stack() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        stack = window.findChild(QStackedWidget, "public_page_stack")
        assert stack is not None
        assert stack.count() == 9
    finally:
        window.close()


def test_public_navigation_starts_on_home() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert window.public_page_stack.currentIndex() == 0
    finally:
        window.close()


def test_public_navigation_methods_switch_pages() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        navigation = (
            (window.show_home, 0),
            (window.show_map, 1),
            (window.show_staff, 2),
            (window.show_schedule, 3),
            (window.show_news, 4),
            (window.show_about, 5),
            (window.show_chat, 6),
        )
        for method, expected_index in navigation:
            method()
            assert window.public_page_stack.currentIndex() == expected_index
    finally:
        window.close()


def test_sidebar_buttons_are_connected_to_navigation() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        navigation = (
            (window.sidebar_map_button, 1),
            (window.sidebar_staff_button, 2),
            (window.sidebar_schedule_button, 3),
            (window.sidebar_news_button, 4),
            (window.sidebar_about_button, 5),
            (window.sidebar_chat_button, 6),
            (window.sidebar_home_button, 0),
        )
        for button, expected_index in navigation:
            button.click()
            assert window.public_page_stack.currentIndex() == expected_index
    finally:
        window.close()


def test_placeholder_pages_have_required_labels() -> None:
    application = _get_application()
    page = PlaceholderPage("Campus Map", "Future navigation", "◇")
    try:
        assert application is not None
        for object_name in (
            "placeholder_icon_label",
            "placeholder_title_label",
            "placeholder_subtitle_label",
            "placeholder_message_label",
        ):
            assert page.findChild(QLabel, object_name) is not None
    finally:
        page.close()


def test_public_app_still_imports() -> None:
    import apps.public_app

    assert apps.public_app.PublicMainWindow is PublicMainWindow
