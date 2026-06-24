"""Headless tests for the stable ECU public dashboard shell."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QPushButton,
    QStackedWidget,
)

from ui.public.main_window import PublicMainWindow


SIDEBAR_BUTTON_NAMES = (
    "sidebar_home_button",
    "sidebar_map_button",
    "sidebar_staff_button",
    "sidebar_schedule_button",
    "sidebar_news_button",
    "sidebar_about_button",
    "sidebar_chat_button",
)


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
        assert window.windowTitle() == "ECU Smart Assistant"
        assert window.objectName() == "public_main_window"
    finally:
        window.close()


def test_public_main_window_has_sidebar_and_content() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert window.findChild(QFrame, "public_shell_sidebar") is not None
        assert window.findChild(QStackedWidget, "public_page_stack") is not None
    finally:
        window.close()


def test_sidebar_has_expected_visual_buttons() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        for object_name in SIDEBAR_BUTTON_NAMES:
            assert window.findChild(QPushButton, object_name) is not None
    finally:
        window.close()


def test_sidebar_buttons_are_touch_friendly() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        for object_name in SIDEBAR_BUTTON_NAMES:
            button = window.findChild(QPushButton, object_name)
            assert button is not None
            assert button.minimumHeight() >= 56 or button.sizeHint().height() >= 56
    finally:
        window.close()


def test_shell_title_and_subtitle_exist() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        home_page = window.public_page_stack.widget(0)
        assert home_page.findChild(QLabel, "placeholder_title_label") is not None
        assert home_page.findChild(QLabel, "placeholder_subtitle_label") is not None
    finally:
        window.close()


def test_public_app_imports_without_admin_dependencies() -> None:
    import apps.public_app

    assert apps.public_app.PublicMainWindow is PublicMainWindow
