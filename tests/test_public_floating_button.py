"""Headless tests for the persistent public Ask Me action."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from ui.public.main_window import PublicMainWindow


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_floating_ask_button_exists() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        button = window.findChild(QPushButton, "floating_ask_button")
        assert button is not None
        assert "Ask" in button.text()
    finally:
        window.close()


def test_floating_ask_button_is_touch_friendly() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        button = window.floating_ask_button
        assert button.minimumHeight() >= 56 or button.sizeHint().height() >= 56
        assert button.minimumWidth() >= 120 or button.sizeHint().width() >= 120
    finally:
        window.close()


def test_floating_ask_button_switches_to_chat() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert window.public_page_stack.currentIndex() == 0
        window.floating_ask_button.click()
        assert window.public_page_stack.currentIndex() == 6
    finally:
        window.close()


def test_floating_ask_button_remains_visible_after_navigation() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        for navigation in (window.show_map, window.show_chat, window.show_about):
            navigation()
            assert not window.floating_ask_button.isHidden()
    finally:
        window.close()
