"""Headless tests for the public chat screen."""

import os
import threading
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QDialog, QLineEdit, QMainWindow, QPushButton, QScrollArea

from ui.public.screens.chat_screen import ChatScreen


class FakeChatController:
    def __init__(self) -> None:
        self.questions: list[str] = []
        self.memory_cleared = False
        self.route = "database_context"
        self.sources = [{"source": "faq", "title": "Test", "score": 72}]

    def answer_question(self, question: str) -> dict:
        self.questions.append(question)
        return {
            "answer": f"Dynamic answer for: {question}",
            "had_context": True,
            "source_used": "database",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": self.sources,
            "gemini_status": "ok",
            "error": None,
            "logged": True,
        }

    def clear_memory(self) -> None:
        self.memory_cleared = True


class SlowFakeChatController(FakeChatController):
    def answer_question(self, question: str) -> dict:
        time.sleep(0.1)
        return super().answer_question(question)


class BlockingFakeChatController(FakeChatController):
    def __init__(self) -> None:
        super().__init__()
        self.started = threading.Event()
        self.release = threading.Event()

    def answer_question(self, question: str) -> dict:
        self.questions.append(question)
        self.started.set()
        self.release.wait(timeout=2)
        return {
            "answer": f"Released answer for: {question}",
            "had_context": True,
            "source_used": "database",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": self.sources,
            "gemini_status": "ok",
            "error": None,
            "logged": True,
        }


class ThreadRecordingFakeChatController(FakeChatController):
    def __init__(self) -> None:
        super().__init__()
        self.answer_thread_id: int | None = None

    def answer_question(self, question: str) -> dict:
        self.answer_thread_id = threading.get_ident()
        return super().answer_question(question)


class FailingFakeChatController(FakeChatController):
    def answer_question(self, question: str) -> dict:
        self.questions.append(question)
        raise RuntimeError("boom")


def _get_application() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _process_until(predicate, timeout_ms: int = 2000) -> None:
    application = _get_application()
    deadline = timeout_ms
    while deadline > 0 and not predicate():
        application.processEvents()
        time.sleep(0.01)
        deadline -= 10
    application.processEvents()


def _row_for_label(screen: ChatScreen, label: QLabel):
    return screen._message_rows[label]


def _is_left_aligned(screen: ChatScreen, label: QLabel) -> bool:
    row = _row_for_label(screen, label).layout()
    return row.itemAt(0).widget() is label and row.itemAt(1).spacerItem() is not None


def _is_right_aligned(screen: ChatScreen, label: QLabel) -> bool:
    row = _row_for_label(screen, label).layout()
    return row.itemAt(0).spacerItem() is not None and row.itemAt(1).widget() is label


def _is_inside_messages_container(screen: ChatScreen, widget) -> bool:
    current = widget
    while current is not None:
        if current is screen.chat_messages_container:
            return True
        current = current.parentWidget()
    return False


def _assert_message_is_not_top_level(screen: ChatScreen, label: QLabel) -> None:
    application = _get_application()
    row_widget = _row_for_label(screen, label)
    assert row_widget not in application.topLevelWidgets()
    assert label not in application.topLevelWidgets()
    assert not isinstance(row_widget, (QDialog, QMainWindow))
    assert not isinstance(label, (QDialog, QMainWindow))
    assert _is_inside_messages_container(screen, row_widget)
    assert _is_inside_messages_container(screen, label)


def test_chat_screen_can_be_created() -> None:
    application = _get_application()
    screen = ChatScreen(controller=FakeChatController())
    try:
        assert application is not None
        assert screen.objectName() == "chat_screen"
    finally:
        screen.close()


