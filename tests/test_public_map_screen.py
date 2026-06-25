"""Headless tests for the public campus map screen."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QWidget

from ui.public.main_window import PublicMainWindow
from ui.public.screens.map_screen import MapCanvas, MapScreen


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_map_screen_can_be_created() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        assert screen.objectName() == "map_screen"
    finally:
        screen.close()


def test_map_canvas_can_be_created() -> None:
    application = _get_application()
    canvas = MapCanvas()
    try:
        assert application is not None
        assert canvas.objectName() == "map_canvas"
        assert canvas.background_image_path is None
    finally:
        canvas.close()


def test_map_screen_required_widgets_exist() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        for object_name, widget_type in (
            ("map_title", QLabel),
            ("map_subtitle", QLabel),
            ("map_search_input", QLineEdit),
            ("map_canvas", MapCanvas),
            ("map_info_panel", QWidget),
            ("map_info_title", QLabel),
        ):
            assert screen.findChild(widget_type, object_name) is not None
    finally:
        screen.close()


def test_map_canvas_exists() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        canvas = screen.findChild(MapCanvas, "map_canvas")
        assert canvas is not None
        assert canvas.minimumWidth() >= 600
        assert canvas.minimumHeight() >= 400
    finally:
        screen.close()


def test_filter_buttons_exist() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        for object_name in (
            "filter_all_button",
            "filter_labs_button",
            "filter_offices_button",
            "filter_clinics_button",
            "filter_library_button",
            "filter_cafeteria_button",
            "filter_other_button",
        ):
            assert screen.findChild(QPushButton, object_name) is not None
    finally:
        screen.close()


def test_search_input_exists_with_placeholder() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        search_input = screen.findChild(QLineEdit, "map_search_input")
        assert search_input is not None
        assert search_input.placeholderText() == "Search for a room, lab, office..."
    finally:
        screen.close()


def test_public_main_window_map_page_is_map_screen() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert isinstance(window.public_page_stack.widget(1), MapScreen)
    finally:
        window.close()


def test_map_canvas_supports_background_image_path(tmp_path) -> None:
    application = _get_application()
    canvas = MapCanvas()
    image_path = tmp_path / "campus-map.png"
    pixmap = QPixmap(24, 24)
    pixmap.fill(QColor("#0B2A52"))
    pixmap.save(str(image_path))
    try:
        assert application is not None
        assert canvas.background_image_path is None
        canvas.set_background_image(str(image_path))
        assert canvas.background_image_path == str(image_path)
        canvas.set_background_image(str(tmp_path / "missing.png"))
        assert canvas.background_image_path == str(tmp_path / "missing.png")
    finally:
        canvas.close()


def test_show_map_switches_to_map_page() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.show_map()
        assert window.public_page_stack.currentIndex() == 1
        assert window.public_page_stack.currentWidget() is window.map_screen
    finally:
        window.close()
