"""Evaluation helpers for the public RAG chatbot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_chatbot_evaluation(
    controller,
    questions_path: str | Path = "data/chatbot_eval_questions.json",
) -> dict[str, Any]:
    """Run prepared questions through a chatbot controller and summarize results."""
    questions = _load_questions(questions_path)
    results = []
    for item in questions:
        question = str(item.get("question", "")).strip()
        expected_sources = [str(source) for source in item.get("expected_sources", [])]
        try:
            response = controller.answer_question(question)
        except Exception as error:
            results.append(
                {
                    "id": item.get("id", ""),
                    "question": question,
                    "answer": "",
                    "route": "error",
                    "confidence": "low",
                    "sources": [],
                    "passed": False,
                    "notes": f"Controller error: {error}",
                }
            )
            continue

        sources = response.get("sources") or []
        passed, notes = _evaluate_response(response, expected_sources)
        results.append(
            {
                "id": item.get("id", ""),
                "question": question,
                "answer": str(response.get("answer", "")),
                "route": str(response.get("route", "")),
                "confidence": str(response.get("confidence", "")),
                "sources": sources,
                "passed": passed,
                "notes": notes,
            }
        )

    passed_count = sum(1 for result in results if result["passed"])
    total = len(results)
    return {
        "total": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "results": results,
    }


def _load_questions(path: str | Path) -> list[dict[str, Any]]:
    questions_path = Path(path)
    payload = json.loads(questions_path.read_text(encoding="utf-8"))
    questions = payload.get("questions", [])
    if not isinstance(questions, list):
        return []
    return [question for question in questions if isinstance(question, dict)]


def _evaluate_response(response: dict[str, Any], expected_sources: list[str]) -> tuple[bool, str]:
    route = str(response.get("route", ""))
    answer = str(response.get("answer", "")).strip()
    sources = response.get("sources") or []
    notes: list[str] = []

    if route == "no_context":
        notes.append("No context route.")
    if not answer:
        notes.append("Empty answer.")
    if expected_sources and not sources:
        notes.append("Expected sources were not returned.")

    if expected_sources and sources:
        returned_sources = {str(source.get("source", "")).casefold() for source in sources}
        expected = {source.casefold() for source in expected_sources}
        if returned_sources.isdisjoint(expected):
            notes.append("Returned sources do not match expected source types.")

    passed = not notes
    return passed, "Passed." if passed else " ".join(notes)