def test_chat_required_widgets_exist() -> None:
    application = _get_application()
    screen = ChatScreen(controller=FakeChatController())
    try:
        assert application is not None
        assert screen.findChild(QScrollArea, "chat_messages_area") is not None
        assert screen.findChild(QLineEdit, "chat_input") is not None
        assert screen.findChild(QPushButton, "chat_send_button") is not None
        assert screen.findChild(QPushButton, "chat_clear_button") is not None
        assert screen.findChild(QPushButton, "chat_retry_button") is not None
        assert screen.findChild(QPushButton, "chat_suggestion_1") is not None
        assert screen.findChild(QPushButton, "chat_suggestion_2") is not None
        assert screen.findChild(QPushButton, "chat_suggestion_3") is not None
        assert screen.findChild(QPushButton, "chat_suggestion_4") is not None
        assert screen.findChild(QLabel, "chat_status_label") is not None
        assert screen.findChild(QLabel, "chat_thinking_label") is not None
    finally:
        screen.close()


def test_sending_message_adds_user_and_bot_messages() -> None:
    application = _get_application()
    controller = FakeChatController()
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        initial_count = len(screen.message_labels)
        screen.chat_input.setText("Where is cafeteria?")
        screen.send_message()
        _process_until(lambda: "Dynamic answer" in screen.message_labels[-1].text())
        assert controller.questions == ["Where is cafeteria?"]
        assert screen.chat_input.text() == ""
        assert len(screen.message_labels) == initial_count + 2
        assert screen.message_labels[-2].property("sender") == "user"
        assert screen.message_labels[-1].property("sender") == "bot"
        assert "Dynamic answer" in screen.message_labels[-1].text()
        assert _is_right_aligned(screen, screen.message_labels[-2])
        assert _is_left_aligned(screen, screen.message_labels[-1])
        _assert_message_is_not_top_level(screen, screen.message_labels[-2])
        _assert_message_is_not_top_level(screen, screen.message_labels[-1])
    finally:
        screen.close()


def test_sending_message_does_not_create_top_level_window() -> None:
    application = _get_application()
    controller = FakeChatController()
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        top_levels_before = set(application.topLevelWidgets())
        screen.chat_input.setText("Who are the professors?")
        screen.send_message()
        _process_until(lambda: "Dynamic answer" in screen.message_labels[-1].text())
        top_levels_after = set(application.topLevelWidgets())

        assert top_levels_after == top_levels_before
        for label in [*screen.message_labels, *screen.source_labels]:
            _assert_message_is_not_top_level(screen, label)
    finally:
        screen.close()


def test_matched_rooms_create_quick_action_button() -> None:
    application = _get_application()
    controller = FakeChatController()

    def room_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": "The cafeteria is in the Student Center.",
            "had_context": True,
            "source_used": "database",
            "matched_rooms": [
                {"title": "Main Cafeteria", "content": "Student Center", "score": 92}
            ],
            "matched_professors": [],
            "sources": [],
            "gemini_status": "ok",
            "error": None,
            "logged": True,
        }

    controller.answer_question = room_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Where is cafeteria?")
        screen.send_message()
        _process_until(lambda: len(screen.quick_action_buttons) == 1)
        assert screen.quick_action_buttons[0].text() == "Open room: Main Cafeteria"
        screen.quick_action_buttons[0].click()
        assert screen.chat_input.text() == "Tell me more about room Main Cafeteria"
    finally:
        screen.close()


def test_matched_professors_create_quick_action_button() -> None:
    application = _get_application()
    controller = FakeChatController()

    def professor_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": "Dr. Mona Samir teaches robotics.",
            "had_context": True,
            "source_used": "database",
            "matched_rooms": [],
            "matched_professors": [
                {"title": "Dr. Mona Samir", "content": "Robotics", "score": 90}
            ],
            "sources": [],
            "gemini_status": "ok",
            "error": None,
            "logged": True,
        }

    controller.answer_question = professor_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Who are the professors?")
        screen.send_message()
        _process_until(lambda: len(screen.quick_action_buttons) == 1)
        assert screen.quick_action_buttons[0].text() == "Professor: Dr. Mona Samir"
    finally:
        screen.close()


