"""Headless tests for live Admin Dashboard summary cards."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from database.init_db import initialize_database
from database.repositories.course_repository import create_course
from database.repositories.event_repository import create_event
from database.repositories.faculty_repository import create_faculty
from database.repositories.faq_repository import create_faq
from database.repositories.log_repository import create_log
from database.repositories.professor_repository import create_professor
from database.repositories.room_repository import create_room
from ui.admin.pages.dashboard_home_page import DashboardHomePage


COUNT_LABEL_ATTRIBUTES = (
    "count_faculties_label",
    "count_professors_label",
    "count_rooms_label",
    "count_courses_label",
    "count_events_label",
    "count_faqs_label",
    "count_logs_label",
)


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _create_temp_db(tmp_path):
    """Initialize and return an isolated database for one widget test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    return database_path


def _create_live_summary_data(db_path) -> None:
    """Create one connected record for every dashboard summary domain."""
    faculty_id = create_faculty("Engineering", db_path=db_path)
    room_id = create_room(
        "Robotics Laboratory",
        "R101",
        "Engineering Building",
        1,
        "Laboratory",
        x_coord=100.0,
        y_coord=200.0,
        db_path=db_path,
    )
    professor_id = create_professor(
        "Dr. Mona Hassan",
        "Professor",
        faculty_id,
        room_id,
        db_path=db_path,
    )
    create_course(
        "ROB101",
        "Introduction to Robotics",
        faculty_id,
        professor_id,
        room_id,
        "Monday",
        "09:00",
        "10:30",
        db_path=db_path,
    )
    create_event(
        "Robotics Exhibition",
        "Student projects",
        "Main Auditorium",
        "2026-06-22",
        "2026-06-23",
        db_path=db_path,
    )
    faq_id = create_faq(
        "Where is the robotics laboratory?",
        "The laboratory is room R101.",
        "robotics laboratory",
        "Campus Navigation",
        db_path,
    )
    create_log(
        "Where is the robotics laboratory?",
        faq_id,
        "The laboratory is room R101.",
        "Public Assistant",
        db_path,
    )


def test_dashboard_home_page_can_be_instantiated(tmp_path) -> None:
    """Confirm the live summary page can be constructed safely."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = DashboardHomePage(db_path=db_path)
    try:
        assert application is not None
        assert page is not None
    finally:
        page.close()


def test_dashboard_home_page_shows_zero_counts_for_empty_database(tmp_path) -> None:
    """Confirm an initialized database begins with zero domain totals."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = DashboardHomePage(db_path=db_path)
    try:
        assert application is not None
        assert all(getattr(page, name).text() == "0" for name in COUNT_LABEL_ATTRIBUTES)
    finally:
        page.close()


def test_dashboard_home_page_shows_live_counts(tmp_path) -> None:
    """Confirm each card displays its repository's current record count."""
    db_path = _create_temp_db(tmp_path)
    _create_live_summary_data(db_path)
    application = _get_application()
    page = DashboardHomePage(db_path=db_path)
    try:
        assert application is not None
        assert all(getattr(page, name).text() == "1" for name in COUNT_LABEL_ATTRIBUTES)
    finally:
        page.close()


def test_dashboard_home_page_refresh_updates_counts(tmp_path) -> None:
    """Confirm refresh retrieves records created after page construction."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = DashboardHomePage(db_path=db_path)
    try:
        assert application is not None
        assert page.count_faculties_label.text() == "0"
        create_faculty("Engineering", db_path=db_path)

        page.refresh_counts()

        assert page.count_faculties_label.text() == "1"
    finally:
        page.close()


def test_dashboard_home_page_has_refresh_button(tmp_path) -> None:
    """Confirm the page exposes its manual live-data refresh action."""
    db_path = _create_temp_db(tmp_path)
    application = _get_application()
    page = DashboardHomePage(db_path=db_path)
    try:
        assert application is not None
        assert isinstance(page.refresh_dashboard_button, QPushButton)
        assert page.refresh_dashboard_button.objectName() == "refresh_dashboard_button"
        assert page.refresh_dashboard_button.text() == "Refresh"
    finally:
        page.close()
