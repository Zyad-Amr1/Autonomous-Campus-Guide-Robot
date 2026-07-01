"""Headless tests for public campus map walking navigation."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QPushButton

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


def test_map_image_path_support_exists() -> None:
    application = _get_application()
    screen = MapScreen()
    expected_path = Path(__file__).resolve().parents[1] / "assets/maps/real_campus_map.jpg"
    try:
        assert application is not None
        assert screen.map_image_path == "assets/maps/real_campus_map.jpg"
        assert screen.map_canvas.background_image_path == "assets/maps/real_campus_map.jpg"
        assert screen.map_canvas.resolved_background_image_path == expected_path
    finally:
        screen.close()


def test_from_to_combo_boxes_contain_landmarks() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        from_items = {
            screen.map_from_combo.itemText(index)
            for index in range(screen.map_from_combo.count())
        }
        to_items = {
            screen.map_to_combo.itemText(index)
            for index in range(screen.map_to_combo.count())
        }
        for landmark in ("Building A", "Building B", "Cafeteria", "Parking", "Stadium"):
            assert landmark in from_items
            assert landmark in to_items
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


def test_walking_buttons_exist() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        assert screen.findChild(QPushButton, "map_start_walk_button") is not None
        assert screen.findChild(QPushButton, "map_pause_walk_button") is not None
        assert screen.findChild(QPushButton, "map_reset_walk_button") is not None
        assert screen.findChild(QLabel, "map_walk_status_label") is not None
    finally:
        screen.close()


def test_search_input_exists() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        assert screen.findChild(QLineEdit, "map_search_input") is not None
        assert screen.findChild(QPushButton, "map_search_button") is not None
    finally:
        screen.close()


def test_start_walk_without_route_shows_safe_message() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.start_walk()
        assert screen.is_walking is False
        assert screen.walk_timer.isActive() is False
        assert screen.map_walk_status_label.text() == "Choose a route first."
    finally:
        screen.close()


def test_start_walk_after_route_sets_walking_state() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.map_from_combo.setCurrentText("Building A")
        screen.map_to_combo.setCurrentText("Cafeteria")
        screen.find_route()
        screen.start_walk()
        assert screen.is_walking is True
        assert screen.walk_timer.isActive() is True
        assert screen.map_canvas.walking_progress == 0.0
        assert screen.map_walk_status_label.text() == "Walking to Cafeteria..."
    finally:
        screen.pause_walk()
        screen.close()


def test_pause_walk_pauses_walking_state() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.map_from_combo.setCurrentText("Building A")
        screen.map_to_combo.setCurrentText("Cafeteria")
        screen.find_route()
        screen.start_walk()
        screen.pause_walk()
        assert screen.is_walking is False
        assert screen.walk_timer.isActive() is False
        assert screen.map_walk_status_label.text() == "Walk paused."
    finally:
        screen.close()


def test_reset_walk_resets_walking_progress() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.map_from_combo.setCurrentText("Building A")
        screen.map_to_combo.setCurrentText("Cafeteria")
        screen.find_route()
        screen.start_walk()
        screen._advance_walk()
        assert screen.walking_progress > 0.0
        screen.reset_walk()
        assert screen.is_walking is False
        assert screen.walking_progress == 0.0
        assert screen.map_canvas.walking_progress == 0.0
    finally:
        screen.close()


def test_walking_progress_reaches_destination_safely() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.map_from_combo.setCurrentText("Building A")
        screen.map_to_combo.setCurrentText("Cafeteria")
        screen.find_route()
        screen.start_walk()
        for _ in range(40):
            screen._advance_walk()
        assert screen.is_walking is False
        assert screen.walk_timer.isActive() is False
        assert screen.walking_progress == 1.0
        assert screen.map_canvas.walking_progress == 1.0
        assert screen.map_walk_status_label.text() == "Arrived at Cafeteria"
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


def test_searching_cafeteria_selects_and_highlights_landmark() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.map_search_input.setText("Cafeteria")
        screen.search_landmark()
        assert screen.selected_landmark == "Cafeteria"
        assert screen.map_canvas.selected_landmark == "Cafeteria"
        assert screen.map_info_title.text() == "Cafeteria"
    finally:
        screen.close()


def test_searching_key_real_map_landmarks_selects_correct_hotspot() -> None:
    application = _get_application()
    screen = MapScreen()
    search_targets = (
        "Building A",
        "Cafeteria",
        "Parking",
        "Stadium",
        "Student Activity",
        "Boys\u2019 Musallah",
        "Girls\u2019 Musallah",
    )
    try:
        assert application is not None
        for landmark in search_targets:
            screen.map_search_input.setText(landmark)
            screen.search_landmark()
            assert screen.selected_landmark == landmark
            assert screen.map_canvas.selected_landmark == landmark
            assert screen.map_info_title.text() == landmark
    finally:
        screen.close()


def test_partial_search_selects_cafeteria() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.map_search_input.setText("caf")
        screen.search_landmark()
        assert screen.selected_landmark == "Cafeteria"
        assert screen.map_canvas.selected_landmark == "Cafeteria"
    finally:
        screen.close()


def test_selecting_marker_updates_selected_landmark() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.map_canvas.landmark_clicked("Parking")
        assert screen.selected_landmark == "Parking"
        assert screen.map_canvas.selected_landmark == "Parking"
        assert "Type/category:" in screen.map_selected_place_label.text()
    finally:
        screen.close()


def test_set_as_destination_updates_to_combo() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.select_landmark("Stadium")
        screen.set_selected_as_destination()
        assert screen.map_to_combo.currentText() == "Stadium"
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
        assert screen.map_canvas.route_start_pulse_active is False
        screen.map_from_combo.setCurrentText("Building A")
        screen.map_to_combo.setCurrentText("Cafeteria")
        screen.find_route()
        assert screen.current_route
        assert screen.current_route[0] == "Building A"
        assert screen.current_route[-1] == "Cafeteria"
        assert screen.map_canvas.current_route == screen.current_route
        assert screen.map_canvas.route_start_pulse_active is True
        route_info = screen.map_route_info_label.text()
        assert "From: Building A" in route_info
        assert "To: Cafeteria" in route_info
    finally:
        screen.close()


def test_route_start_pulse_updates_safely_when_route_exists() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        assert screen.map_canvas.route_start_pulse_active is False
        assert screen.map_canvas.pulse_phase == 0.0

        screen.map_from_combo.setCurrentText("Building A")
        screen.map_to_combo.setCurrentText("Cafeteria")
        screen.find_route()
        previous_phase = screen.map_canvas.pulse_phase
        screen.map_canvas._advance_route_start_pulse()

        assert screen.map_canvas.route_start_pulse_active is True
        assert screen.map_canvas.pulse_phase > previous_phase
    finally:
        screen.close()


def test_find_route_still_works_after_zoom() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.map_canvas.zoom_in()
        screen.map_canvas.zoom_in()
        screen.map_from_combo.setCurrentText("Building A")
        screen.map_to_combo.setCurrentText("Cafeteria")
        screen.find_route()
        assert screen.map_canvas.zoom_factor > 1.0
        assert screen.current_route[0] == "Building A"
        assert screen.current_route[-1] == "Cafeteria"
        assert screen.map_canvas.current_route == screen.current_route
        assert screen.map_canvas.route_start_pulse_active is True
    finally:
        screen.close()


def test_route_steps_are_generated_after_finding_route() -> None:
    application = _get_application()
    screen = MapScreen()
    try:
        assert application is not None
        screen.map_from_combo.setCurrentText("Building A")
        screen.map_to_combo.setCurrentText("Cafeteria")
        screen.find_route()
        steps = screen.findChild(QLabel, "map_route_steps_label")
        assert steps is not None
        assert "Start at Building A" in steps.text()
        assert "Arrive at Cafeteria" in steps.text()
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
        assert screen.map_canvas.route_start_pulse_active is True
        screen.reset_route()
        assert screen.current_route == []
        assert screen.map_canvas.current_route == []
        assert screen.map_canvas.route_start_pulse_active is False
        assert screen.map_canvas.pulse_phase == 0.0
        assert screen.map_route_steps_label.text() == ""
        assert screen.is_walking is False
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
