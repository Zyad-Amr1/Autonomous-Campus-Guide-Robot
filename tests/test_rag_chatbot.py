from services import rag_chatbot


def _database_match(source_table="faculties", score=90, title="Engineering"):
    return {
        "source": "database",
        "source_table": source_table,
        "title": title,
        "content": "Engineering programs and robotics labs.",
        "score": score,
        "raw": {"id": 1},
    }


def _website_result():
    return {
        "source": "ecu_website",
        "title": "Faculty of Engineering and Technology",
        "url": "https://ecu.edu.eg/faculties/engineering-and-technology/",
        "path": "faculties/engineering-and-technology/",
        "content": "Official ECU engineering website content.",
    }


def test_database_strong_match_uses_database_context(monkeypatch, tmp_path):
    monkeypatch.setattr(
        rag_chatbot,
        "retrieve_from_database",
        lambda question, db_path: [_database_match()],
    )
    monkeypatch.setattr(rag_chatbot, "retrieve_from_website", lambda question: None)
    monkeypatch.setattr(
        rag_chatbot,
        "ask_gemini",
        lambda question, context: {"ok": True, "answer": "DB answer", "error_type": None},
    )

    result = rag_chatbot.get_chatbot_response("Tell me about engineering", tmp_path)

    assert result["source_used"] == "database"
    assert result["had_context"] is True
    assert result["answer"] == "DB answer"


def test_database_strong_match_calls_gemini(monkeypatch, tmp_path):
    calls = {}
    monkeypatch.setattr(
        rag_chatbot,
        "retrieve_from_database",
        lambda question, db_path: [_database_match()],
    )

    def fake_ask(question, context):
        calls["question"] = question
        calls["context"] = context
        return {"ok": True, "answer": "Gemini answer", "error_type": None}

    monkeypatch.setattr(rag_chatbot, "ask_gemini", fake_ask)

    rag_chatbot.get_chatbot_response("Tell me about engineering", tmp_path)

    assert calls["question"] == "Tell me about engineering"
    assert calls["context"][0]["source_table"] == "faculties"


def test_weak_database_match_falls_back_to_website(monkeypatch, tmp_path):
    monkeypatch.setattr(
        rag_chatbot,
        "retrieve_from_database",
        lambda question, db_path: [_database_match(score=50)],
    )
    monkeypatch.setattr(rag_chatbot, "retrieve_from_website", lambda question: _website_result())
    monkeypatch.setattr(
        rag_chatbot,
        "ask_gemini",
        lambda question, context: {
            "ok": True,
            "answer": "Website answer",
            "error_type": None,
        },
    )

    result = rag_chatbot.get_chatbot_response("Tell me about engineering", tmp_path)

    assert result["source_used"] == "ecu_website"
    assert result["answer"] == "Website answer"


def test_website_context_calls_gemini(monkeypatch, tmp_path):
    calls = {}
    monkeypatch.setattr(rag_chatbot, "retrieve_from_database", lambda question, db_path: [])
    monkeypatch.setattr(rag_chatbot, "retrieve_from_website", lambda question: _website_result())

    def fake_ask(question, context):
        calls["context"] = context
        return {"ok": True, "answer": "Website answer", "error_type": None}

    monkeypatch.setattr(rag_chatbot, "ask_gemini", fake_ask)

    rag_chatbot.get_chatbot_response("engineering website", tmp_path)

    assert calls["context"][0]["source"] == "ecu_website"


def test_no_database_and_no_website_returns_none_source(monkeypatch, tmp_path):
    monkeypatch.setattr(rag_chatbot, "retrieve_from_database", lambda question, db_path: [])
    monkeypatch.setattr(rag_chatbot, "retrieve_from_website", lambda question: None)

    result = rag_chatbot.get_chatbot_response("unknown topic", tmp_path)

    assert result["source_used"] == "none"
    assert result["had_context"] is False
    assert "I do not have enough ECU information" in result["answer"]


def test_no_context_does_not_call_gemini(monkeypatch, tmp_path):
    calls = {"gemini": 0}
    monkeypatch.setattr(rag_chatbot, "retrieve_from_database", lambda question, db_path: [])
    monkeypatch.setattr(rag_chatbot, "retrieve_from_website", lambda question: None)

    def fake_ask(question, context):
        calls["gemini"] += 1
        return {"ok": True, "answer": "Should not happen", "error_type": None}

    monkeypatch.setattr(rag_chatbot, "ask_gemini", fake_ask)

    rag_chatbot.get_chatbot_response("unknown topic", tmp_path)

    assert calls["gemini"] == 0


