"""Tests for RAG chatbot evaluation helpers."""

import json

from controllers.rag.evaluator import run_chatbot_evaluation


class FakeController:
    def __init__(self, responses: dict[str, dict]) -> None:
        self.responses = responses
        self.questions: list[str] = []

    def answer_question(self, question: str) -> dict:
        self.questions.append(question)
        return self.responses[question]


def _questions_file(tmp_path):
    path = tmp_path / "questions.json"
    path.write_text(
        json.dumps(
            {
                "questions": [
                    {
                        "id": "q1",
                        "question": "Tell me about faculties",
                        "language": "en",
                        "expected_sources": ["faculties"],
                    },
                    {
                        "id": "q2",
                        "question": "Where is the cafeteria?",
                        "language": "en",
                        "expected_sources": ["rooms"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def test_loads_evaluation_questions_and_runs_controller(tmp_path) -> None:
    questions_path = _questions_file(tmp_path)
    controller = FakeController(
        {
            "Tell me about faculties": {
                "answer": "Faculty answer",
                "route": "rag_fallback",
                "confidence": "high",
                "sources": [{"source": "faculties", "title": "Engineering"}],
            },
            "Where is the cafeteria?": {
                "answer": "Cafeteria answer",
                "route": "rag_fallback",
                "confidence": "medium",
                "sources": [{"source": "rooms", "title": "Cafeteria"}],
            },
        }
    )

    summary = run_chatbot_evaluation(controller, questions_path)

    assert controller.questions == ["Tell me about faculties", "Where is the cafeteria?"]
    assert summary["total"] == 2
    assert len(summary["results"]) == 2


def test_marks_passed_when_answer_and_expected_source_exist(tmp_path) -> None:
    controller = FakeController(
        {
            "Tell me about faculties": {
                "answer": "Faculty answer",
                "route": "rag_groq",
                "confidence": "high",
                "sources": [{"source": "faculties", "title": "Engineering"}],
            },
            "Where is the cafeteria?": {
                "answer": "Cafeteria answer",
                "route": "rag_fallback",
                "confidence": "medium",
                "sources": [{"source": "rooms", "title": "Cafeteria"}],
            },
        }
    )

    summary = run_chatbot_evaluation(controller, _questions_file(tmp_path))

    assert summary["passed"] == 2
    assert summary["failed"] == 0
    assert all(result["passed"] for result in summary["results"])


def test_marks_failed_for_no_context(tmp_path) -> None:
    controller = FakeController(
        {
            "Tell me about faculties": {
                "answer": "",
                "route": "no_context",
                "confidence": "low",
                "sources": [],
            },
            "Where is the cafeteria?": {
                "answer": "Cafeteria answer",
                "route": "rag_fallback",
                "confidence": "medium",
                "sources": [{"source": "rooms", "title": "Cafeteria"}],
            },
        }
    )

    summary = run_chatbot_evaluation(controller, _questions_file(tmp_path))

    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["results"][0]["passed"] is False


def test_returns_correct_summary_counts_for_source_mismatch(tmp_path) -> None:
    controller = FakeController(
        {
            "Tell me about faculties": {
                "answer": "Faculty answer",
                "route": "rag_fallback",
                "confidence": "medium",
                "sources": [{"source": "events", "title": "Open Day"}],
            },
            "Where is the cafeteria?": {
                "answer": "Cafeteria answer",
                "route": "rag_fallback",
                "confidence": "medium",
                "sources": [{"source": "rooms", "title": "Cafeteria"}],
            },
        }
    )

    summary = run_chatbot_evaluation(controller, _questions_file(tmp_path))

    assert summary["total"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1
