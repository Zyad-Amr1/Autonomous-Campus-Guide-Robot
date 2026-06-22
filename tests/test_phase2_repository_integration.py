"""Phase 2 integration tests proving repository readiness before GUI development."""

from datetime import date

from database.init_db import initialize_database
from database.repositories.admin_repository import authenticate_admin
from database.repositories.course_repository import (
    count_courses,
    create_course,
    get_today_courses,
    search_courses,
)
from database.repositories.event_repository import (
    count_events,
    create_event,
    get_active_events,
    search_events,
)
from database.repositories.faculty_repository import count_faculties, create_faculty
from database.repositories.faq_repository import (
    count_faqs,
    create_faq,
    find_best_faq_match,
    search_faqs,
)
from database.repositories.log_repository import (
    count_logs,
    create_log,
    get_recent_logs,
    get_unmatched_questions,
    search_logs,
)
from database.repositories.professor_repository import (
    count_professors,
    create_professor,
    search_professors,
)
from database.repositories.room_repository import (
    count_rooms,
    create_room,
    get_mappable_rooms,
    search_rooms,
)


def _create_temp_db(tmp_path):
    """Initialize and return an isolated database for one integration test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    return database_path


def _create_academic_chain(db_path):
    """Create linked faculty, room, and professor records for course tests."""
    faculty_id = create_faculty(
        "Faculty of Engineering",
        building="Engineering Building",
        db_path=db_path,
    )
    room_id = create_room(
        "Robotics Laboratory",
        "R101",
        "Engineering Building",
        1,
        "Laboratory",
        "Autonomous systems teaching laboratory",
        120.5,
        240.25,
        db_path,
    )
    professor_id = create_professor(
        "Dr. Mona Hassan",
        "Associate Professor",
        faculty_id,
        room_id,
        "mona.hassan@ecu.edu.eg",
        office_hours="Sunday 10:00-12:00",
        db_path=db_path,
    )
    return faculty_id, room_id, professor_id


def test_phase2_repositories_work_together_end_to_end(tmp_path) -> None:
    """Verify the connected repository workflow before dashboard construction."""
    db_path = _create_temp_db(tmp_path)

    admin = authenticate_admin("admin", "admin123", db_path)
    assert admin is not None
    assert admin["role"] == "super_admin"

    faculty_id, room_id, professor_id = _create_academic_chain(db_path)
    create_course(
        "ROB101",
        "Introduction to Robotics",
        faculty_id,
        professor_id,
        room_id,
        "Sunday",
        "09:00",
        "10:30",
        "Fall 2026",
        db_path,
    )
    create_event(
        "ECU Robotics Exhibition",
        "Student robotics projects and demonstrations",
        "Main Auditorium",
        "2026-06-20",
        "2026-06-24",
        "10:00",
        "16:00",
        db_path,
    )
    faq_id = create_faq(
        "Where is the robotics laboratory?",
        "The robotics laboratory is room R101 in the Engineering Building.",
        "robotics laboratory directions R101",
        "Campus Navigation",
        db_path,
    )

    original_query = "How do I find the robotics laboratory?"
    matched_faq = find_best_faq_match(original_query, db_path)
    assert matched_faq is not None
    assert matched_faq["id"] == faq_id

    create_log(
        original_query,
        matched_faq["id"],
        matched_faq["answer"],
        "Public Assistant",
        db_path,
    )
    recent_logs = get_recent_logs(db_path=db_path)

    assert len(recent_logs) == 1
    assert recent_logs[0]["query_text"] == original_query
    assert recent_logs[0]["matched_question"] == matched_faq["question"]
    assert recent_logs[0]["matched_answer"] == matched_faq["answer"]
    assert count_faculties(db_path) == 1
    assert count_rooms(db_path) == 1
    assert count_professors(db_path) == 1
    assert count_courses(db_path) == 1
    assert count_events(db_path) == 1
    assert count_faqs(db_path) == 1
    assert count_logs(db_path) == 1


def test_phase2_search_functions_return_expected_results(tmp_path) -> None:
    """Verify dashboard searches work across all repository domains."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id, professor_id = _create_academic_chain(db_path)
    create_course(
        "ROB201",
        "Mobile Robotics",
        faculty_id,
        professor_id,
        room_id,
        "Monday",
        "11:00",
        "12:30",
        "Spring 2027",
        db_path,
    )
    create_event(
        "Innovation and Robotics Expo",
        "An exhibition of student technology projects",
        "Main Auditorium",
        "2026-07-10",
        "2026-07-11",
        db_path=db_path,
    )
    faq_id = create_faq(
        "How can I reach the robotics laboratory?",
        "Go to room R101 in the Engineering Building.",
        "robotics directions R101",
        "Campus Navigation",
        db_path,
    )
    create_log(
        "Where is room R101?",
        faq_id,
        "Go to the Engineering Building.",
        "Public Assistant",
        db_path,
    )

    assert [room["room_number"] for room in search_rooms("Engineering Building", db_path)] == [
        "R101"
    ]
    assert [room["room_number"] for room in search_rooms("R101", db_path)] == ["R101"]
    assert [
        professor["full_name"] for professor in search_professors("Mona Hassan", db_path)
    ] == ["Dr. Mona Hassan"]
    assert [
        professor["full_name"]
        for professor in search_professors("Faculty of Engineering", db_path)
    ] == ["Dr. Mona Hassan"]
    assert [course["course_code"] for course in search_courses("ROB201", db_path)] == [
        "ROB201"
    ]
    assert [course["course_code"] for course in search_courses("Mona Hassan", db_path)] == [
        "ROB201"
    ]
    assert [event["title"] for event in search_events("Robotics Expo", db_path)] == [
        "Innovation and Robotics Expo"
    ]
    assert [event["title"] for event in search_events("Main Auditorium", db_path)] == [
        "Innovation and Robotics Expo"
    ]
    assert [faq["id"] for faq in search_faqs("directions", db_path)] == [faq_id]
    assert [faq["id"] for faq in search_faqs("Campus Navigation", db_path)] == [faq_id]
    assert [log["query_text"] for log in search_logs("room R101", db_path)] == [
        "Where is room R101?"
    ]
    assert [log["query_text"] for log in search_logs("Public Assistant", db_path)] == [
        "Where is room R101?"
    ]


