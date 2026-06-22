"""Tests for course and schedule operations shared by both ECU applications."""

import sqlite3
from datetime import date

import pytest

from database.init_db import initialize_database
from database.repositories.course_repository import (
    count_courses,
    create_course,
    delete_course,
    get_all_courses,
    get_course_by_id,
    get_courses_by_day,
    get_today_courses,
    search_courses,
    update_course,
)
from database.repositories.faculty_repository import create_faculty
from database.repositories.professor_repository import create_professor
from database.repositories.room_repository import create_room


def create_temp_db(tmp_path):
    """Initialize and return an isolated database path for one test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    return database_path


def create_test_faculty(db_path, name: str = "Engineering") -> int:
    """Create a faculty required by course relationships."""
    return create_faculty(name, db_path=db_path)


def create_test_room(
    db_path,
    room_name: str = "Robotics Laboratory",
    room_number: str = "R101",
    building: str = "Engineering Building",
) -> int:
    """Create a room required by course schedules."""
    return create_room(
        room_name,
        room_number,
        building,
        1,
        "Classroom",
        db_path=db_path,
    )


def create_test_professor(
    db_path,
    faculty_id: int,
    office_room_id: int | None = None,
    full_name: str = "Dr. Mona Hassan",
) -> int:
    """Create a professor required by course schedules."""
    return create_professor(
        full_name,
        "Professor",
        faculty_id,
        office_room_id,
        db_path=db_path,
    )


def create_dependencies(db_path):
    """Create and return a standard faculty, professor, and room tuple."""
    faculty_id = create_test_faculty(db_path)
    room_id = create_test_room(db_path)
    professor_id = create_test_professor(db_path, faculty_id, room_id)
    return faculty_id, professor_id, room_id


def create_standard_course(
    db_path,
    faculty_id: int,
    professor_id: int | None,
    room_id: int | None,
    course_code: str = "ROB101",
    course_name: str = "Introduction to Robotics",
    schedule_day: str = "Monday",
    start_time: str = "09:00",
    end_time: str = "10:30",
    semester: str | None = "Fall 2026",
) -> int:
    """Create a reusable course record for repository tests."""
    return create_course(
        course_code,
        course_name,
        faculty_id,
        professor_id,
        room_id,
        schedule_day,
        start_time,
        end_time,
        semester,
        db_path,
    )


def test_create_course_returns_new_id(tmp_path) -> None:
    """Confirm course creation returns a positive integer identifier."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)

    course_id = create_standard_course(db_path, faculty_id, professor_id, room_id)

    assert isinstance(course_id, int)
    assert course_id > 0


def test_create_course_saves_data_correctly(tmp_path) -> None:
    """Confirm course fields and joined display details are saved correctly."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)

    course_id = create_course(
        "  ROB101  ",
        "  Introduction to Robotics  ",
        faculty_id,
        professor_id,
        room_id,
        "  Monday  ",
        "  09:00  ",
        "  10:30  ",
        "  Fall 2026  ",
        db_path,
    )
    course = get_course_by_id(course_id, db_path)

    assert course is not None
    assert course["course_code"] == "ROB101"
    assert course["course_name"] == "Introduction to Robotics"
    assert course["schedule_day"] == "Monday"
    assert course["start_time"] == "09:00"
    assert course["end_time"] == "10:30"
    assert course["semester"] == "Fall 2026"
    assert course["faculty_name"] == "Engineering"
    assert course["professor_name"] == "Dr. Mona Hassan"
    assert course["room_name"] == "Robotics Laboratory"
    assert course["room_number"] == "R101"
    assert course["building"] == "Engineering Building"
    assert course["floor"] == 1


def test_create_course_rejects_empty_required_fields(tmp_path) -> None:
    """Confirm each required course text field rejects blank input."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)
    valid_values = {
        "course_code": "ROB101",
        "course_name": "Introduction to Robotics",
        "faculty_id": faculty_id,
        "professor_id": professor_id,
        "room_id": room_id,
        "schedule_day": "Monday",
        "start_time": "09:00",
        "end_time": "10:30",
    }

    for field_name in (
        "course_code",
        "course_name",
        "schedule_day",
        "start_time",
        "end_time",
    ):
        invalid_values = valid_values.copy()
        invalid_values[field_name] = "   "
        with pytest.raises(ValueError):
            create_course(**invalid_values, db_path=db_path)