def test_no_context_source_indicator_is_displayed() -> None:
    application = _get_application()
    controller = FakeChatController()

    def no_context_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": f"Dynamic answer for: {question}",
            "had_context": False,
            "source_used": "none",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": [],
            "gemini_status": "not_called",
            "error": None,
            "logged": True,
        }

    controller.answer_question = no_context_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Unknown topic")
        screen.send_message()
        _process_until(lambda: "Dynamic answer" in screen.message_labels[-1].text())
        assert screen.source_labels
        assert "Source: No matching ECU context found" in screen.source_labels[-1].text()
    finally:
        screen.close()


def test_no_context_answer_is_displayed_as_assistant_bubble() -> None:
    application = _get_application()
    controller = FakeChatController()
    controller.route = "no_context"
    controller.sources = []

    def no_context_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": "I do not have enough information about that yet. Please sync or add university data in the Data section.",
            "had_context": False,
            "source_used": "none",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": [],
            "gemini_status": "not_called",
            "error": None,
            "logged": True,
        }

    controller.answer_question = no_context_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Unknown topic")
        screen.send_message()
        _process_until(lambda: "I do not have enough information" in screen.message_labels[-1].text())
        assert screen.message_labels[-2].property("sender") == "user"
        assert screen.message_labels[-1].property("sender") == "bot"
        assert screen.message_labels[-1].text() != "?"
        assert "Source: No matching ECU context found" in screen.source_labels[-1].text()
        assert screen.chat_status_label.text() == "No ECU context found"
    finally:
        screen.close()


def test_useless_controller_answer_is_displayed_as_readable_message() -> None:
    application = _get_application()
    controller = FakeChatController()
    controller.route = "no_context"
    controller.sources = []

    def useless_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": "?",
            "had_context": False,
            "source_used": "none",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": [],
            "gemini_status": "not_called",
            "error": None,
            "logged": True,
        }

    controller.answer_question = useless_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Unknown topic")
        screen.send_message()
        _process_until(lambda: "I could not generate a useful answer" in screen.message_labels[-1].text())
        assert screen.message_labels[-1].text() != "?"
        assert screen.message_labels[-1].text() == "Sorry, I could not generate a useful answer. Please try again."
    finally:
        screen.close()


def test_status_label_shows_route_and_source_count() -> None:
    application = _get_application()
    controller = FakeChatController()
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Where is cafeteria?")
        screen.send_message()
        _process_until(lambda: "Answered from ECU records" in screen.chat_status_label.text())
        assert screen.chat_status_label.text() == "Answered from ECU records"
    finally:
        screen.close()


def test_status_label_shows_website_source() -> None:
    application = _get_application()
    controller = FakeChatController()

    def auto_sync_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": "Website answer",
            "had_context": True,
            "source_used": "ecu_website",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": [{"source": "ecu_website", "title": "One", "url": "https://ecu.edu.eg/"}],
            "gemini_status": "ok",
            "error": None,
            "logged": True,
        }

    controller.answer_question = auto_sync_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Tell me about faculties")
        screen.send_message()
        _process_until(lambda: screen.chat_status_label.text() == "Answered from ecu.edu.eg")
        assert screen.chat_status_label.text() == "Answered from ecu.edu.eg"
    finally:
        screen.close()


def test_database_source_displays_ecu_records_indicator() -> None:
    application = _get_application()
    screen = ChatScreen(controller=FakeChatController())
    try:
        assert application is not None
        screen.chat_input.setText("Where is cafeteria?")
        screen.send_message()
        _process_until(lambda: screen.source_labels)
        assert "Source: ECU records" in screen.source_labels[-1].text()
    finally:
        screen.close()


def test_website_source_displays_ecu_website_indicator() -> None:
    application = _get_application()
    controller = FakeChatController()

    def website_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": "Website answer",
            "had_context": True,
            "source_used": "ecu_website",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": [
                {
                    "source": "ecu_website",
                    "title": "Faculty of Engineering and Technology",
                    "url": "https://ecu.edu.eg/faculties/engineering-and-technology/",
                }
            ],
            "gemini_status": "ok",
            "error": None,
            "logged": True,
        }

    controller.answer_question = website_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Tell me about engineering")
        screen.send_message()
        _process_until(lambda: screen.source_labels)
        assert "Source: ecu.edu.eg" in screen.source_labels[-1].text()
    finally:
        screen.close()


