"""Headless tests for the public chat screen."""

import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QScrollArea

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
            "confidence": "high",
            "sources": self.sources,
            "route": self.route,
            "debug": {
                "chunk_count_after": 4,
                "auto_synced_database": False,
                "source_counts": {"faq": 1},
            },
        }

    def clear_memory(self) -> None:
        self.memory_cleared = True


class SlowFakeChatController(FakeChatController):
    def answer_question(self, question: str) -> dict:
        time.sleep(0.1)
        return super().answer_question(question)


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
    finally:
        screen.close()


def test_sources_are_displayed_when_returned() -> None:
    application = _get_application()
    screen = ChatScreen(controller=FakeChatController())
    try:
        assert application is not None
        screen.chat_input.setText("Where is cafeteria?")
        screen.send_message()
        _process_until(lambda: len(screen.source_labels) == 1)
        assert screen.source_labels
        sources_area = screen.source_labels[-1]
        assert sources_area.objectName() == "chat_sources_area"
        assert "Sources:" in sources_area.text()
        assert "FAQ: Test" in sources_area.text()
        assert "score 72" in sources_area.text()
    finally:
        screen.close()


def test_no_sources_are_displayed_for_no_context() -> None:
    application = _get_application()
    controller = FakeChatController()
    controller.route = "no_context"
    controller.sources = [{"source": "faq", "title": "Hidden", "score": 9}]
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Unknown topic")
        screen.send_message()
        _process_until(lambda: "Dynamic answer" in screen.message_labels[-1].text())
        assert screen.source_labels == []
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
            "confidence": "low",
            "sources": [],
            "route": "no_context",
            "debug": {"chunk_count_after": 0, "auto_synced_database": False},
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
        assert screen.source_labels == []
        assert screen.chat_status_label.text() == "No context found | 0 chunks"
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
            "confidence": "low",
            "sources": [],
            "route": "no_context",
            "language": "en",
            "debug": {"chunk_count_after": 0, "auto_synced_database": False},
        }

    controller.answer_question = useless_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Unknown topic")
        screen.send_message()
        _process_until(lambda: "I do not have enough information" in screen.message_labels[-1].text())
        assert screen.message_labels[-1].text() != "?"
    finally:
        screen.close()


def test_status_label_shows_route_and_source_count() -> None:
    application = _get_application()
    screen = ChatScreen(controller=FakeChatController())
    try:
        assert application is not None
        screen.chat_input.setText("Where is cafeteria?")
        screen.send_message()
        _process_until(lambda: "Answered from database_context" in screen.chat_status_label.text())
        assert screen.chat_status_label.text() == "Answered from database_context | 1 sources | high confidence"
    finally:
        screen.close()


def test_status_label_shows_auto_sync_chunk_count() -> None:
    application = _get_application()
    controller = FakeChatController()

    def auto_sync_answer(question: str) -> dict:
        controller.questions.append(question)
        return {
            "answer": "Synced answer",
            "confidence": "medium",
            "sources": [{"source": "faq", "title": "One", "score": 44}],
            "route": "rag_fallback",
            "debug": {"chunk_count_after": 25, "auto_synced_database": True},
        }

    controller.answer_question = auto_sync_answer
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Tell me about faculties")
        screen.send_message()
        _process_until(lambda: screen.chat_status_label.text().startswith("Knowledge synced automatically"))
        assert screen.chat_status_label.text() == "Knowledge synced automatically | 25 chunks"
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