def test_create_course_rejects_invalid_faculty_id(tmp_path) -> None:
    """Confirm invalid faculty relationships are rejected by SQLite."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)

    with pytest.raises(sqlite3.IntegrityError):
        create_standard_course(db_path, faculty_id + 999999, professor_id, room_id)


def test_create_course_rejects_invalid_professor_id(tmp_path) -> None:
    """Confirm invalid professor relationships are rejected by SQLite."""
    db_path = create_temp_db(tmp_path)
    faculty_id = create_test_faculty(db_path)
    room_id = create_test_room(db_path)

    with pytest.raises(sqlite3.IntegrityError):
        create_standard_course(db_path, faculty_id, 999999, room_id)


def test_create_course_rejects_invalid_room_id(tmp_path) -> None:
    """Confirm invalid room relationships are rejected by SQLite."""
    db_path = create_temp_db(tmp_path)
    faculty_id = create_test_faculty(db_path)
    professor_id = create_test_professor(db_path, faculty_id)

    with pytest.raises(sqlite3.IntegrityError):
        create_standard_course(db_path, faculty_id, professor_id, 999999)


def test_create_course_rejects_duplicate_schedule_constraint(tmp_path) -> None:
    """Confirm SQLite prevents duplicate course schedule locations."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)
    create_standard_course(db_path, faculty_id, professor_id, room_id)

    with pytest.raises(sqlite3.IntegrityError):
        create_standard_course(
            db_path,
            faculty_id,
            professor_id,
            room_id,
            course_name="Robotics Lab Session",
        )


def test_get_course_by_id_returns_none_for_missing_id(tmp_path) -> None:
    """Confirm lookup returns ``None`` for an unknown course identifier."""
    db_path = create_temp_db(tmp_path)

    assert get_course_by_id(999999, db_path) is None


def test_get_all_courses_returns_ordered_rows(tmp_path) -> None:
    """Confirm courses use stable day, start-time, and code ordering."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)
    create_standard_course(
        db_path, faculty_id, professor_id, room_id, "MON200", "Monday Later", "Monday", "11:00", "12:00"
    )
    create_standard_course(
        db_path, faculty_id, professor_id, room_id, "FRI100", "Friday Course", "Friday", "09:00", "10:00"
    )
    create_standard_course(
        db_path, faculty_id, professor_id, room_id, "MON100", "Monday Early", "Monday", "08:00", "09:00"
    )

    courses = get_all_courses(db_path)

    assert [course["course_code"] for course in courses] == [
        "FRI100",
        "MON100",
        "MON200",
    ]


def test_update_course_updates_existing_row(tmp_path) -> None:
    """Confirm all editable course schedule fields can be updated."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)
    course_id = create_standard_course(db_path, faculty_id, professor_id, room_id)

    was_updated = update_course(
        course_id,
        "  AI201  ",
        "  Artificial Intelligence  ",
        faculty_id,
        professor_id,
        room_id,
        "  Tuesday  ",
        "  11:00  ",
        "  12:30  ",
        "  Spring 2027  ",
        db_path,
    )
    course = get_course_by_id(course_id, db_path)

    assert was_updated is True
    assert course is not None
    assert course["course_code"] == "AI201"
    assert course["course_name"] == "Artificial Intelligence"
    assert course["schedule_day"] == "Tuesday"
    assert course["start_time"] == "11:00"
    assert course["end_time"] == "12:30"
    assert course["semester"] == "Spring 2027"


def test_update_course_returns_false_for_missing_id(tmp_path) -> None:
    """Confirm updating an unknown course reports no change."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)

    assert (
        update_course(
            999999,
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
        is False
    )


def test_update_course_rejects_empty_required_fields(tmp_path) -> None:
    """Confirm updates validate every required course text field."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)
    course_id = create_standard_course(db_path, faculty_id, professor_id, room_id)
    valid_values = {
        "course_code": "ROB101",
        "course_name": "Introduction to Robotics",
        "faculty_id": faculty_id,
        "professor_id": professor_id,
        "room_id": room_id,
        "schedule_day": "Monday",
        "start_time": "09:00",
        "end_time": "10:30",
    }

    for field_name in (
        "course_code",
        "course_name",
        "schedule_day",
        "start_time",
        "end_time",
    ):
        invalid_values = valid_values.copy()
        invalid_values[field_name] = "   "
        with pytest.raises(ValueError):
            update_course(course_id, **invalid_values, db_path=db_path)


