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
            "confidence": "medium",
            "sources": self.sources,
            "route": "rag_fallback",
            "debug": {"chunk_count_after": 4, "auto_synced_database": False},
        }


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


def test_sources_are_displayed_when_returned() -> None:
    application = _get_application()
    controller = FakeChatController()
    controller.route = "rag_fallback"
    controller.sources = [
        {"source": "faq", "title": "How can I find a professor office?", "score": 72, "id": "faq:1"},
        {"source": "professors", "title": "Ass. Prof. Dr. Marwa Taher", "score": 31, "id": "professors:1"},
        {"source": "professors", "title": "Ass. Prof. Marian Mamdouh", "score": 31, "id": "professors:2"},
    ]
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Where is cafeteria?")
        screen.send_message()
        _process_until(lambda: len(screen.source_labels) == 1)
        assert screen.source_labels
        sources_area = screen.source_labels[-1]
        assert sources_area.objectName() == "chat_sources_area"
        assert "Sources:" in sources_area.text()
        assert "- faq: How can I find a professor office?" in sources_area.text()
        assert "- professors: Ass. Prof. Dr. Marwa Taher" in sources_area.text()
        assert "- professors: Ass. Prof. Marian Mamdouh" in sources_area.text()
        assert "score" not in sources_area.text()
        assert "faq:1" not in sources_area.text()
        assert _is_left_aligned(screen, sources_area)
        _assert_message_is_not_top_level(screen, sources_area)
    finally:
        screen.close()


def test_no_sources_are_displayed_for_no_context() -> None:
    application = _get_application()
    controller = FakeChatController()
    controller.route = "no_context"
    controller.sources = []
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
        _process_until(lambda: "I could not generate a useful answer" in screen.message_labels[-1].text())
        assert screen.message_labels[-1].text() != "?"
        assert screen.message_labels[-1].text() == (
            "I could not generate a useful answer. "
            "Please try again or sync university data from the Data section."
        )
    finally:
        screen.close()


def test_status_label_shows_route_and_source_count() -> None:
    application = _get_application()
    controller = FakeChatController()
    controller.route = "rag_fallback"
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_input.setText("Where is cafeteria?")
        screen.send_message()
        _process_until(lambda: "Answered from rag_fallback" in screen.chat_status_label.text())
        assert screen.chat_status_label.text() == "Answered from rag_fallback | 1 sources | high confidence"
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
        assert screen.chat_status_label.text() == "Answered from rag_fallback | 1 sources | medium confidence"
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
        assert screen.message_labels[-1].text() == "Sorry, I had a problem generating the answer. Please try again."
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
