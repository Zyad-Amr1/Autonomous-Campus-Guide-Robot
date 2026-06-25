"""Headless tests for database-backed public map markers."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

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


def test_temp_db_initializes(tmp_path) -> None:
    db_path = _create_temp_db(tmp_path)

    assert db_path.exists()


def test_rooms_with_coordinates_load_as_markers(tmp_path) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    create_room(
        "Robotics Lab",
        "E101",
        "Engineering",
        1,
        "Labs",
        x_coord=0.25,
        y_coord=0.35,
        db_path=db_path,
    )
    screen = MapScreen(db_path=db_path)
    try:
        assert application is not None
        assert len(screen.map_canvas.markers) == 1
        assert screen.map_canvas.markers[0]["room_name"] == "Robotics Lab"
    finally:
        screen.close()


def test_rooms_without_coordinates_are_skipped(tmp_path) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    create_room(
        "Mapped Office",
        "A201",
        "Administration",
        2,
        "Offices",
        x_coord=0.45,
        y_coord=0.55,
        db_path=db_path,
    )
    create_room(
        "Unmapped Office",
        "A202",
        "Administration",
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


def test_marker_category_colors_are_assigned() -> None:
    application = _get_application()
    canvas = MapCanvas()
    try:
        assert application is not None
        assert canvas.marker_color("Labs") == "#2F80ED"
        assert canvas.marker_color("Offices") == "#8E5CF7"
        assert canvas.marker_color("Clinics") == "#D94D45"
        assert canvas.marker_color("Library") == "#3BAA6B"
        assert canvas.marker_color("Cafeteria") == "#E67E22"
        assert canvas.marker_color("Unknown") == canvas.marker_color("Other")
    finally:
        canvas.close()


def test_selecting_marker_updates_selected_marker() -> None:
    application = _get_application()
    canvas = MapCanvas()
    marker = {
        "room_name": "Library",
        "room_number": "L100",
        "building": "Library",
        "floor": 1,
        "category": "Library",
        "description": "Main library",
        "x_coord": 0.5,
        "y_coord": 0.5,
    }
    try:
        assert application is not None
        canvas.set_markers([marker])
        canvas.select_marker(canvas.markers[0])
        assert canvas.selected_marker == marker
    finally:
        canvas.close()


def test_map_screen_info_panel_updates_when_marker_selected(tmp_path) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    create_room(
        "Admissions Office",
        "S101",
        "Student Center",
        1,
        "Offices",
        "Admissions support desk.",
        x_coord=0.62,
        y_coord=0.48,
        db_path=db_path,
    )
    screen = MapScreen(db_path=db_path)
    try:
        assert application is not None
        marker = screen.map_canvas.markers[0]
        screen.map_canvas.select_marker(marker)
        assert screen.map_canvas.selected_marker == marker
        assert screen.map_info_title.text() == "Admissions Office"
        details = screen.map_info_details.text()
        assert "Room number: S101" in details
        assert "Building: Student Center" in details
        assert "Floor: 1" in details
        assert "Category: Offices" in details
        assert "Admissions support desk." in details
    finally:
        screen.close()


def test_map_opens_safely_with_empty_db(tmp_path) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    screen = MapScreen(db_path=db_path)
    try:
        assert application is not None
        assert screen.map_canvas.markers == []
        assert screen.map_info_title.text() == "Select a place"
    finally:
        screen.close()
