"""Public database-backed chatbot screen."""

from __future__ import annotations

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from controllers.public_chat_controller import PublicChatController
from ui.public.theme import (
    BORDER,
    CHARCOAL,
    ECU_RED,
    ECU_RED_DARK,
    GOLD_LIGHT,
    LIGHT_GRAY,
    OFF_WHITE,
    PAGE_PADDING,
    TEXT_DARK,
    TEXT_MUTED,
    WHITE,
    font,
    px,
)


SUGGESTED_QUESTIONS = (
    "Where is the cafeteria?",
    "Tell me about faculties",
    "Who are the professors?",
    "What events are available?",
)


class ChatAnswerWorker(QObject):
    """Run chatbot answer generation away from the GUI thread."""

    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, controller: PublicChatController, question: str) -> None:
        super().__init__()
        self.controller = controller
        self.question = question

    def run(self) -> None:
        try:
            self.finished.emit(self.controller.answer_question(self.question))
        except Exception as error:
            self.failed.emit(str(error))


class ChatScreen(QWidget):
    """Modern public chat interface backed by university database context."""

    def __init__(
        self,
        controller: PublicChatController | None = None,
        parent_window=None,
    ) -> None:
        super().__init__()
        self.controller = controller or PublicChatController()
        self.parent_window = parent_window
        self._last_pending_question: str | None = None
        self._active_threads: list[QThread] = []
        self._active_workers: list[ChatAnswerWorker] = []
        self.message_labels: list[QLabel] = []
        self.source_labels: list[QLabel] = []
        self._translations: dict[str, str] = {}
        self.setObjectName("chat_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._apply_styles()
        self.add_bot_message("Hi, I am ECU Smart Assistant. Ask me about faculties, rooms, professors, courses, events, or FAQs.")

    def _build_ui(self) -> None:
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(PAGE_PADDING, 22, PAGE_PADDING, PAGE_PADDING)
        page_layout.setSpacing(14)

        self.chat_title = QLabel("Ask ECU Smart Assistant")
        self.chat_title.setObjectName("chat_title")
        self.chat_subtitle = QLabel("Answers are generated from the university database context.")
        self.chat_subtitle.setObjectName("chat_subtitle")
        self.chat_subtitle.setWordWrap(True)
        page_layout.addWidget(self.chat_title)
        page_layout.addWidget(self.chat_subtitle)

        suggestions_layout = QHBoxLayout()
        suggestions_layout.setSpacing(10)
        self.suggestion_buttons: list[QPushButton] = []
        for index, question in enumerate(SUGGESTED_QUESTIONS, start=1):
            button = QPushButton(question)
            button.setObjectName(f"chat_suggestion_{index}")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, text=question: self.ask_suggested_question(text))
            self.suggestion_buttons.append(button)
            setattr(self, f"chat_suggestion_{index}", button)
            suggestions_layout.addWidget(button)
        page_layout.addLayout(suggestions_layout)

        self.chat_messages_area = QScrollArea()
        self.chat_messages_area.setObjectName("chat_messages_area")
        self.chat_messages_area.setWidgetResizable(True)
        self.chat_messages_area.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_messages_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_messages_container = QWidget()
        self.chat_messages_container.setObjectName("chat_messages_container")
        self.chat_messages_layout = QVBoxLayout(self.chat_messages_container)
        self.chat_messages_layout.setContentsMargins(18, 18, 18, 18)
        self.chat_messages_layout.setSpacing(12)
        self.chat_messages_layout.addStretch()
        self.chat_messages_area.setWidget(self.chat_messages_container)
        page_layout.addWidget(self.chat_messages_area, stretch=1)

        self.chat_status_label = QLabel("Ready")
        self.chat_status_label.setObjectName("chat_status_label")
        page_layout.addWidget(self.chat_status_label)

        self.chat_thinking_label = QLabel("")
        self.chat_thinking_label.setObjectName("chat_thinking_label")
        self.chat_thinking_label.setVisible(False)
        page_layout.addWidget(self.chat_thinking_label)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("chat_input")
        self.chat_input.setPlaceholderText("Ask about ECU...")
        self.chat_input.returnPressed.connect(self.send_message)
        self.chat_send_button = QPushButton("Send")
        self.chat_send_button.setObjectName("chat_send_button")
        self.chat_send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chat_send_button.clicked.connect(self.send_message)
        input_row.addWidget(self.chat_input, stretch=1)
        input_row.addWidget(self.chat_send_button)
        page_layout.addLayout(input_row)

    def ask_suggested_question(self, question: str) -> None:
        """Send one of the visible suggested questions."""
        self.chat_input.setText(question)
        self.send_message()

    def handle_pending_question(self, question: str | None) -> None:
        """Consume a quick-ask question from the public shell once."""
        cleaned_question = (question or "").strip()
        if not cleaned_question or cleaned_question == self._last_pending_question:
            return
        self._last_pending_question = cleaned_question
        self.chat_input.setText(cleaned_question)
        QTimer.singleShot(0, self.send_message)

    def send_message(self) -> None:
        """Add user and bot bubbles for a question without blocking on UI work."""
        question = self.chat_input.text().strip()
        if not question:
            self.chat_status_label.setText("Type a question first.")
            return

        self.add_user_message(question)
        self.chat_input.clear()
        thinking_text = self._thinking_text(question)
        self.chat_status_label.setText("Searching university data...")
        self.chat_thinking_label.setText(thinking_text)
        self.chat_thinking_label.setVisible(True)
        self.chat_send_button.setEnabled(False)
        self._start_answer_worker(question)

    def _start_answer_worker(self, question: str) -> None:
        """Start a background worker for the controller call."""
        thread = QThread(self)
        worker = ChatAnswerWorker(self.controller, question)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._handle_answer_result)
        worker.failed.connect(self._handle_answer_error)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        worker.finished.connect(lambda: self._active_workers.remove(worker) if worker in self._active_workers else None)
        worker.failed.connect(lambda: self._active_workers.remove(worker) if worker in self._active_workers else None)
        thread.finished.connect(lambda: self._active_threads.remove(thread) if thread in self._active_threads else None)
        thread.finished.connect(thread.deleteLater)
        self._active_threads.append(thread)
        self._active_workers.append(worker)
        thread.start()

    def _handle_answer_result(self, result: dict) -> None:
        """Render a completed bot answer."""
        self.add_bot_message(str(result["answer"]))
        sources = result.get("sources") or []
        if sources:
            self.add_sources_message(sources)
        confidence = str(result.get("confidence", "low"))
        route = str(result.get("route", "fallback"))
        self.chat_status_label.setText(f"Answered from {route} ({confidence} confidence).")
        self.chat_thinking_label.setVisible(False)
        self.chat_thinking_label.setText("")
        self.chat_send_button.setEnabled(True)

    def _handle_answer_error(self, _error: str) -> None:
        """Render a safe message when answer generation fails unexpectedly."""
        self.add_bot_message("I could not answer safely right now. Please try another question.")
        self.chat_status_label.setText("Assistant error handled safely.")
        self.chat_thinking_label.setVisible(False)
        self.chat_thinking_label.setText("")
        self.chat_send_button.setEnabled(True)

    def closeEvent(self, event) -> None:  # noqa: N802
        """Stop active answer workers when the chat widget closes."""
        for thread in list(self._active_threads):
            thread.quit()
            thread.wait(1000)
        super().closeEvent(event)

    def add_user_message(self, text: str) -> QLabel:
        """Append a right-aligned user bubble."""
        return self._add_message(text, sender="user")

    def add_bot_message(self, text: str) -> QLabel:
        """Append a left-aligned bot bubble."""
        return self._add_message(text, sender="bot")

    def add_sources_message(self, sources: list[dict]) -> QLabel:
        """Append a compact source list under the latest bot answer."""
        source_text = self._format_sources(sources)
        sources_label = QLabel(source_text)
        sources_label.setWordWrap(True)
        sources_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        sources_label.setObjectName("chat_sources_area")
        sources_label.setProperty("sender", "sources")
        sources_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sources_label.setMaximumWidth(640)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(sources_label)
        row.addStretch()

        insert_index = max(0, self.chat_messages_layout.count() - 1)
        self.chat_messages_layout.insertLayout(insert_index, row)
        self.source_labels.append(sources_label)
        self._scroll_to_bottom()
        return sources_label

    def _add_message(self, text: str, sender: str) -> QLabel:
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setObjectName("chat_user_message" if sender == "user" else "chat_bot_message")
        bubble.setProperty("sender", sender)
        bubble.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        bubble.setMaximumWidth(640)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if sender == "user":
            row.addStretch()
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch()

        insert_index = max(0, self.chat_messages_layout.count() - 1)
        self.chat_messages_layout.insertLayout(insert_index, row)
        self.message_labels.append(bubble)
        self._scroll_to_bottom()
        return bubble

    def _scroll_to_bottom(self) -> None:
        QTimer.singleShot(0, lambda: self.chat_messages_area.verticalScrollBar().setValue(
            self.chat_messages_area.verticalScrollBar().maximum()
        ))

    def _format_sources(self, sources: list[dict]) -> str:
        """Format public source metadata without exposing noisy internals."""
        lines = ["Sources:"]
        for source in sources[:5]:
            source_name = self._source_display_name(str(source.get("source", "")))
            title = str(source.get("title", "")).strip()
            if source_name and title:
                lines.append(f"- {source_name}: {title}")
            elif title:
                lines.append(f"- {title}")
            elif source_name:
                lines.append(f"- {source_name}")
        return "\n".join(lines)

    def _source_display_name(self, source: str) -> str:
        """Convert source keys into clean visitor-facing labels."""
        labels = {
            "faq": "FAQ",
            "faculties": "Faculties",
            "professors": "Professors",
            "rooms": "Rooms",
            "courses": "Courses",
            "events": "Events",
            "website": "Website",
            "document": "Document",
        }
        return labels.get(source.strip().lower(), source.strip().title())

    def _thinking_text(self, question: str) -> str:
        """Return a brief loading state in the user's apparent language."""
        if any("\u0600" <= character <= "\u06ff" for character in question):
            return "\u062c\u0627\u0631\u064a \u0627\u0644\u062a\u0641\u0643\u064a\u0631..."
        return "Thinking..."

    def update_language(self, translations: dict[str, str]) -> None:
        """Keep chat labels compatible with public language switching."""
        self._translations = translations
        is_arabic = translations.get("chat", "") == "اسأل"
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft if is_arabic else Qt.LayoutDirection.LeftToRight)
        self.chat_title.setText("اسأل مساعد ECU الذكي" if is_arabic else "Ask ECU Smart Assistant")
        self.chat_subtitle.setText(
            "تأتي الإجابات من بيانات الجامعة المتاحة."
            if is_arabic
            else "Answers are generated from the university database context."
        )
        self.chat_input.setPlaceholderText("اسأل عن ECU..." if is_arabic else "Ask about ECU...")
        self.chat_send_button.setText("إرسال" if is_arabic else "Send")
        self.chat_status_label.setText("جاهز" if is_arabic else "Ready")
        for button, question in zip(self.suggestion_buttons, SUGGESTED_QUESTIONS, strict=False):
            button.setText(question)
        self._apply_styles()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#chat_screen {{
                background-color: {OFF_WHITE};
                color: {TEXT_DARK};
                {font(15)}
            }}

            QLabel#chat_title {{
                color: {CHARCOAL};
                {font(30, 850)}
            }}

            QLabel#chat_subtitle,
            QLabel#chat_status_label,
            QLabel#chat_thinking_label {{
                color: {TEXT_MUTED};
                {font(14, 650)}
            }}

            QScrollArea#chat_messages_area {{
                background-color: {WHITE};
                border: 1px solid {BORDER};
                border-radius: {px(10)};
            }}

            QWidget#chat_messages_container {{
                background-color: {WHITE};
            }}

            QLabel#chat_bot_message {{
                background-color: {LIGHT_GRAY};
                color: {TEXT_DARK};
                border: 1px solid {BORDER};
                border-radius: {px(10)};
                padding: {px(12)} {px(14)};
                {font(14, 650)}
            }}

            QLabel#chat_user_message {{
                background-color: {ECU_RED};
                color: {WHITE};
                border: none;
                border-radius: {px(10)};
                padding: {px(12)} {px(14)};
                {font(14, 700)}
            }}

            QLabel#chat_sources_area {{
                background-color: {WHITE};
                color: {TEXT_MUTED};
                border: 1px solid {BORDER};
                border-radius: {px(8)};
                padding: {px(10)} {px(12)};
                {font(12, 650)}
            }}

            QLineEdit#chat_input {{
                background-color: {WHITE};
                color: {TEXT_DARK};
                border: 1px solid {BORDER};
                border-radius: {px(10)};
                padding: 0 {px(16)};
                min-height: {px(46)};
                {font(15, 700)}
            }}

            QLineEdit#chat_input:focus {{
                border: 2px solid {ECU_RED};
            }}

            QPushButton#chat_send_button {{
                background-color: {ECU_RED};
                color: {WHITE};
                border: none;
                border-radius: {px(10)};
                min-width: {px(112)};
                min-height: {px(46)};
                padding: 0 {px(18)};
                {font(15, 850)}
            }}

            QPushButton#chat_send_button:hover {{
                background-color: {ECU_RED_DARK};
            }}

            QPushButton#chat_send_button:disabled {{
                background-color: {BORDER};
                color: {TEXT_MUTED};
            }}

            QPushButton#chat_suggestion_1,
            QPushButton#chat_suggestion_2,
            QPushButton#chat_suggestion_3,
            QPushButton#chat_suggestion_4 {{
                background-color: {WHITE};
                color: {CHARCOAL};
                border: 1px solid {BORDER};
                border-radius: {px(10)};
                min-height: {px(44)};
                padding: 0 {px(14)};
                {font(13, 750)}
            }}

            QPushButton#chat_suggestion_1:hover,
            QPushButton#chat_suggestion_2:hover,
            QPushButton#chat_suggestion_3:hover,
            QPushButton#chat_suggestion_4:hover {{
                background-color: {GOLD_LIGHT};
                border-color: {ECU_RED};
            }}
            """
        )