def test_gemini_ok_message_appears_in_source_indicator() -> None:
    application = _get_application()
    screen = ChatScreen(controller=FakeChatController())
    try:
        assert application is not None
        screen.chat_input.setText("Where is cafeteria?")
        screen.send_message()
        _process_until(lambda: screen.source_labels)
        assert "AI answer generated from retrieved ECU context" in screen.source_labels[-1].text()
    finally:
        screen.close()


def test_fallback_message_appears_when_gemini_not_ok_with_context() -> None:
    application = _get_application()
    controller = FakeChatController()

    def fallback_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": "Based on ECU records: Cafeteria.",
            "had_context": True,
            "source_used": "database",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": [{"source": "database", "source_table": "rooms", "title": "Cafeteria", "score": 90}],
            "gemini_status": "rate_limited",
            "error": "rate_limited",
            "logged": True,
        }

    controller.answer_question = fallback_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Where is cafeteria?")
        screen.send_message()
        _process_until(lambda: screen.source_labels)
        assert "AI service unavailable - showing best available ECU match" in screen.source_labels[-1].text()
    finally:
        screen.close()


def test_database_source_details_are_displayed() -> None:
    application = _get_application()
    controller = FakeChatController()

    def database_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": "Professor answer",
            "had_context": True,
            "source_used": "database",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": [
                {
                    "source": "database",
                    "source_table": "professors",
                    "title": "Ass. Prof. Dr. Marwa Taher",
                    "score": 88,
                    "id": "professors:1",
                }
            ],
            "gemini_status": "ok",
            "error": None,
            "logged": True,
        }

    controller.answer_question = database_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Who are the professors?")
        screen.send_message()
        _process_until(lambda: screen.source_labels)
        assert "- professors: Ass. Prof. Dr. Marwa Taher" in screen.source_labels[-1].text()
        assert "professors:1" not in screen.source_labels[-1].text()
    finally:
        screen.close()


def test_website_source_details_are_displayed() -> None:
    application = _get_application()
    controller = FakeChatController()

    def website_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": "Engineering answer",
            "had_context": True,
            "source_used": "ecu_website",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": [
                {
                    "source": "ecu_website",
                    "title": "Faculty of Engineering and Technology",
                    "url": "https://ecu.edu.eg/faculties/engineering-and-technology/",
                }
            ],
            "gemini_status": "ok",
            "error": None,
            "logged": True,
        }

    controller.answer_question = website_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Tell me about engineering")
        screen.send_message()
        _process_until(lambda: screen.source_labels)
        assert "- ecu.edu.eg: Faculty of Engineering and Technology" in screen.source_labels[-1].text()
    finally:
        screen.close()


def test_source_details_are_limited_to_three() -> None:
    application = _get_application()
    controller = FakeChatController()

    def many_sources_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": "Answer",
            "had_context": True,
            "source_used": "database",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": [
                {"source": "database", "source_table": "rooms", "title": "Room A", "score": 90},
                {"source": "database", "source_table": "rooms", "title": "Room B", "score": 80},
                {"source": "database", "source_table": "rooms", "title": "Room C", "score": 70},
                {"source": "database", "source_table": "rooms", "title": "Room D", "score": 65},
            ],
            "gemini_status": "ok",
            "error": None,
            "logged": True,
        }

    controller.answer_question = many_sources_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("rooms")
        screen.send_message()
        _process_until(lambda: screen.source_labels)
        text = screen.source_labels[-1].text()
        assert "Room A" in text
        assert "Room B" in text
        assert "Room C" in text
        assert "Room D" not in text
    finally:
        screen.close()


