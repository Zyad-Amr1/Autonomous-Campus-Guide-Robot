"""Tests for hybrid RAG retrieval."""

from controllers.rag.hybrid_retriever import hybrid_retrieve


def _chunks() -> list[dict]:
    return [
        {
            "id": "faculties:engineering",
            "source": "faculties",
            "title": "Faculty of Engineering",
            "content": "Engineering programs include software, mechatronics, and renewable energy.",
            "keywords": ["faculty", "engineering", "departments"],
            "language": "en",
        },
        {
            "id": "professors:mona",
            "source": "professors",
            "title": "Dr. Mona Hassan",
            "content": "Professor of robotics with office hours on Sunday.",
            "keywords": ["professor", "robotics"],
            "language": "en",
        },
        {
            "id": "rooms:cafeteria",
            "source": "rooms",
            "title": "Cafeteria",
            "content": "The cafeteria is in the Student Center.",
            "keywords": ["cafeteria", "food", "location"],
            "language": "en",
        },
        {
            "id": "faculties:ar",
            "source": "faculties",
            "title": "كلية الهندسة",
            "content": "تضم كلية الهندسة أقسام البرمجيات والميكاترونكس والطاقة.",
            "keywords": ["كلية", "الهندسة", "أقسام"],
            "language": "ar",
        },
    ]


def test_exact_title_match_ranks_first() -> None:
    results = hybrid_retrieve("Faculty of Engineering", _chunks(), intent="faculty_info")

    assert results[0]["id"] == "faculties:engineering"
    assert results[0]["final_score"] > results[1]["final_score"]
    assert "score_details" in results[0]


def test_keyword_match_returns_correct_chunk() -> None:
    results = hybrid_retrieve("robotics professor", _chunks(), intent="professor_info")

    assert results
    assert results[0]["id"] == "professors:mona"


def test_unrelated_query_returns_empty() -> None:
    assert hybrid_retrieve("parking permits on Mars", _chunks()) == []


def test_arabic_query_retrieves_arabic_chunk() -> None:
    results = hybrid_retrieve("ما أقسام كلية الهندسة؟", _chunks(), intent="faculty_info")

    assert results
    assert results[0]["id"] == "faculties:ar"


def test_source_intent_bonus_works() -> None:
    chunks = [
        {
            "id": "rooms:engineering",
            "source": "rooms",
            "title": "Engineering Hall",
            "content": "A hall named Engineering.",
            "keywords": ["engineering"],
        },
        {
            "id": "faculties:engineering",
            "source": "faculties",
            "title": "Engineering",
            "content": "Engineering faculty information.",
            "keywords": ["engineering"],
        },
    ]

    results = hybrid_retrieve("Engineering", chunks, intent="faculty_info")

    assert results[0]["id"] == "faculties:engineering"


def test_works_when_sklearn_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr("controllers.rag.hybrid_retriever._tfidf_scores", lambda *_args: None)

    results = hybrid_retrieve("cafeteria", _chunks(), intent="room_location")

    assert results
    assert results[0]["id"] == "rooms:cafeteria"
    assert results[0]["score_details"]["tfidf"] == 0.0
