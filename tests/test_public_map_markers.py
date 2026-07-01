"""Headless tests for public map canvas database marker rendering."""

import os
import sqlite3

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import QApplication

from database.init_db import initialize_database
from database.repositories.room_repository import create_room
from ui.public.screens.map_screen import MapCanvas, MapScreen


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _create_temp_db(tmp_path):
    """Initialize and return an isolated database path for one test."""
    db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(db_path)
    return db_path


def _render_canvas(canvas: MapCanvas) -> None:
    """Render once so the canvas computes its current image target rectangle."""
    if canvas.width() <= 0 or canvas.height() <= 0:
        canvas.resize(800, 560)
    target = QPixmap(canvas.width(), canvas.height())
    target.fill(QColor("white"))
    painter = QPainter(target)
    try:
        canvas.render(painter, QPoint(0, 0))
    finally:
        painter.end()


def _click_canvas(canvas: MapCanvas, point: QPointF) -> None:
    """Send a left-click directly to the map canvas."""
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        point,
        point,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    canvas.mousePressEvent(event)


def test_map_canvas_has_set_markers_method() -> None:
    application = _get_application()
    canvas = MapCanvas()
    try:
        assert application is not None
        assert hasattr(canvas, "set_markers")
    finally:
        canvas.close()


def test_set_markers_stores_valid_markers() -> None:
    application = _get_application()
    canvas = MapCanvas()
    marker = {
        "id": 1,
        "title": "Room D101",
        "room_name": "Room D101",
        "category": "Lab",
        "x_coord": "0.45",
        "y_coord": 0.62,
        "description": "Robotics lab.",
    }
    try:
        assert application is not None
        canvas.set_markers([marker])
        assert len(canvas.database_markers) == 1
        assert canvas.markers == canvas.database_markers
        assert canvas.database_markers[0]["title"] == "Room D101"
        assert canvas.database_markers[0]["x_coord"] == 0.45
        assert canvas.database_markers[0]["y_coord"] == 0.62
    finally:
        canvas.close()


def test_set_markers_accepts_calibrated_map_coordinates() -> None:
    application = _get_application()
    canvas = MapCanvas()
    marker = {
        "title": "Room D101",
        "category": "Lab",
        "x_coord": 880,
        "y_coord": 170,
    }
    try:
        assert application is not None
        canvas.set_markers([marker])
        assert len(canvas.database_markers) == 1
        assert canvas.database_markers[0]["x_coord"] == 0.88
        assert canvas.database_markers[0]["y_coord"] == 0.17
    finally:
        canvas.close()


def test_set_markers_skips_markers_missing_coordinates() -> None:
    application = _get_application()
    canvas = MapCanvas()
    markers = [
        {"title": "Missing X", "y_coord": 0.4},
        {"title": "Missing Y", "x_coord": 0.4},
        {"title": "Bad X", "x_coord": "east", "y_coord": 0.4},
        {"title": "Out Of Range", "x_coord": 1.2, "y_coord": 0.4},
        {"title": "Zero Origin", "x_coord": 0, "y_coord": 0},
        {"title": "Valid Room", "x_coord": 0.4, "y_coord": 0.5},
    ]
    try:
        assert application is not None
        canvas.set_markers(markers)
        assert [marker["title"] for marker in canvas.database_markers] == ["Valid Room"]
    finally:
        canvas.close()


def test_set_markers_handles_none_safely() -> None:
    application = _get_application()
    canvas = MapCanvas()
    try:
        assert application is not None
        canvas.set_markers(None)
        assert canvas.database_markers == []
        assert canvas.markers == []
    finally:
        canvas.close()


def test_marker_category_colors_are_consistent() -> None:
    application = _get_application()
    canvas = MapCanvas()
    try:
        assert application is not None
        assert canvas.marker_color("Library") == canvas.marker_color("library")
        assert canvas.marker_color("Offices") == canvas.marker_color("office")
        assert canvas.marker_color("Lab") == canvas.marker_color("Labs")
        assert canvas.marker_color("Classroom") == canvas.marker_color("classrooms")
        assert canvas.marker_color("Service") == canvas.marker_color("Student Services")
        assert canvas.marker_color("Other") == canvas.marker_color("Unknown")
        assert canvas.marker_color("Lab") != canvas.marker_color("Other")
    finally:
        canvas.close()


def test_paint_render_path_does_not_crash_with_markers() -> None:
    application = _get_application()
    canvas = MapCanvas()
    canvas.resize(800, 560)
    canvas.set_markers(
        [
            {"title": "Room D101", "category": "Lab", "x_coord": 0.45, "y_coord": 0.62},
            {"room_name": "Library", "category": "Library", "x_coord": 0.28, "y_coord": 0.33},
            {"category": "Other", "x_coord": 0.66, "y_coord": 0.48},
        ]
    )
    target = QPixmap(800, 560)
    target.fill(QColor("white"))
    painter = QPainter(target)
    try:
        assert application is not None
        canvas.render(painter, QPoint(0, 0))
    finally:
        painter.end()
        canvas.close()


