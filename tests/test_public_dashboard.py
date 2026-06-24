"""Headless tests for the standalone public robot dashboard shell."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from ui.public.main_window import PublicMainWindow
from ui.public.screens.home_screen import HomeScreen
from ui.public.screens.placeholder_screen import PlaceholderScreen


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_public_main_window_can_be_created() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert window.windowTitle() == "ECU Robot Assistant"
        assert window.objectName() == "public_main_window"
        assert window.public_page_stack.objectName() == "public_page_stack"
    finally:
        window.close()


def test_public_main_window_has_expected_pages() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert window.public_page_stack.count() == 9
    finally:
        window.close()


def test_home_screen_has_three_main_topics() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        assert isinstance(screen.map_button, QPushButton)
        assert isinstance(screen.chatbot_button, QPushButton)
        assert isinstance(screen.university_info_button, QPushButton)
    finally:
        screen.close()


def test_home_screen_has_secondary_quick_actions() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        for attribute in (
            "faculties_quick_button",
            "professors_quick_button",
            "courses_quick_button",
            "events_quick_button",
            "faq_quick_button",
        ):
            assert isinstance(getattr(screen, attribute), QPushButton)
    finally:
        screen.close()


def test_main_topic_buttons_are_large_enough_for_touch() -> None:
    application = _get_application()
    screen = HomeScreen()
    try:
        assert application is not None
        assert screen.map_button.minimumHeight() >= 56
        assert screen.chatbot_button.minimumHeight() >= 56
        assert screen.university_info_button.minimumHeight() >= 56
    finally:
        screen.close()


def test_navigation_methods_switch_pages() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        navigation = (
            (window.show_map, 1),
            (window.show_chatbot, 2),
            (window.show_university_info, 3),
            (window.show_faculties, 4),
            (window.show_professors, 5),
            (window.show_courses, 6),
            (window.show_events, 7),
            (window.show_faq, 8),
        )
        for method, expected_index in navigation:
            method()
            assert window.public_page_stack.currentIndex() == expected_index
        window.show_home()
        assert window.public_page_stack.currentIndex() == 0
    finally:
        window.close()


def test_home_and_placeholder_buttons_drive_navigation() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.home_screen.map_button.click()
        assert window.public_page_stack.currentIndex() == 1
        map_placeholder = window.public_page_stack.currentWidget()
        map_placeholder.back_home_button.click()
        assert window.public_page_stack.currentIndex() == 0

        window.home_screen.chatbot_button.click()
        assert window.public_page_stack.currentIndex() == 2
        window.show_home()
        window.home_screen.university_info_button.click()
        assert window.public_page_stack.currentIndex() == 3
    finally:
        window.close()


def test_placeholder_screen_has_back_home_button() -> None:
    application = _get_application()
    screen = PlaceholderScreen("Campus Map", "Find your destination.", "🗺️")
    try:
        assert application is not None
        assert isinstance(screen.back_home_button, QPushButton)
        assert screen.placeholder_title_label is not None
        assert screen.placeholder_subtitle_label is not None
        assert screen.placeholder_icon_label is not None
        assert screen.placeholder_message_label is not None
        screen.back_home_button.click()
    finally:
        screen.close()


def test_public_app_imports_without_admin_dependencies() -> None:
    import apps.public_app

    assert apps.public_app.PublicMainWindow is PublicMainWindow