def test_gemini_failure_with_database_context_returns_database_fallback(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        rag_chatbot,
        "retrieve_from_database",
        lambda question, db_path: [_database_match(title="Robotics Lab")],
    )
    monkeypatch.setattr(
        rag_chatbot,
        "ask_gemini",
        lambda question, context: {"ok": False, "answer": "", "error_type": "api_error"},
    )

    result = rag_chatbot.get_chatbot_response("Tell me about robotics", tmp_path)

    assert result["gemini_status"] == "api_error"
    assert result["answer"].startswith("Based on ECU records: Robotics Lab.")


def test_gemini_failure_with_website_context_returns_website_fallback(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(rag_chatbot, "retrieve_from_database", lambda question, db_path: [])
    monkeypatch.setattr(rag_chatbot, "retrieve_from_website", lambda question: _website_result())
    monkeypatch.setattr(
        rag_chatbot,
        "ask_gemini",
        lambda question, context: {
            "ok": False,
            "answer": "",
            "error_type": "rate_limited",
        },
    )

    result = rag_chatbot.get_chatbot_response("engineering", tmp_path)

    assert result["gemini_status"] == "rate_limited"
    assert result["answer"].startswith("Based on the ECU website:")


def test_matched_rooms_populated_from_room_matches(monkeypatch, tmp_path):
    monkeypatch.setattr(
        rag_chatbot,
        "retrieve_from_database",
        lambda question, db_path: [
            _database_match(source_table="rooms", title="Main Cafeteria")
        ],
    )
    monkeypatch.setattr(
        rag_chatbot,
        "ask_gemini",
        lambda question, context: {"ok": True, "answer": "Room answer", "error_type": None},
    )

    result = rag_chatbot.get_chatbot_response("cafeteria", tmp_path)

    assert result["matched_rooms"] == [
        {
            "title": "Main Cafeteria",
            "content": "Engineering programs and robotics labs.",
            "score": 90,
        }
    ]


def test_matched_professors_populated_from_professor_matches(monkeypatch, tmp_path):
    monkeypatch.setattr(
        rag_chatbot,
        "retrieve_from_database",
        lambda question, db_path: [
            _database_match(source_table="professors", title="Dr. Mona Samir")
        ],
    )
    monkeypatch.setattr(
        rag_chatbot,
        "ask_gemini",
        lambda question, context: {
            "ok": True,
            "answer": "Professor answer",
            "error_type": None,
        },
    )

    result = rag_chatbot.get_chatbot_response("professors", tmp_path)

    assert result["matched_professors"] == [
        {
            "title": "Dr. Mona Samir",
            "content": "Engineering programs and robotics labs.",
            "score": 90,
        }
    ]


def test_arabic_no_context_response_is_arabic(monkeypatch, tmp_path):
    monkeypatch.setattr(rag_chatbot, "retrieve_from_database", lambda question, db_path: [])
    monkeypatch.setattr(rag_chatbot, "retrieve_from_website", lambda question: None)

    result = rag_chatbot.get_chatbot_response("ما هي التفاصيل؟", tmp_path)

    assert "لا أملك معلومات كافية" in result["answer"]
    assert result["source_used"] == "none"


def test_sources_are_clean_for_database(monkeypatch, tmp_path):
    monkeypatch.setattr(
        rag_chatbot,
        "retrieve_from_database",
        lambda question, db_path: [_database_match(source_table="rooms")],
    )
    monkeypatch.setattr(
        rag_chatbot,
        "ask_gemini",
        lambda question, context: {"ok": True, "answer": "Answer", "error_type": None},
    )

    result = rag_chatbot.get_chatbot_response("rooms", tmp_path)

    assert result["sources"] == [
        {
            "source": "database",
            "title": "Engineering",
            "source_table": "rooms",
            "score": 90,
        }
    ]


def test_sources_are_clean_for_website(monkeypatch, tmp_path):
    monkeypatch.setattr(rag_chatbot, "retrieve_from_database", lambda question, db_path: [])
    monkeypatch.setattr(rag_chatbot, "retrieve_from_website", lambda question: _website_result())
    monkeypatch.setattr(
        rag_chatbot,
        "ask_gemini",
        lambda question, context: {"ok": True, "answer": "Answer", "error_type": None},
    )

    result = rag_chatbot.get_chatbot_response("engineering", tmp_path)

    assert result["sources"] == [
        {
            "source": "ecu_website",
            "title": "Faculty of Engineering and Technology",
            "url": "https://ecu.edu.eg/faculties/engineering-and-technology/",
        }
    ]


def test_no_real_api_or_website_calls(monkeypatch, tmp_path):
    calls = {"website": 0, "gemini": 0}
    monkeypatch.setattr(
        rag_chatbot,
        "retrieve_from_database",
        lambda question, db_path: [_database_match()],
    )

    def fake_website(question):
        calls["website"] += 1
        return _website_result()

    def fake_gemini(question, context):
        calls["gemini"] += 1
        return {"ok": True, "answer": "Answer", "error_type": None}

    monkeypatch.setattr(rag_chatbot, "retrieve_from_website", fake_website)
    monkeypatch.setattr(rag_chatbot, "ask_gemini", fake_gemini)

    rag_chatbot.get_chatbot_response("engineering", tmp_path)

    assert calls["website"] == 0
    assert calls["gemini"] == 1


def test_database_answer_logs_database_source(monkeypatch, tmp_path):
    logged_calls = {}
    monkeypatch.setattr(
        rag_chatbot,
        "retrieve_from_database",
        lambda question, db_path: [_database_match()],
    )
    monkeypatch.setattr(
        rag_chatbot,
        "ask_gemini",
        lambda question, context: {"ok": True, "answer": "Answer", "error_type": None},
    )

    def fake_log(db_path, question, source_used, had_context, timestamp=None):
        logged_calls["source_used"] = source_used
        logged_calls["had_context"] = had_context
        return True

    monkeypatch.setattr(rag_chatbot, "log_chatbot_interaction", fake_log)

    result = rag_chatbot.get_chatbot_response("engineering", tmp_path)

    assert logged_calls == {"source_used": "database", "had_context": True}
    assert result["logged"] is True


def test_website_answer_logs_website_source(monkeypatch, tmp_path):
    logged_calls = {}
    monkeypatch.setattr(rag_chatbot, "retrieve_from_database", lambda question, db_path: [])
    monkeypatch.setattr(rag_chatbot, "retrieve_from_website", lambda question: _website_result())
    monkeypatch.setattr(
        rag_chatbot,
        "ask_gemini",
        lambda question, context: {"ok": True, "answer": "Answer", "error_type": None},
    )

    def fake_log(db_path, question, source_used, had_context, timestamp=None):
        logged_calls["source_used"] = source_used
        logged_calls["had_context"] = had_context
        return True

    monkeypatch.setattr(rag_chatbot, "log_chatbot_interaction", fake_log)

    result = rag_chatbot.get_chatbot_response("engineering", tmp_path)

    assert logged_calls == {"source_used": "ecu_website", "had_context": True}
    assert result["logged"] is True


def test_no_context_answer_logs_none_source(monkeypatch, tmp_path):
    logged_calls = {}
    monkeypatch.setattr(rag_chatbot, "retrieve_from_database", lambda question, db_path: [])
    monkeypatch.setattr(rag_chatbot, "retrieve_from_website", lambda question: None)

    def fake_log(db_path, question, source_used, had_context, timestamp=None):
        logged_calls["source_used"] = source_used
        logged_calls["had_context"] = had_context
        return True

    monkeypatch.setattr(rag_chatbot, "log_chatbot_interaction", fake_log)

    result = rag_chatbot.get_chatbot_response("unknown", tmp_path)

    assert logged_calls == {"source_used": "none", "had_context": False}
    assert result["logged"] is True


def test_logging_failure_does_not_break_chatbot_response(monkeypatch, tmp_path):
    monkeypatch.setattr(
        rag_chatbot,
        "retrieve_from_database",
        lambda question, db_path: [_database_match()],
    )
    monkeypatch.setattr(
        rag_chatbot,
        "ask_gemini",
        lambda question, context: {"ok": True, "answer": "Answer", "error_type": None},
    )
    monkeypatch.setattr(
        rag_chatbot,
        "log_chatbot_interaction",
        lambda *args, **kwargs: False,
    )

    result = rag_chatbot.get_chatbot_response("engineering", tmp_path)

    assert result["answer"] == "Answer"
    assert result["logged"] is False


def test_returned_dict_includes_logged_boolean(monkeypatch, tmp_path):
    monkeypatch.setattr(rag_chatbot, "retrieve_from_database", lambda question, db_path: [])
    monkeypatch.setattr(rag_chatbot, "retrieve_from_website", lambda question: None)
    monkeypatch.setattr(
        rag_chatbot,
        "log_chatbot_interaction",
        lambda *args, **kwargs: True,
    )

    result = rag_chatbot.get_chatbot_response("unknown", tmp_path)

    assert isinstance(result["logged"], bool)
