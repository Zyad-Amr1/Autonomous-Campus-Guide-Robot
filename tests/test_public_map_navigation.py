"""Headless tests for public campus map walking navigation."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QPushButton

from ui.public.screens.map_screen import MapScreen


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


def test_from_to_combo_boxes_exist() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        assert screen.findChild(QComboBox, "map_from_combo") is not None
        assert screen.findChild(QComboBox, "map_to_combo") is not None
    finally:
        screen.close()


def test_route_buttons_exist() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        assert screen.findChild(QPushButton, "map_find_route_button") is not None
        assert screen.findChild(QPushButton, "map_reset_route_button") is not None
    finally:
        screen.close()


def test_landmarks_include_key_places() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        for landmark in ("Building A", "Building B", "Cafeteria", "Parking", "Stadium"):
            assert landmark in screen.landmarks
    finally:
        screen.close()


def test_shortest_path_between_building_a_and_cafeteria() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        path = screen.shortest_path("Building A", "Cafeteria")
        assert path[0] == "Building A"
        assert path[-1] == "Cafeteria"
        assert len(path) >= 2
    finally:
        screen.close()


def test_find_route_updates_current_route() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.map_from_combo.setCurrentText("Building A")
        screen.map_to_combo.setCurrentText("Cafeteria")
        screen.find_route()
        assert screen.current_route
        assert screen.current_route[0] == "Building A"
        assert screen.current_route[-1] == "Cafeteria"
        assert screen.map_canvas.current_route == screen.current_route
        assert "Route: Building A" in screen.map_route_info_label.text()
    finally:
        screen.close()


def test_reset_clears_current_route() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.map_from_combo.setCurrentText("Building A")
        screen.map_to_combo.setCurrentText("Cafeteria")
        screen.find_route()
        screen.reset_route()
        assert screen.current_route == []
        assert screen.map_canvas.current_route == []
    finally:
        screen.close()


def test_missing_map_image_does_not_crash(tmp_path) -> None:
    application = _get_application()
    screen = MapScreen(map_image_path=str(tmp_path / "missing.png"))
    try:
        assert application is not None
        assert screen.map_canvas.background_image_path == str(tmp_path / "missing.png")
        assert screen.map_canvas.current_route == []
    finally:
        screen.close()
