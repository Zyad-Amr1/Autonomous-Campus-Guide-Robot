"""Headless tests for the public chat screen."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QScrollArea

from ui.public.screens.chat_screen import ChatScreen


class FakeChatController:
    def __init__(self) -> None:
        self.questions: list[str] = []

    def answer_question(self, question: str) -> dict:
        self.questions.append(question)
        return {
            "answer": f"Dynamic answer for: {question}",
            "confidence": "high",
            "sources": [{"source_type": "faq", "title": "Test", "snippet": "Context"}],
            "route": "database_context",
        }


def _get_application() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


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
        assert screen.findChild(QPushButton, "chat_suggestion_1") is not None
        assert screen.findChild(QPushButton, "chat_suggestion_2") is not None
        assert screen.findChild(QPushButton, "chat_suggestion_3") is not None
        assert screen.findChild(QPushButton, "chat_suggestion_4") is not None
        assert screen.findChild(QLabel, "chat_status_label") is not None
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
        assert controller.questions == ["Where is cafeteria?"]
        assert screen.chat_input.text() == ""
        assert len(screen.message_labels) == initial_count + 2
        assert screen.message_labels[-2].property("sender") == "user"
        assert screen.message_labels[-1].property("sender") == "bot"
        assert "Dynamic answer" in screen.message_labels[-1].text()
    finally:
        screen.close()


def test_suggestion_button_sends_question() -> None:
    application = _get_application()
    controller = FakeChatController()
    screen = ChatScreen(controller=controller)
    try:
        assert application is not None
        screen.chat_suggestion_2.click()
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
        QApplication.processEvents()
        screen.handle_pending_question("Who are the professors?")
        QApplication.processEvents()
        assert controller.questions == ["Who are the professors?"]
    finally:
        screen.close()
