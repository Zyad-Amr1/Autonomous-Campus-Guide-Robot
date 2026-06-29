"""Tests for RAG reranking."""

from controllers.rag.reranker import rerank_chunks


def test_boosts_title_match() -> None:
    chunks = [
        {
            "id": "faq:engineering",
            "source": "faq",
            "title": "Engineering clubs",
            "content": "Club information.",
            "final_score": 20,
        },
        {
            "id": "faculties:engineering",
            "source": "faculties",
            "title": "Faculty of Engineering",
            "content": "Engineering faculty information.",
            "final_score": 18,
        },
    ]

    results = rerank_chunks("Faculty of Engineering", chunks, intent="faculty_info")

    assert results[0]["id"] == "faculties:engineering"


def test_boosts_intent_source_match() -> None:
    chunks = [
        {
            "id": "rooms:engineering",
            "source": "rooms",
            "title": "Engineering",
            "content": "Engineering hall location.",
            "final_score": 25,
        },
        {
            "id": "faculties:engineering",
            "source": "faculties",
            "title": "Engineering",
            "content": "Engineering faculty information.",
            "final_score": 24,
        },
    ]

    results = rerank_chunks("Engineering", chunks, intent="faculty_info")

    assert results[0]["id"] == "faculties:engineering"


def test_penalizes_unrelated_chunks() -> None:
    chunks = [
        {
            "id": "events:open-day",
            "source": "events",
            "title": "Open Day",
            "content": "Student clubs and admissions event.",
            "final_score": 10,
        }
    ]

    assert rerank_chunks("cafeteria location", chunks, intent="room_location") == []


def test_returns_only_limit_results() -> None:
    chunks = [
        {
            "id": f"faq:{index}",
            "source": "faq",
            "title": f"Engineering FAQ {index}",
            "content": "Engineering information.",
            "final_score": 20 + index,
        }
        for index in range(5)
    ]

    results = rerank_chunks("Engineering", chunks, intent="faculty_info", limit=2)

    assert len(results) == 2
    assert results[0]["final_score"] >= results[1]["final_score"]
