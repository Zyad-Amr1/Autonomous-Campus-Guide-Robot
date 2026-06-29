"""Tests for lightweight RAG query analysis."""

from controllers.rag.query_analyzer import (
    detect_intent,
    detect_language,
    extract_keywords,
    normalize_query,
)


def test_detects_arabic() -> None:
    assert detect_language("ما هي كليات الجامعة؟") == "ar"


def test_detects_english() -> None:
    assert detect_language("Tell me about ECU faculties") == "en"


def test_detects_mixed_language() -> None:
    assert detect_language("Where is الكافيتريا?") == "mixed"


def test_detects_faculty_intent() -> None:
    assert detect_intent("What faculties and departments are available?") == "faculty_info"


def test_detects_professor_intent() -> None:
    assert detect_intent("Who are the professors in robotics?") == "professor_info"


def test_detects_room_location_intent() -> None:
    assert detect_intent("Where is the cafeteria room?") == "room_location"
    assert detect_intent("\u0623\u064a\u0646 \u0627\u0644\u0643\u0627\u0641\u064a\u062a\u0631\u064a\u0627\u061f") == "room_location"


def test_extracts_useful_keywords() -> None:
    keywords = extract_keywords("Tell me about Faculty of Engineering departments.")

    assert "faculty" in keywords
    assert "engineering" in keywords
    assert "department" in keywords
    assert "tell" not in keywords


def test_normalize_query_handles_case_and_arabic_forms() -> None:
    assert normalize_query("  أَيْنَ Faculty?  ") == "اين faculty"