def test_map_screen_accepts_db_path_argument(tmp_path) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    screen = MapScreen(db_path=db_path)
    try:
        assert application is not None
        assert screen.db_path == db_path
    finally:
        screen.close()


def test_map_screen_loads_rooms_with_coordinates(tmp_path) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    create_room(
        "Robotics Lab",
        "D101",
        "Building D",
        1,
        "Lab",
        "Robotics workspace.",
        x_coord=0.45,
        y_coord=0.62,
        db_path=db_path,
    )
    screen = MapScreen(db_path=db_path)
    try:
        assert application is not None
        assert len(screen.map_canvas.markers) == 1
        marker = screen.map_canvas.markers[0]
        assert marker["id"] is not None
        assert marker["title"] == "Robotics Lab"
        assert marker["room_name"] == "Robotics Lab"
        assert marker["room_number"] == "D101"
        assert marker["building"] == "Building D"
        assert marker["floor"] == 1
        assert marker["category"] == "Lab"
        assert marker["description"] == "Robotics workspace."
        assert marker["x_coord"] == 0.45
        assert marker["y_coord"] == 0.62
        assert marker["raw"]["room_number"] == "D101"
    finally:
        screen.close()


def test_map_screen_skips_rooms_without_coordinates(tmp_path) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    create_room(
        "Mapped Office",
        "A201",
        "Building A",
        2,
        "Offices",
        x_coord=0.3,
        y_coord=0.4,
        db_path=db_path,
    )
    create_room(
        "Unmapped Office",
        "A202",
        "Building A",
        2,
        "Offices",
        db_path=db_path,
    )
    screen = MapScreen(db_path=db_path)
    try:
        assert application is not None
        assert [marker["room_name"] for marker in screen.map_canvas.markers] == [
            "Mapped Office"
        ]
    finally:
        screen.close()


def test_map_screen_skips_invalid_coordinate_values(tmp_path) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    create_room(
        "Valid Room",
        "C103",
        "Building C",
        1,
        "Classroom",
        x_coord=0.25,
        y_coord=0.35,
        db_path=db_path,
    )
    create_room(
        "Out Of Range",
        "C999",
        "Building C",
        1,
        "Classroom",
        x_coord=1.4,
        y_coord=0.35,
        db_path=db_path,
    )
    create_room(
        "Bad Coordinate",
        "C998",
        "Building C",
        1,
        "Classroom",
        x_coord="bad",
        y_coord=0.35,
        db_path=db_path,
    )
    screen = MapScreen(db_path=db_path)
    try:
        assert application is not None
        assert [marker["room_name"] for marker in screen.map_canvas.markers] == [
            "Valid Room"
        ]
    finally:
        screen.close()


def test_empty_rooms_table_does_not_crash(tmp_path) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    screen = MapScreen(db_path=db_path)
    try:
        assert application is not None
        assert screen.map_canvas.markers == []
    finally:
        screen.close()


def test_missing_rooms_table_does_not_crash(tmp_path) -> None:
    application = _get_application()
    db_path = tmp_path / "missing_rooms_table.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
    screen = MapScreen(db_path=db_path)
    try:
        assert application is not None
        assert screen.map_canvas.markers == []
    finally:
        screen.close()


def test_map_canvas_receives_loaded_markers(tmp_path, monkeypatch) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    create_room(
        "Admissions Office",
        "S101",
        "Student Center",
        1,
        "Offices",
        x_coord=0.62,
        y_coord=0.48,
        db_path=db_path,
    )
    received_markers = {}
    original_set_markers = MapCanvas.set_markers

    def capture_set_markers(self, markers):
        received_markers["markers"] = markers
        original_set_markers(self, markers)

    monkeypatch.setattr(MapCanvas, "set_markers", capture_set_markers)
    screen = MapScreen(db_path=db_path)
    try:
        assert application is not None
        assert len(received_markers["markers"]) == 1
        assert received_markers["markers"][0]["room_name"] == "Admissions Office"
        assert screen.map_canvas.markers[0]["room_number"] == "S101"
    finally:
        screen.close()


def test_clicking_database_marker_updates_selected_marker_state() -> None:
    application = _get_application()
    canvas = MapCanvas()
    marker = {
        "title": "Room D101",
        "room_name": "Room D101",
        "room_number": "D101",
        "category": "Lab",
        "x_coord": 0.45,
        "y_coord": 0.62,
    }
    try:
        assert application is not None
        canvas.set_markers([marker])
        _render_canvas(canvas)
        _click_canvas(canvas, canvas._point_for_marker(canvas.markers[0]))
        assert canvas.selected_marker == canvas.markers[0]
        assert canvas.selected_marker_payload["type"] == "database_marker"
        assert canvas.selected_marker_payload["room_number"] == "D101"
    finally:
        canvas.close()


