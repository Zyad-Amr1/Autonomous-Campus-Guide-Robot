"""Tests for FAQ operations and deterministic public-assistant matching."""

import pytest

from database.init_db import initialize_database
from database.repositories.faq_repository import (
    count_faqs,
    create_faq,
    delete_faq,
    find_best_faq_match,
    get_all_faqs,
    get_faq_by_id,
    get_faqs_by_category,
    search_faqs,
    update_faq,
)


def create_temp_db(tmp_path):
    """Initialize and return an isolated database path for one test."""
    database_path = tmp_path / "test_ecu_robot.db"
    initialize_database(database_path)
    return database_path


def create_standard_faq(
    db_path,
    question: str = "Where is the university library?",
    answer: str = "The library is in the main building.",
    keywords: str | None = "library books study",
    category: str | None = "Campus Services",
) -> int:
    """Create a reusable FAQ record for repository tests."""
    return create_faq(question, answer, keywords, category, db_path)


def test_create_faq_returns_new_id(tmp_path) -> None:
    """Confirm FAQ creation returns a positive integer identifier."""
    db_path = create_temp_db(tmp_path)

    faq_id = create_standard_faq(db_path)

    assert isinstance(faq_id, int)
    assert faq_id > 0


def test_create_faq_saves_data_correctly(tmp_path) -> None:
    """Confirm all FAQ fields are normalized and persisted correctly."""
    db_path = create_temp_db(tmp_path)

    faq_id = create_faq(
        "  Where is the university library?  ",
        "  The library is in the main building.  ",
        "  library books study  ",
        "  Campus Services  ",
        db_path,
    )
    faq = get_faq_by_id(faq_id, db_path)

    assert faq is not None
    assert faq["question"] == "Where is the university library?"
    assert faq["answer"] == "The library is in the main building."
    assert faq["keywords"] == "library books study"
    assert faq["category"] == "Campus Services"


def test_create_faq_rejects_empty_question_or_answer(tmp_path) -> None:
    """Confirm FAQ questions and answers must both contain text."""
    db_path = create_temp_db(tmp_path)

    with pytest.raises(ValueError, match="FAQ question cannot be empty"):
        create_faq("   ", "Answer", db_path=db_path)
    with pytest.raises(ValueError, match="FAQ answer cannot be empty"):
        create_faq("Question", "   ", db_path=db_path)


def test_get_faq_by_id_returns_none_for_missing_id(tmp_path) -> None:
    """Confirm lookup returns ``None`` for an unknown FAQ identifier."""
    db_path = create_temp_db(tmp_path)

    assert get_faq_by_id(999999, db_path) is None


def test_get_all_faqs_returns_ordered_rows(tmp_path) -> None:
    """Confirm FAQs use stable category and question ordering."""
    db_path = create_temp_db(tmp_path)
    create_standard_faq(db_path, "Where is admissions?", category="Services")
    create_standard_faq(db_path, "How do I register?", category="Academic")
    create_standard_faq(db_path, "How do I view grades?", category="Academic")

    faqs = get_all_faqs(db_path)

    assert [(faq["category"], faq["question"]) for faq in faqs] == [
        ("Academic", "How do I register?"),
        ("Academic", "How do I view grades?"),
        ("Services", "Where is admissions?"),
    ]


def test_update_faq_updates_existing_row(tmp_path) -> None:
    """Confirm all editable FAQ fields can be updated."""
    db_path = create_temp_db(tmp_path)
    faq_id = create_standard_faq(db_path)

    was_updated = update_faq(
        faq_id,
        "  How can I access the digital library?  ",
        "  Sign in through the student portal.  ",
        "  digital library portal  ",
        "  Academic Resources  ",
        db_path,
    )
    faq = get_faq_by_id(faq_id, db_path)

    assert was_updated is True
    assert faq is not None
    assert faq["question"] == "How can I access the digital library?"
    assert faq["answer"] == "Sign in through the student portal."
    assert faq["keywords"] == "digital library portal"
    assert faq["category"] == "Academic Resources"


def test_update_faq_returns_false_for_missing_id(tmp_path) -> None:
    """Confirm updating an unknown FAQ reports no change."""
    db_path = create_temp_db(tmp_path)

    assert update_faq(999999, "Question", "Answer", db_path=db_path) is False


def test_update_faq_rejects_empty_question_or_answer(tmp_path) -> None:
    """Confirm updates validate both required FAQ fields."""
    db_path = create_temp_db(tmp_path)
    faq_id = create_standard_faq(db_path)

    with pytest.raises(ValueError, match="FAQ question cannot be empty"):
        update_faq(faq_id, "   ", "Answer", db_path=db_path)
    with pytest.raises(ValueError, match="FAQ answer cannot be empty"):
        update_faq(faq_id, "Question", "   ", db_path=db_path)


