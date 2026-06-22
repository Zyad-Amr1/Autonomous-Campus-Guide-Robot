"""Tests for university event operations shared by both ECU applications."""

import pytest

from database.init_db import initialize_database
from database.repositories.event_repository import (
    count_events,
    create_event,
    delete_event,
    get_active_events,
    get_all_events,
    get_event_by_id,
    search_events,
    update_event,
)


def create_temp_db(tmp_path):
    """Initialize and return an isolated database path for one test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    return database_path


def create_standard_event(
    db_path,
    title: str = "ECU Robotics Conference",
    start_date: str = "2026-06-22",
    end_date: str = "2026-06-23",
    description: str | None = "Research presentations and demonstrations",
    location: str | None = "Main Auditorium",
    start_time: str | None = "09:00",
    end_time: str | None = "16:00",
) -> int:
    """Create a reusable event record for repository tests."""
    return create_event(
        title,
        description,
        location,
        start_date,
        end_date,
        start_time,
        end_time,
        db_path,
    )


def test_create_event_returns_new_id(tmp_path) -> None:
    """Confirm event creation returns a positive integer identifier."""
    db_path = create_temp_db(tmp_path)

    event_id = create_standard_event(db_path)

    assert isinstance(event_id, int)
    assert event_id > 0


def test_create_event_saves_data_correctly(tmp_path) -> None:
    """Confirm all event fields are normalized and persisted correctly."""
    db_path = create_temp_db(tmp_path)

    event_id = create_event(
        "  ECU Robotics Conference  ",
        "  Research presentations and demonstrations  ",
        "  Main Auditorium  ",
        "  2026-06-22  ",
        "  2026-06-23  ",
        "  09:00  ",
        "  16:00  ",
        db_path,
    )
    event = get_event_by_id(event_id, db_path)

    assert event is not None
    assert event["title"] == "ECU Robotics Conference"
    assert event["description"] == "Research presentations and demonstrations"
    assert event["location"] == "Main Auditorium"
    assert event["start_date"] == "2026-06-22"
    assert event["end_date"] == "2026-06-23"
    assert event["start_time"] == "09:00"
    assert event["end_time"] == "16:00"


def test_create_event_rejects_empty_title(tmp_path) -> None:
    """Confirm whitespace-only event titles are rejected."""
    db_path = create_temp_db(tmp_path)

    with pytest.raises(ValueError, match="Event title cannot be empty"):
        create_event("   ", None, None, "2026-06-22", "2026-06-23", db_path=db_path)


def test_create_event_rejects_invalid_dates(tmp_path) -> None:
    """Confirm malformed dates and reversed date ranges are rejected."""
    db_path = create_temp_db(tmp_path)

    with pytest.raises(ValueError, match="Start date must use YYYY-MM-DD format"):
        create_event("Event", None, None, "bad-date", "2026-06-23", db_path=db_path)
    with pytest.raises(ValueError, match="End date must use YYYY-MM-DD format"):
        create_event("Event", None, None, "2026-06-22", "bad-date", db_path=db_path)
    with pytest.raises(ValueError, match="End date cannot be before start date"):
        create_event("Event", None, None, "2026-06-23", "2026-06-22", db_path=db_path)


def test_get_event_by_id_returns_none_for_missing_id(tmp_path) -> None:
    """Confirm lookup returns ``None`` for an unknown event identifier."""
    db_path = create_temp_db(tmp_path)

    assert get_event_by_id(999999, db_path) is None


def test_get_all_events_returns_ordered_rows(tmp_path) -> None:
    """Confirm events use stable start-date and title ordering."""
    db_path = create_temp_db(tmp_path)
    create_standard_event(db_path, "Later Event", "2026-08-01", "2026-08-01")
    create_standard_event(db_path, "Beta Event", "2026-07-01", "2026-07-01")
    create_standard_event(db_path, "Alpha Event", "2026-07-01", "2026-07-01")

    events = get_all_events(db_path)

    assert [event["title"] for event in events] == [
        "Alpha Event",
        "Beta Event",
        "Later Event",
    ]


def test_update_event_updates_existing_row(tmp_path) -> None:
    """Confirm all editable event fields can be updated."""
    db_path = create_temp_db(tmp_path)
    event_id = create_standard_event(db_path)

    was_updated = update_event(
        event_id,
        "  ECU Innovation Day  ",
        "  Student projects  ",
        "  Innovation Hub  ",
        "  2026-07-10  ",
        "  2026-07-11  ",
        "  10:00  ",
        "  15:00  ",
        db_path,
    )
    event = get_event_by_id(event_id, db_path)

    assert was_updated is True
    assert event is not None
    assert event["title"] == "ECU Innovation Day"
    assert event["description"] == "Student projects"
    assert event["location"] == "Innovation Hub"
    assert event["start_date"] == "2026-07-10"
    assert event["end_date"] == "2026-07-11"
    assert event["start_time"] == "10:00"
    assert event["end_time"] == "15:00"


def test_update_event_returns_false_for_missing_id(tmp_path) -> None:
    """Confirm updating an unknown event reports no change."""
    db_path = create_temp_db(tmp_path)

    assert (
        update_event(
            999999,
            "Event",
            None,
            None,
            "2026-06-22",
            "2026-06-23",
            db_path=db_path,
        )
        is False
    )


def test_update_event_rejects_invalid_title_or_dates(tmp_path) -> None:
    """Confirm updates enforce title, date format, and date-range rules."""
    db_path = create_temp_db(tmp_path)
    event_id = create_standard_event(db_path)

    with pytest.raises(ValueError, match="Event title cannot be empty"):
        update_event(
            event_id, "   ", None, None, "2026-06-22", "2026-06-23", db_path=db_path
        )
    with pytest.raises(ValueError, match="Start date must use YYYY-MM-DD format"):
        update_event(
            event_id, "Event", None, None, "bad-date", "2026-06-23", db_path=db_path
        )
    with pytest.raises(ValueError, match="End date cannot be before start date"):
        update_event(
            event_id, "Event", None, None, "2026-06-23", "2026-06-22", db_path=db_path
        )


def test_delete_event_removes_existing_row(tmp_path) -> None:
    """Confirm deleting an event removes its database record."""
    db_path = create_temp_db(tmp_path)
    event_id = create_standard_event(db_path)

    was_deleted = delete_event(event_id, db_path)

    assert was_deleted is True
    assert get_event_by_id(event_id, db_path) is None


def test_delete_event_returns_false_for_missing_id(tmp_path) -> None:
    """Confirm deleting an unknown event reports no change."""
    db_path = create_temp_db(tmp_path)

    assert delete_event(999999, db_path) is False


def test_count_events_returns_correct_number(tmp_path) -> None:
    """Confirm the repository reports the current event total."""
    db_path = create_temp_db(tmp_path)
    create_standard_event(db_path, "Event One")
    create_standard_event(db_path, "Event Two")
    create_standard_event(db_path, "Event Three")

    assert count_events(db_path) == 3


def test_search_events_matches_title_description_location_and_dates(tmp_path) -> None:
    """Confirm search covers all event text and date fields."""
    db_path = create_temp_db(tmp_path)
    create_standard_event(
        db_path,
        "Robotics Conference",
        "2026-06-22",
        "2026-06-23",
        "Autonomous systems research",
        "Main Auditorium",
    )
    create_standard_event(
        db_path,
        "Career Fair",
        "2026-07-10",
        "2026-07-11",
        "Employer networking",
        "Sports Hall",
    )

    expected_searches = {
        "Robotics": "Robotics Conference",
        "Employer": "Career Fair",
        "Auditorium": "Robotics Conference",
        "2026-07-10": "Career Fair",
        "2026-06-23": "Robotics Conference",
    }
    for search_text, expected_title in expected_searches.items():
        assert [event["title"] for event in search_events(search_text, db_path)] == [
            expected_title
        ]


def test_search_events_with_empty_text_returns_all(tmp_path) -> None:
    """Confirm a blank search returns every event in standard order."""
    db_path = create_temp_db(tmp_path)
    create_standard_event(db_path, "Later Event", "2026-08-01", "2026-08-01")
    create_standard_event(db_path, "Earlier Event", "2026-07-01", "2026-07-01")

    events = search_events("   ", db_path)

    assert [event["title"] for event in events] == ["Earlier Event", "Later Event"]


def test_get_active_events_returns_events_for_current_date_range(tmp_path) -> None:
    """Confirm active filtering excludes past and future events."""
    db_path = create_temp_db(tmp_path)
    create_standard_event(db_path, "Active Event", "2026-06-20", "2026-06-24")
    create_standard_event(db_path, "Past Event", "2026-06-01", "2026-06-10")
    create_standard_event(db_path, "Future Event", "2026-07-01", "2026-07-02")

    events = get_active_events("2026-06-22", db_path)

    assert [event["title"] for event in events] == ["Active Event"]


def test_get_active_events_includes_start_and_end_dates(tmp_path) -> None:
    """Confirm active event ranges include both boundary dates."""
    db_path = create_temp_db(tmp_path)
    create_standard_event(db_path, "Starts Today", "2026-06-22", "2026-06-24")
    create_standard_event(db_path, "Ends Today", "2026-06-20", "2026-06-22")

    events = get_active_events("2026-06-22", db_path)

    assert {event["title"] for event in events} == {"Starts Today", "Ends Today"}


def test_get_active_events_rejects_invalid_current_date(tmp_path) -> None:
    """Confirm active-event queries reject malformed dates."""
    db_path = create_temp_db(tmp_path)

    with pytest.raises(ValueError, match="Current date must use YYYY-MM-DD format"):
        get_active_events("bad-date", db_path)