def test_delete_course_removes_existing_row(tmp_path) -> None:
    """Confirm deleting a course removes its database record."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)
    course_id = create_standard_course(db_path, faculty_id, professor_id, room_id)

    was_deleted = delete_course(course_id, db_path)

    assert was_deleted is True
    assert get_course_by_id(course_id, db_path) is None


def test_delete_course_returns_false_for_missing_id(tmp_path) -> None:
    """Confirm deleting an unknown course reports no change."""
    db_path = create_temp_db(tmp_path)

    assert delete_course(999999, db_path) is False


def test_count_courses_returns_correct_number(tmp_path) -> None:
    """Confirm the repository reports the current course total."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)
    create_standard_course(db_path, faculty_id, professor_id, room_id, "ROB101")
    create_standard_course(
        db_path, faculty_id, professor_id, room_id, "AI201", "Artificial Intelligence", "Tuesday"
    )
    create_standard_course(
        db_path, faculty_id, professor_id, room_id, "CS301", "Computer Vision", "Wednesday"
    )

    assert count_courses(db_path) == 3


def test_search_courses_matches_course_faculty_professor_room_and_building(tmp_path) -> None:
    """Confirm search covers course and all joined display fields."""
    db_path = create_temp_db(tmp_path)
    engineering_id = create_test_faculty(db_path, "Engineering")
    engineering_room_id = create_test_room(db_path)
    mona_id = create_test_professor(
        db_path, engineering_id, engineering_room_id, "Dr. Mona Hassan"
    )
    business_id = create_test_faculty(db_path, "Business")
    business_room_id = create_test_room(
        db_path, "Seminar Hall", "S201", "Main Building"
    )
    ahmed_id = create_test_professor(
        db_path, business_id, business_room_id, "Dr. Ahmed Ali"
    )
    create_standard_course(
        db_path,
        engineering_id,
        mona_id,
        engineering_room_id,
        "ROB101",
        "Robotics Fundamentals",
        "Monday",
        semester="Fall 2026",
    )
    create_standard_course(
        db_path,
        business_id,
        ahmed_id,
        business_room_id,
        "BUS201",
        "Marketing Principles",
        "Tuesday",
        semester="Spring 2027",
    )

    expected_searches = {
        "ROB101": "ROB101",
        "Marketing": "BUS201",
        "Business": "BUS201",
        "Mona": "ROB101",
        "S201": "BUS201",
        "Engineering Building": "ROB101",
        "Seminar Hall": "BUS201",
        "Tuesday": "BUS201",
        "Fall 2026": "ROB101",
    }
    for search_text, expected_code in expected_searches.items():
        assert [
            course["course_code"] for course in search_courses(search_text, db_path)
        ] == [expected_code]


def test_search_courses_with_empty_text_returns_all(tmp_path) -> None:
    """Confirm a blank search returns every course in standard order."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)
    create_standard_course(db_path, faculty_id, professor_id, room_id, "TUE201", schedule_day="Tuesday")
    create_standard_course(db_path, faculty_id, professor_id, room_id, "MON101", schedule_day="Monday")

    courses = search_courses("   ", db_path)

    assert [course["course_code"] for course in courses] == ["MON101", "TUE201"]


def test_get_courses_by_day_returns_matching_courses_case_insensitive(tmp_path) -> None:
    """Confirm day filtering is case-insensitive and excludes other days."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)
    create_standard_course(db_path, faculty_id, professor_id, room_id, "MON101", schedule_day="Monday")
    create_standard_course(db_path, faculty_id, professor_id, room_id, "TUE201", schedule_day="Tuesday")

    courses = get_courses_by_day("mOnDaY", db_path)

    assert [course["course_code"] for course in courses] == ["MON101"]


def test_get_courses_by_day_with_empty_day_returns_empty_list(tmp_path) -> None:
    """Confirm blank day filters return no course records."""
    db_path = create_temp_db(tmp_path)

    assert get_courses_by_day("   ", db_path) == []


def test_get_today_courses_uses_current_day(tmp_path) -> None:
    """Confirm today's schedule uses Python's current weekday name."""
    db_path = create_temp_db(tmp_path)
    faculty_id, professor_id, room_id = create_dependencies(db_path)
    today_name = date.today().strftime("%A")
    other_day = "Tuesday" if today_name != "Tuesday" else "Wednesday"
    create_standard_course(
        db_path, faculty_id, professor_id, room_id, "TODAY101", schedule_day=today_name
    )
    create_standard_course(
        db_path, faculty_id, professor_id, room_id, "OTHER201", schedule_day=other_day
    )

    courses = get_today_courses(db_path)

    assert [course["course_code"] for course in courses] == ["TODAY101"]