def test_phase2_public_dashboard_queries_are_ready(tmp_path) -> None:
    """Verify public-facing repository queries are ready before GUI screens."""
    db_path = _create_temp_db(tmp_path)
    faculty_id, room_id, professor_id = _create_academic_chain(db_path)
    today_name = date.today().strftime("%A")
    course_id = create_course(
        "TODAY101",
        "Today's Robotics Seminar",
        faculty_id,
        professor_id,
        room_id,
        today_name,
        "13:00",
        "14:00",
        db_path=db_path,
    )
    event_id = create_event(
        "Active Campus Welcome Event",
        "Guidance for new students",
        "Student Center",
        "2026-06-20",
        "2026-06-24",
        db_path=db_path,
    )
    faq_id = create_faq(
        "Where is the university library?",
        "The library is in the main building.",
        "library locate directions books",
        "Campus Services",
        db_path,
    )
    unmatched_log_id = create_log(
        "Is there an astronomy club?",
        response_text="No matching answer was found.",
        screen_name="Public Assistant",
        db_path=db_path,
    )

    mappable_rooms = get_mappable_rooms(db_path)
    today_courses = get_today_courses(db_path)
    active_events = get_active_events("2026-06-22", db_path)
    faq_match = find_best_faq_match("How can I locate the library?", db_path)
    unmatched_logs = get_unmatched_questions(db_path)

    assert [room["id"] for room in mappable_rooms] == [room_id]
    assert [course["id"] for course in today_courses] == [course_id]
    assert [event["id"] for event in active_events] == [event_id]
    assert faq_match is not None
    assert faq_match["id"] == faq_id
    assert [log["id"] for log in unmatched_logs] == [unmatched_log_id]