def test_delete_faq_removes_existing_row(tmp_path) -> None:
    """Confirm deleting an FAQ removes its database record."""
    db_path = create_temp_db(tmp_path)
    faq_id = create_standard_faq(db_path)

    was_deleted = delete_faq(faq_id, db_path)

    assert was_deleted is True
    assert get_faq_by_id(faq_id, db_path) is None


def test_delete_faq_returns_false_for_missing_id(tmp_path) -> None:
    """Confirm deleting an unknown FAQ reports no change."""
    db_path = create_temp_db(tmp_path)

    assert delete_faq(999999, db_path) is False


def test_count_faqs_returns_correct_number(tmp_path) -> None:
    """Confirm the repository reports the current FAQ total."""
    db_path = create_temp_db(tmp_path)
    create_standard_faq(db_path, "Question One")
    create_standard_faq(db_path, "Question Two")
    create_standard_faq(db_path, "Question Three")

    assert count_faqs(db_path) == 3


def test_search_faqs_matches_question_answer_keywords_and_category(tmp_path) -> None:
    """Confirm search covers every requested FAQ field."""
    db_path = create_temp_db(tmp_path)
    create_standard_faq(
        db_path,
        "Where is the library?",
        "It is beside the main auditorium.",
        "books study",
        "Campus Services",
    )
    create_standard_faq(
        db_path,
        "How do I apply?",
        "Complete the online admission form.",
        "application enrollment",
        "Admissions",
    )

    expected_searches = {
        "library": "Where is the library?",
        "online admission": "How do I apply?",
        "enrollment": "How do I apply?",
        "Campus Services": "Where is the library?",
    }
    for search_text, expected_question in expected_searches.items():
        assert [faq["question"] for faq in search_faqs(search_text, db_path)] == [
            expected_question
        ]


def test_search_faqs_with_empty_text_returns_all(tmp_path) -> None:
    """Confirm a blank search returns every FAQ in standard order."""
    db_path = create_temp_db(tmp_path)
    create_standard_faq(db_path, "Services Question", category="Services")
    create_standard_faq(db_path, "Academic Question", category="Academic")

    faqs = search_faqs("   ", db_path)

    assert [faq["question"] for faq in faqs] == [
        "Academic Question",
        "Services Question",
    ]


def test_get_faqs_by_category_returns_matching_faqs_case_insensitive(tmp_path) -> None:
    """Confirm category filtering is case-insensitive and exclusive."""
    db_path = create_temp_db(tmp_path)
    create_standard_faq(db_path, "Library Question", category="Campus Services")
    create_standard_faq(db_path, "Parking Question", category="Campus Services")
    create_standard_faq(db_path, "Registration Question", category="Academic")

    faqs = get_faqs_by_category("cAmPuS sErViCeS", db_path)

    assert [faq["question"] for faq in faqs] == [
        "Library Question",
        "Parking Question",
    ]


def test_get_faqs_by_category_with_empty_category_returns_empty_list(tmp_path) -> None:
    """Confirm blank category filters return no FAQ records."""
    db_path = create_temp_db(tmp_path)

    assert get_faqs_by_category("   ", db_path) == []


def test_find_best_faq_match_matches_question_keywords_and_answer(tmp_path) -> None:
    """Confirm deterministic scoring prioritizes relevant FAQ content."""
    db_path = create_temp_db(tmp_path)
    create_standard_faq(
        db_path,
        "Where is the library?",
        "The library is in the main building.",
        "books study",
        "Campus Services",
    )
    create_standard_faq(
        db_path,
        "How do I apply for admission?",
        "Complete the online form and submit academic records.",
        "application enrollment",
        "Admissions",
    )
    create_standard_faq(
        db_path,
        "How can I pay tuition?",
        "Payments are accepted through the finance office.",
        "tuition fees payment",
        "Finance",
    )

    question_match = find_best_faq_match("where library", db_path)
    keyword_match = find_best_faq_match("enrollment", db_path)
    answer_match = find_best_faq_match("academic records", db_path)

    assert question_match is not None
    assert question_match["question"] == "Where is the library?"
    assert keyword_match is not None
    assert keyword_match["question"] == "How do I apply for admission?"
    assert answer_match is not None
    assert answer_match["question"] == "How do I apply for admission?"


def test_find_best_faq_match_returns_none_for_empty_or_unmatched_query(tmp_path) -> None:
    """Confirm blank and unrelated queries do not produce false matches."""
    db_path = create_temp_db(tmp_path)
    create_standard_faq(db_path)

    assert find_best_faq_match("   ", db_path) is None
    assert find_best_faq_match("astronomy telescope", db_path) is None
