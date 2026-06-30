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
from controllers.public_chat_controller import is_useless_answer
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
ARABIC_SUGGESTED_QUESTIONS = (
    "ما هي كليات الجامعة؟",
    "أين القاعات؟",
    "من هم أعضاء هيئة التدريس؟",
    "ما الفعاليات المتاحة؟",
)
WELCOME_ENGLISH = (
    "Hello! I'm ECU Smart Assistant. Ask me about university information, "
    "faculties, rooms, professors, courses, events, or services."
)
SAFE_FALLBACK_ANSWER = (
    "I could not generate a useful answer. "
    "Please try again or sync university data from the Data section."
)
WELCOME_ARABIC = (
    "مرحبًا! أنا مساعد ECU الذكي. يمكنك سؤالي عن معلومات الجامعة أو الكليات "
    "أو القاعات أو أعضاء هيئة التدريس أو الجداول أو الفعاليات."
)


class ChatAnswerWorker(QObject):
    """Run chatbot answer generation away from the GUI thread."""

    result_ready = Signal(int, dict)
    error = Signal(int, str)

    def __init__(self, controller: PublicChatController, question: str, request_id: int) -> None:
        super().__init__()
        self.controller = controller
        self.question = question
        self.request_id = request_id

    def run(self) -> None:
        try:
            self.result_ready.emit(self.request_id, self.controller.answer_question(self.question))
        except Exception as error:
            self.error.emit(self.request_id, str(error))


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
        self._message_rows: dict[QLabel, QWidget] = {}
        self._translations: dict[str, str] = {}
        self._last_user_question: str | None = None
        self._request_id = 0
        self._typing_timer: QTimer | None = None
        self._typing_label: QLabel | None = None
        self._typing_text = ""
        self._typing_index = 0
        self._pending_sources: list[dict] = []
        self._pending_route = ""
        self._thinking_bubble: QLabel | None = None
        self._is_arabic_ui = False
        self.setObjectName("chat_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._apply_styles()
        self._add_welcome_message()

    def _build_ui(self) -> None:
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(PAGE_PADDING, 22, PAGE_PADDING, PAGE_PADDING)
        page_layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        title_column = QVBoxLayout()
        title_column.setSpacing(4)
        self.chat_title = QLabel("ECU Smart Assistant")
        self.chat_title.setObjectName("chat_title")
        self.chat_subtitle = QLabel("Ask about faculties, rooms, staff, schedules, events, and services")
        self.chat_subtitle.setObjectName("chat_subtitle")
        self.chat_subtitle.setWordWrap(True)
        title_column.addWidget(self.chat_title)
        title_column.addWidget(self.chat_subtitle)
        header_row.addLayout(title_column, stretch=1)

        self.chat_retry_button = QPushButton("Retry")
        self.chat_retry_button.setObjectName("chat_retry_button")
        self.chat_retry_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chat_retry_button.setEnabled(False)
        self.chat_retry_button.clicked.connect(self.retry_last_question)
        self.chat_clear_button = QPushButton("Clear")
        self.chat_clear_button.setObjectName("chat_clear_button")
        self.chat_clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chat_clear_button.clicked.connect(self.clear_chat)
        header_row.addWidget(self.chat_retry_button)
        header_row.addWidget(self.chat_clear_button)
        page_layout.addLayout(header_row)

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
        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        status_row.addWidget(self.chat_status_label, stretch=1)

        self.chat_thinking_label = QLabel("")
        self.chat_thinking_label.setObjectName("chat_thinking_label")
        self.chat_thinking_label.setVisible(False)
        status_row.addWidget(self.chat_thinking_label)
        page_layout.addLayout(status_row)

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

    def send_message(self, *_args) -> None:
        """Add user and bot bubbles for a question without blocking on UI work."""
        question = self.chat_input.text().strip()
        self._send_question(question, add_user_bubble=True)

    def retry_last_question(self) -> None:
        """Regenerate the previous answer without duplicating the user bubble."""
        if not self._last_user_question or not self.chat_send_button.isEnabled():
            return
        self._send_question(self._last_user_question, add_user_bubble=False)

    def clear_chat(self) -> None:
        """Clear visible messages and in-memory conversation context."""
        self._request_id += 1
        self._stop_typing()
        self._clear_message_area()
        self._last_user_question = None
        self.chat_retry_button.setEnabled(False)
        clear_memory = getattr(self.controller, "clear_memory", None)
        if callable(clear_memory):
            clear_memory()
        self.chat_status_label.setText("Ready" if not self._is_arabic_ui else "جاهز")
        self.chat_thinking_label.setVisible(False)
        self.chat_thinking_label.setText("")
        self._add_welcome_message()

    def _send_question(self, question: str, add_user_bubble: bool) -> None:
        """Send a prepared question through the background worker."""
        if not question:
            self.chat_status_label.setText("Type a question first.")
            return

        self._stop_typing()
        if add_user_bubble:
            self.add_user_message(question)
        self.chat_input.clear()
        self._last_user_question = question
        self.chat_retry_button.setEnabled(False)
        thinking_text = self._thinking_text(question)
        self.chat_status_label.setText("Searching university data...")
        self.chat_thinking_label.setText(thinking_text)
        self.chat_thinking_label.setVisible(True)
        self._thinking_bubble = self.add_bot_message(thinking_text)
        self.chat_send_button.setEnabled(False)
        self._request_id += 1
        self._start_answer_worker(question, self._request_id)

    def _start_answer_worker(self, question: str, request_id: int) -> None:
        """Start a background worker for the controller call."""
        thread = QThread(self)
        worker = ChatAnswerWorker(self.controller, question, request_id)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.result_ready.connect(self._handle_answer_result)
        worker.error.connect(self._handle_answer_error)
        worker.result_ready.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.result_ready.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        worker.result_ready.connect(lambda *_args: self._active_workers.remove(worker) if worker in self._active_workers else None)
        worker.error.connect(lambda *_args: self._active_workers.remove(worker) if worker in self._active_workers else None)
        thread.finished.connect(lambda: self._active_threads.remove(thread) if thread in self._active_threads else None)
        thread.finished.connect(thread.deleteLater)
        self._active_threads.append(thread)
        self._active_workers.append(worker)
        thread.start()

    def _handle_answer_result(self, request_id: int, result: dict) -> None:
        """Render a completed bot answer."""
        if request_id != self._request_id:
            return
        self._remove_thinking_bubble()
        confidence = str(result.get("confidence", "low"))
        route = str(result.get("route", "fallback"))
        sources = list(result.get("sources") or [])
        debug = dict(result.get("debug") or {})
        self.chat_status_label.setText(self._status_text(route, confidence, sources, debug))
        self.chat_thinking_label.setVisible(False)
        self.chat_thinking_label.setText("")
        self.chat_send_button.setEnabled(True)
        self.chat_retry_button.setEnabled(bool(self._last_user_question))
        answer = str(result.get("answer") or "").strip()
        if is_useless_answer(answer):
            answer = SAFE_FALLBACK_ANSWER
        self._display_answer(answer, sources)

    def _handle_answer_error(self, request_id: int, _error: str) -> None:
        """Render a safe message when answer generation fails unexpectedly."""
        if request_id != self._request_id:
            return
        self._remove_thinking_bubble()
        self.add_bot_message("Sorry, I had a problem generating the answer. Please try again.")
        self.chat_status_label.setText("Assistant error. Please try again.")
        self.chat_thinking_label.setVisible(False)
        self.chat_thinking_label.setText("")
        self.chat_send_button.setEnabled(True)
        self.chat_retry_button.setEnabled(bool(self._last_user_question))

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

        row_widget = QWidget(self.chat_messages_container)
        row_widget.setObjectName("chat_sources_row")
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(sources_label)
        row.addStretch()

        self._insert_message_row(row_widget)
        self.source_labels.append(sources_label)
        self._message_rows[sources_label] = row_widget
        self._scroll_to_bottom()
        return sources_label

    def _add_message(self, text: str, sender: str) -> QLabel:
        bubble = QLabel(text, self.chat_messages_container)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setObjectName("chat_user_message" if sender == "user" else "chat_bot_message")
        bubble.setProperty("sender", sender)
        bubble.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        bubble.setMaximumWidth(640)

        row_widget = QWidget(self.chat_messages_container)
        row_widget.setObjectName("chat_user_row" if sender == "user" else "chat_bot_row")
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 0, 0, 0)
        if sender == "user":
            row.addStretch()
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch()

        self._insert_message_row(row_widget)
        self.message_labels.append(bubble)
        self._message_rows[bubble] = row_widget
        self._scroll_to_bottom()
        return bubble

    def _insert_message_row(self, row_widget: QWidget) -> None:
        """Insert a message row widget inside the scroll area's message layout."""
        last_index = self.chat_messages_layout.count() - 1
        if last_index >= 0:
            last_item = self.chat_messages_layout.itemAt(last_index)
            if last_item is not None and last_item.spacerItem() is not None:
                self.chat_messages_layout.takeAt(last_index)
        self.chat_messages_layout.addWidget(row_widget)
        self.chat_messages_layout.addStretch()

    def _scroll_to_bottom(self) -> None:
        QTimer.singleShot(0, lambda: self.chat_messages_area.verticalScrollBar().setValue(
            self.chat_messages_area.verticalScrollBar().maximum()
        ))

    def _format_sources(self, sources: list[dict]) -> str:
        """Format public source metadata without exposing noisy internals."""
        lines = ["Sources:"]
        for source in sources[:5]:
            source_name = str(source.get("source", "")).strip().lower()
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

    def _format_source_score(self, score) -> str:
        try:
            numeric_score = float(score)
        except (TypeError, ValueError):
            return ""
        if numeric_score <= 0:
            return ""
        return f"score {numeric_score:.0f}"

    def _status_text(
        self,
        route: str,
        confidence: str,
        sources: list[dict],
        debug: dict,
    ) -> str:
        """Build a compact visitor-safe generation status line."""
        if debug.get("auto_synced_database"):
            return f"Knowledge synced automatically | {int(debug.get('chunk_count_after') or 0)} chunks"
        if route == "no_context":
            return f"No context found | {int(debug.get('chunk_count_after') or 0)} chunks"
        return f"Answered from {route} | {len(sources)} sources | {confidence} confidence"

    def _thinking_text(self, question: str) -> str:
        """Return a brief loading state in the user's apparent language."""
        if any("\u0600" <= character <= "\u06ff" for character in question):
            return "\u062c\u0627\u0631\u064a \u0627\u0644\u062a\u0641\u0643\u064a\u0631..."
        return "Thinking..."

    def _add_welcome_message(self) -> None:
        """Add the localized welcome assistant message."""
        self.add_bot_message(WELCOME_ARABIC if self._is_arabic_ui else WELCOME_ENGLISH)

    def _display_answer(self, text: str, sources: list[dict]) -> None:
        """Display the completed assistant answer immediately and reliably."""
        self._stop_typing()
        self.add_bot_message(text)
        if sources:
            self.add_sources_message(sources)

    def _start_typing_answer(self, text: str, sources: list[dict], route: str) -> None:
        """Reveal assistant answer with a lightweight QTimer typing effect."""
        self._pending_sources = sources
        self._pending_route = route
        self._typing_text = text
        self._typing_index = 0
        self._typing_label = self.add_bot_message("")
        if not self.isVisible():
            self._typing_label.setText(self._typing_text)
            if self._pending_sources and self._pending_route != "no_context":
                self.add_sources_message(self._pending_sources)
            self._pending_sources = []
            self._pending_route = ""
            self._typing_label = None
            self._typing_text = ""
            return
        self._typing_timer = QTimer(self)
        self._typing_timer.setInterval(12)
        self._typing_timer.timeout.connect(self._typing_tick)
        self._typing_timer.start()

    def _typing_tick(self) -> None:
        if self._typing_label is None:
            self._stop_typing()
            return
        chunk_size = 4 if any("\u0600" <= char <= "\u06ff" for char in self._typing_text) else 6
        self._typing_index = min(len(self._typing_text), self._typing_index + chunk_size)
        self._typing_label.setText(self._typing_text[: self._typing_index])
        self._scroll_to_bottom()
        if self._typing_index >= len(self._typing_text):
            self._stop_typing()
            if self._pending_sources and self._pending_route != "no_context":
                self.add_sources_message(self._pending_sources)
            self._pending_sources = []
            self._pending_route = ""

    def _stop_typing(self) -> None:
        if self._typing_timer is not None:
            self._typing_timer.stop()
            self._typing_timer.deleteLater()
        self._typing_timer = None
        self._typing_label = None
        self._typing_text = ""
        self._typing_index = 0

    def _remove_thinking_bubble(self) -> None:
        if self._thinking_bubble is not None:
            self._remove_label(self._thinking_bubble)
            self._thinking_bubble = None

    def _remove_label(self, label: QLabel) -> None:
        row_widget = self._message_rows.pop(label, None)
        if row_widget is None:
            return
        for index in range(self.chat_messages_layout.count()):
            item = self.chat_messages_layout.itemAt(index)
            if item is not None and item.widget() is row_widget:
                self.chat_messages_layout.takeAt(index)
                break
        row_widget.deleteLater()
        if label in self.message_labels:
            self.message_labels.remove(label)
        if label in self.source_labels:
            self.source_labels.remove(label)

    def _clear_message_area(self) -> None:
        while self.chat_messages_layout.count():
            item = self.chat_messages_layout.takeAt(0)
            self._delete_layout_item(item)
        self.message_labels.clear()
        self.source_labels.clear()
        self._message_rows.clear()
        self._thinking_bubble = None
        self.chat_messages_layout.addStretch()

    def _delete_layout(self, layout: QHBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            self._delete_layout_item(item)
        layout.deleteLater()

    def _delete_layout_item(self, item) -> None:
        widget = item.widget()
        child_layout = item.layout()
        if widget is not None:
            widget.deleteLater()
        elif child_layout is not None:
            self._delete_layout(child_layout)

    def update_language(self, translations: dict[str, str]) -> None:
        """Keep chat labels compatible with public language switching."""
        self._translations = translations
        is_arabic = translations.get("chat", "") == "اسأل"
        self._is_arabic_ui = is_arabic
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft if is_arabic else Qt.LayoutDirection.LeftToRight)
        self.chat_title.setText("مساعد ECU الذكي" if is_arabic else "ECU Smart Assistant")
        self.chat_subtitle.setText(
            "اسأل عن الكليات والقاعات وأعضاء هيئة التدريس والجداول والفعاليات والخدمات."
            if is_arabic
            else "Ask about faculties, rooms, staff, schedules, events, and services"
        )
        self.chat_input.setPlaceholderText("اسأل عن ECU..." if is_arabic else "Ask about ECU...")
        self.chat_send_button.setText("إرسال" if is_arabic else "Send")
        self.chat_retry_button.setText("إعادة" if is_arabic else "Retry")
        self.chat_clear_button.setText("مسح" if is_arabic else "Clear")
        self.chat_status_label.setText("جاهز" if is_arabic else "Ready")
        suggestions = ARABIC_SUGGESTED_QUESTIONS if is_arabic else SUGGESTED_QUESTIONS
        for button, question in zip(self.suggestion_buttons, suggestions, strict=False):
            button.setText(question)
        if len(self.message_labels) == 1 and self.message_labels[0].property("sender") == "bot":
            self.message_labels[0].setText(WELCOME_ARABIC if is_arabic else WELCOME_ENGLISH)
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

            QPushButton#chat_retry_button,
            QPushButton#chat_clear_button {{
                background-color: {WHITE};
                color: {CHARCOAL};
                border: 1px solid {BORDER};
                border-radius: {px(10)};
                min-width: {px(86)};
                min-height: {px(40)};
                padding: 0 {px(14)};
                {font(13, 800)}
            }}

            QPushButton#chat_retry_button:hover,
            QPushButton#chat_clear_button:hover {{
                background-color: {GOLD_LIGHT};
                border-color: {ECU_RED};
            }}

            QPushButton#chat_retry_button:disabled {{
                background-color: {LIGHT_GRAY};
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