def test_clicking_database_marker_updates_map_screen_info_panel(tmp_path) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    create_room(
        "Room D101",
        "D101",
        "Building D",
        1,
        "Lab",
        "Robotics lab.",
        x_coord=0.45,
        y_coord=0.62,
        db_path=db_path,
    )
    screen = MapScreen(db_path=db_path)
    try:
        assert application is not None
        _render_canvas(screen.map_canvas)
        _click_canvas(screen.map_canvas, screen.map_canvas._point_for_marker(screen.map_canvas.markers[0]))
        assert screen.map_info_title.text() == "Room D101"
        assert screen.map_route_info_label.text() == "Selected room/location"
        details = screen.map_selected_place_label.text()
        assert "Room: D101" in details
        assert "Category: Lab" in details
        assert "Building: Building D" in details
        assert "Floor: 1" in details
        assert "Description: Robotics lab." in details
        assert screen.map_route_steps_label.text() == ""
        assert not screen.map_set_destination_button.isEnabled()
    finally:
        screen.close()


def test_marker_click_uses_rendered_canvas_coordinates_correctly() -> None:
    application = _get_application()
    canvas = MapCanvas()
    clicked_payload = {}
    marker = {
        "title": "Admissions Office",
        "room_number": "S101",
        "category": "Offices",
        "x_coord": 0.62,
        "y_coord": 0.48,
    }
    canvas.marker_clicked = clicked_payload.update
    try:
        assert application is not None
        canvas.set_markers([marker])
        canvas.resize(1024, 620)
        _render_canvas(canvas)
        point = canvas._point_for_marker(canvas.markers[0]) + QPointF(8, -6)
        _click_canvas(canvas, point)
        assert clicked_payload["type"] == "database_marker"
        assert clicked_payload["room_number"] == "S101"
    finally:
        canvas.close()


def test_marker_data_and_clicks_still_work_after_zoom() -> None:
    application = _get_application()
    canvas = MapCanvas()
    marker = {
        "title": "Zoomed Lab",
        "room_number": "Z101",
        "category": "Lab",
        "x_coord": 0.52,
        "y_coord": 0.44,
    }
    try:
        assert application is not None
        canvas.set_markers([marker])
        canvas.resize(1024, 620)
        canvas.zoom_in()
        canvas.zoom_in()
        _render_canvas(canvas)
        assert canvas.zoom_factor > 1.0
        assert canvas.markers[0]["title"] == "Zoomed Lab"

        _click_canvas(canvas, canvas._point_for_marker(canvas.markers[0]))
        assert canvas.selected_marker == canvas.markers[0]
        assert canvas.selected_marker_payload["room_number"] == "Z101"
    finally:
        canvas.close()


def test_clicking_empty_area_does_not_crash_or_select_marker() -> None:
    application = _get_application()
    canvas = MapCanvas()
    canvas.set_markers(
        [{"title": "Room D101", "category": "Lab", "x_coord": 0.45, "y_coord": 0.62}]
    )
    try:
        assert application is not None
        _render_canvas(canvas)
        _click_canvas(canvas, QPointF(30, 30))
        assert canvas.selected_marker is None
    finally:
        canvas.close()


def test_clicking_static_landmark_still_works() -> None:
    application = _get_application()
    canvas = MapCanvas()
    clicked = []
    canvas.landmark_clicked = clicked.append
    try:
        assert application is not None
        _render_canvas(canvas)
        _click_canvas(canvas, canvas._point_for_name("Cafeteria"))
        assert canvas.selected_landmark == "Cafeteria"
        assert clicked == ["Cafeteria"]
        assert canvas.selected_marker is None
    finally:
        canvas.close()


def test_clicking_each_static_landmark_hotspot_still_works() -> None:
    application = _get_application()
    canvas = MapCanvas()
    clicked = []
    canvas.landmark_clicked = clicked.append
    expected_landmarks = tuple(canvas.landmarks)
    try:
        assert application is not None
        _render_canvas(canvas)
        for landmark in expected_landmarks:
            _click_canvas(canvas, canvas._point_for_name(landmark))
            assert canvas.selected_landmark == landmark
            assert canvas.selected_marker is None
        assert clicked == list(expected_landmarks)
    finally:
        canvas.close()


def test_selected_database_marker_highlight_state_is_stored() -> None:
    application = _get_application()
    canvas = MapCanvas()
    markers = [
        {"id": 1, "title": "Room D101", "category": "Lab", "x_coord": 0.45, "y_coord": 0.62},
        {"id": 2, "title": "Room C103", "category": "Classroom", "x_coord": 0.35, "y_coord": 0.52},
    ]
    try:
        assert application is not None
        canvas.set_markers(markers)
        payload = canvas.select_marker(canvas.markers[1])
        assert canvas.selected_marker == canvas.markers[1]
        assert canvas._is_selected_marker(canvas.markers[1])
        assert not canvas._is_selected_marker(canvas.markers[0])
        assert payload["title"] == "Room C103"
    finally:
        canvas.close()


def test_missing_optional_marker_fields_do_not_crash_info_panel(tmp_path) -> None:
    application = _get_application()
    screen = MapScreen(db_path=tmp_path / "missing-marker-fields.db")
    marker = {"title": "Campus marker", "type": "database_marker", "raw": {}}
    try:
        assert application is not None
        screen._show_database_marker_details(marker)
        assert screen.map_info_title.text() == "Campus marker"
        assert screen.map_selected_place_label.text() == "No additional details available."
    finally:
        screen.close()