def test_raw_json_debug_and_api_key_are_not_displayed_in_sources() -> None:
    application = _get_application()
    controller = FakeChatController()

    def secret_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": "Answer",
            "had_context": True,
            "source_used": "database",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": [
                {
                    "source": "database",
                    "source_table": "rooms",
                    "title": "Cafeteria",
                    "score": 90,
                    "raw": {"api_key": "SECRET_KEY"},
                    "debug": {"prompt": "hidden"},
                }
            ],
            "gemini_status": "ok",
            "error": None,
            "logged": True,
        }

    controller.answer_question = secret_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("cafeteria")
        screen.send_message()
        _process_until(lambda: screen.source_labels)
        text = screen.source_labels[-1].text()
        assert "SECRET_KEY" not in text
        assert "api_key" not in text
        assert "debug" not in text
        assert "prompt" not in text
        assert "{" not in text
    finally:
        screen.close()


def test_thinking_state_disables_and_reenables_send_button() -> None:
    application = _get_application()
    screen = ChatScreen(controller=SlowFakeChatController())
    try:
        assert application is not None
        screen.chat_input.setText("Where is cafeteria?")
        screen.send_message()
        assert screen.chat_send_button.isEnabled() is False
        assert screen.chat_thinking_label.isHidden() is False
        assert screen.chat_thinking_label.text() == "Thinking..."
        _process_until(lambda: screen.chat_send_button.isEnabled(), timeout_ms=3000)
        assert screen.chat_send_button.isEnabled() is True
        assert screen.chat_thinking_label.isHidden() is True
    finally:
        screen.close()


def test_message_send_is_responsive_while_worker_is_running() -> None:
    application = _get_application()
    controller = BlockingFakeChatController()
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        initial_count = len(screen.message_labels)
        screen.chat_input.setText("Who are the professors?")
        screen.send_message()
        _process_until(lambda: controller.started.is_set())

        assert controller.questions == ["Who are the professors?"]
        assert screen.chat_send_button.isEnabled() is False
        assert len(screen.message_labels) == initial_count + 2
        assert screen.message_labels[-2].text() == "Who are the professors?"
        assert screen.message_labels[-2].property("sender") == "user"
        assert screen.message_labels[-1].text() == "Thinking..."
        assert screen.message_labels[-1].property("sender") == "bot"
        assert _is_right_aligned(screen, screen.message_labels[-2])
        assert _is_left_aligned(screen, screen.message_labels[-1])

        controller.release.set()
        _process_until(lambda: screen.chat_send_button.isEnabled(), timeout_ms=3000)
        assert screen.message_labels[-1].text().startswith("Released answer for:")
        assert screen.chat_status_label.text() == "Answered from ECU records"
    finally:
        controller.release.set()
        screen.close()


def test_message_send_does_not_call_controller_on_main_thread() -> None:
    application = _get_application()
    controller = ThreadRecordingFakeChatController()
    main_thread_id = threading.get_ident()
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Tell me about faculties")
        screen.send_message()
        _process_until(lambda: screen.chat_send_button.isEnabled(), timeout_ms=3000)

        assert controller.questions == ["Tell me about faculties"]
        assert controller.answer_thread_id is not None
        assert controller.answer_thread_id != main_thread_id
        assert screen.message_labels[-1].text() == "Dynamic answer for: Tell me about faculties"
    finally:
        screen.close()


def test_default_chat_screen_uses_rag_service_without_real_external_calls(
    monkeypatch,
    tmp_path,
) -> None:
    application = _get_application()
    calls = {}
    main_thread_id = threading.get_ident()
    db_path = tmp_path / "ecu_robot.db"

    def fake_rag_response(question, received_db_path):
        calls["question"] = question
        calls["db_path"] = received_db_path
        calls["thread_id"] = threading.get_ident()
        return {
            "answer": "RAG answer",
            "had_context": True,
            "source_used": "database",
            "matched_rooms": [],
            "matched_professors": [],
            "sources": [],
            "gemini_status": "ok",
            "error": None,
            "logged": True,
        }

    monkeypatch.setattr(
        "ui.public.screens.chat_screen.get_chatbot_response",
        fake_rag_response,
    )
    screen = ChatScreen(db_path=db_path)
    try:
        assert application is not None
        screen.chat_input.setText("Tell me about engineering")
        screen.send_message()
        _process_until(lambda: screen.message_labels[-1].text() == "RAG answer")

        assert calls["question"] == "Tell me about engineering"
        assert calls["db_path"] == db_path
        assert calls["thread_id"] != main_thread_id
        assert screen.chat_status_label.text() == "Answered from ECU records"
    finally:
        screen.close()


