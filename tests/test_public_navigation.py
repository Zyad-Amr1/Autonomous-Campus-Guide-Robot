"""Headless tests for public kiosk navigation."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QStackedWidget

from ui.public.main_window import PublicMainWindow
from ui.public.screens.placeholder_page import PlaceholderPage


def _get_application() -> QApplication:
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
        assert stack.count() == 10
    finally:
        window.close()


def test_public_navigation_starts_on_language_selection() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert window.public_page_stack.currentIndex() == 0
    finally:
        window.close()


def test_public_navigation_methods_switch_pages_after_language() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.select_language("en")
        navigation = (
            (window.show_home, 1),
            (window.show_map, 2),
            (window.show_about, 3),
            (window.show_chat, 4),
            (window.show_staff, 5),
            (window.show_schedule, 6),
            (window.show_news, 7),
            (window.show_data, 8),
        )
        for method, expected_index in navigation:
            method()
            assert window.public_page_stack.currentIndex() == expected_index
    finally:
        window.close()


def test_sidebar_and_floating_buttons_are_available_after_language() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.select_language("en")
        assert not window.sidebar.isHidden()
        assert not window.header.isHidden()
        assert not window.floating_actions_widget.isHidden()
        window.sidebar_map_button.click()
        assert window.public_page_stack.currentIndex() == 2
        window.floating_ask_button.click()
        assert window.public_page_stack.currentIndex() == 4
        window.header_home_button.click()
        assert window.public_page_stack.currentIndex() == 1
    finally:
        window.close()


def test_placeholder_pages_have_required_labels() -> None:
    application = _get_application()
    page = PlaceholderPage("Campus Map", "Future navigation", "INFO")
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
