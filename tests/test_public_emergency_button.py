"""Headless tests for the persistent public emergency help action."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from ui.public.main_window import PublicMainWindow


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_emergency_help_button_exists() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        button = window.findChild(QPushButton, "emergency_help_button")
        assert button is not None
        assert button.text() == "🚨 Help"
    finally:
        window.close()


def test_emergency_help_button_is_touch_friendly() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        button = window.emergency_help_button
        assert button.minimumHeight() >= 56 or button.sizeHint().height() >= 56
        assert button.minimumWidth() >= 100 or button.sizeHint().width() >= 100
    finally:
        window.close()


def test_emergency_help_button_remains_visible_after_navigation() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        for navigation in (
            window.show_map,
            window.show_staff,
            window.show_schedule,
            window.show_news,
            window.show_about,
            window.show_chat,
            window.show_home,
        ):
            navigation()
            assert not window.emergency_help_button.isHidden()
    finally:
        window.close()


def test_emergency_help_button_opens_message_box(monkeypatch) -> None:
    application = _get_application()
    window = PublicMainWindow()
    calls = []

    def fake_information(parent, title, message):
        calls.append((parent, title, message))
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "information", fake_information)
    try:
        assert application is not None
        window.emergency_help_button.click()
        assert len(calls) == 1
        parent, title, message = calls[0]
        assert parent is window
        assert title == "Emergency Help"
        assert "Campus Security: 0000" in message
        assert "First Aid / Medical Help: 0000" in message
        assert "Student Affairs: 0000" in message
        assert "Please contact the nearest staff member" in message
    finally:
        window.close()


def test_navigation_still_works_after_emergency_button_exists() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.sidebar_map_button.click()
        assert window.public_page_stack.currentIndex() == 1
        window.floating_ask_button.click()
        assert window.public_page_stack.currentIndex() == 6
        window.sidebar_home_button.click()
        assert window.public_page_stack.currentIndex() == 0
        window.language_toggle_button.click()
        window.sidebar_about_button.click()
        assert window.public_page_stack.currentIndex() == 5
    finally:
        window.close()