def test_second_send_is_blocked_while_worker_is_running() -> None:
    application = _get_application()
    controller = BlockingFakeChatController()
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("professors")
        screen.send_message()
        _process_until(lambda: controller.started.is_set())

        screen.chat_input.setText("tell me about faculties")
        screen.send_message()

        assert controller.questions == ["professors"]
        assert screen.chat_status_label.text() == "Please wait for the current answer."
        assert screen.chat_send_button.isEnabled() is False

        controller.release.set()
        _process_until(lambda: screen.chat_send_button.isEnabled(), timeout_ms=3000)
        assert controller.questions == ["professors"]
        assert screen.message_labels[-1].text() == "Released answer for: professors"
    finally:
        controller.release.set()
        screen.close()


def test_worker_error_displays_friendly_message_and_reenables_send() -> None:
    application = _get_application()
    screen = ChatScreen(controller=FailingFakeChatController())
    try:
        assert application is not None
        screen.chat_input.setText("Who are the professors?")
        screen.send_message()
        assert screen.chat_send_button.isEnabled() is False
        _process_until(lambda: screen.chat_send_button.isEnabled(), timeout_ms=3000)
        assert screen.message_labels[-1].property("sender") == "bot"
        assert screen.message_labels[-1].text() == "Sorry, I could not generate a useful answer. Please try again."
        assert screen.chat_status_label.text() == "Assistant error. Please try again."
        assert screen.chat_send_button.isEnabled() is True
    finally:
        screen.close()


def test_suggestion_button_sends_question() -> None:
    application = _get_application()
    controller = FakeChatController()
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_suggestion_2.click()
        _process_until(lambda: controller.questions == ["Tell me about faculties"])
        assert controller.questions == ["Tell me about faculties"]
    finally:
        screen.close()


def test_pending_question_is_not_duplicated() -> None:
    application = _get_application()
    controller = FakeChatController()
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.handle_pending_question("Who are the professors?")
        _process_until(lambda: controller.questions == ["Who are the professors?"])
        screen.handle_pending_question("Who are the professors?")
        _process_until(lambda: len(controller.questions) == 1)
        assert controller.questions == ["Who are the professors?"]
    finally:
        screen.close()


def test_retry_button_resends_last_question() -> None:
    application = _get_application()
    controller = FakeChatController()
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        assert screen.chat_retry_button.isEnabled() is False
        screen.chat_input.setText("Tell me about faculties")
        screen.send_message()
        _process_until(lambda: screen.chat_retry_button.isEnabled())
        screen.chat_retry_button.click()
        _process_until(lambda: controller.questions == ["Tell me about faculties", "Tell me about faculties"])
        assert controller.questions == ["Tell me about faculties", "Tell me about faculties"]
    finally:
        screen.close()


def test_clear_button_clears_messages_and_memory() -> None:
    application = _get_application()
    controller = FakeChatController()
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Tell me about faculties")
        screen.send_message()
        _process_until(lambda: "Dynamic answer" in screen.message_labels[-1].text())
        screen.chat_clear_button.click()
        assert controller.memory_cleared is True
        assert len(screen.message_labels) == 1
        assert "ECU Smart Assistant" in screen.message_labels[0].text()
        assert screen.source_labels == []
        assert screen.chat_retry_button.isEnabled() is False
    finally:
        screen.close()


def test_arabic_welcome_message_appears_when_language_is_arabic() -> None:
    application = _get_application()
    screen = ChatScreen(controller=FakeChatController())
    try:
        assert application is not None
        screen.update_language({"chat": "اسأل"})
        assert "مرحب" in screen.message_labels[0].text()
        assert screen.layoutDirection() == Qt.LayoutDirection.RightToLeft
    finally:
        screen.close()
