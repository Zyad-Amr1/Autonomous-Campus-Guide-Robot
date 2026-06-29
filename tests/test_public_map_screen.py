"""Headless tests for the public campus map route screen."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QPushButton, QWidget

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
        assert canvas.map_image_path is None
        assert canvas.map_image_exists is False
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
            ("map_canvas", MapCanvas),
            ("map_search_input", QLineEdit),
            ("map_search_button", QPushButton),
            ("map_from_combo", QComboBox),
            ("map_to_combo", QComboBox),
            ("map_find_route_button", QPushButton),
            ("map_reset_route_button", QPushButton),
            ("map_zoom_in_button", QPushButton),
            ("map_zoom_out_button", QPushButton),
            ("map_reset_view_button", QPushButton),
            ("map_start_walk_button", QPushButton),
            ("map_pause_walk_button", QPushButton),
            ("map_reset_walk_button", QPushButton),
            ("map_selected_place_label", QLabel),
            ("map_route_info_label", QLabel),
            ("map_route_steps_label", QLabel),
            ("map_walk_status_label", QLabel),
            ("map_info_panel", QWidget),
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


def test_public_main_window_map_page_is_map_screen() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        assert isinstance(window.map_screen, MapScreen)
        assert window.public_page_stack.indexOf(window.map_screen) == 2
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
        assert canvas.resolved_background_image_path is None
        canvas.set_background_image(str(image_path))
        assert canvas.background_image_path == str(image_path)
        assert canvas.resolved_background_image_path == image_path
        assert canvas.map_image_path == str(image_path)
        assert canvas.map_image_exists is True
        assert canvas._background_pixmap.isNull() is False
        canvas.set_background_image(str(tmp_path / "missing.png"))
        assert canvas.background_image_path == str(tmp_path / "missing.png")
        assert canvas.resolved_background_image_path == tmp_path / "missing.png"
        assert canvas.map_image_exists is False
    finally:
        canvas.close()


def test_map_screen_resolves_default_image_path_from_project_root() -> None:
    application = _get_application()
    screen = MapScreen()
    expected_path = Path(__file__).resolve().parents[1] / "assets/maps/ecu_campus_map.png"
    try:
        assert application is not None
        assert screen.map_image_path == "assets/maps/ecu_campus_map.png"
        assert screen.map_canvas.background_image_path == "assets/maps/ecu_campus_map.png"
        assert screen.map_canvas.resolved_background_image_path == expected_path
        assert screen.map_canvas.map_image_path.endswith("assets\\maps\\ecu_campus_map.png") or (
            screen.map_canvas.map_image_path.endswith("assets/maps/ecu_campus_map.png")
        )
    finally:
        screen.close()


def test_show_map_switches_to_map_page() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.show_map()
        assert window.public_page_stack.currentIndex() == window.public_page_stack.indexOf(window.map_screen)
        assert window.public_page_stack.currentWidget() is window.map_screen
    finally:
        window.close()
