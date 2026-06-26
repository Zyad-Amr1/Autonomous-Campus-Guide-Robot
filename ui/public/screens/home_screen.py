"""Touch-first public home screen for the ECU kiosk."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.public.theme import (
    BORDER,
    CARD_RADIUS,
    CHARCOAL,
    ECU_RED,
    GOLD_LIGHT,
    OFF_WHITE,
    PAGE_PADDING,
    TEXT_DARK,
    TEXT_MUTED,
    WHITE,
    font,
    px,
)


class HomeScreen(QWidget):
    """Show three clear choices for public visitors after language selection."""

    def __init__(self, parent_window=None) -> None:
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("public_home_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(
            PAGE_PADDING + 24,
            PAGE_PADDING + 18,
            PAGE_PADDING + 24,
            PAGE_PADDING + 18,
        )
        page_layout.setSpacing(24)

        title_group = QVBoxLayout()
        title_group.setSpacing(8)
        self.home_title = QLabel("How can I help you today?")
        self.home_title.setObjectName("home_title")
        self.home_title.setWordWrap(True)
        self.home_subtitle = QLabel("Choose one service to begin.")
        self.home_subtitle.setObjectName("home_subtitle")
        self.home_subtitle.setWordWrap(True)
        title_group.addWidget(self.home_title)
        title_group.addWidget(self.home_subtitle)
        page_layout.addLayout(title_group)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        self.home_info_card = self._create_card(
            "University Information",
            "Explore faculties, staff, schedules, events, and services.",
            "home_info_card",
            "about",
        )
        self.home_chatbot_card = self._create_card(
            "Ask Chatbot",
            "Ask questions about ECU and get instant guidance.",
            "home_chatbot_card",
            "chat",
        )
        self.home_map_card = self._create_card(
            "Campus Map",
            "Find buildings, rooms, and walking routes.",
            "home_map_card",
            "map",
        )
        cards_layout.addWidget(self.home_info_card)
        cards_layout.addWidget(self.home_chatbot_card)
        cards_layout.addWidget(self.home_map_card)
        page_layout.addLayout(cards_layout, stretch=1)
        page_layout.addStretch()

    def _create_card(
        self,
        title: str,
        description: str,
        object_name: str,
        navigation_key: str,
    ) -> QPushButton:
        button = QPushButton(f"{title}\n{description}")
        button.setObjectName(object_name)
        button.setProperty("homeCard", True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumSize(260, 260)
        button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        callback = getattr(self.parent_window, f"show_{navigation_key}", None)
        if callback is not None:
            button.clicked.connect(callback)
        return button

    def _apply_styles(self) -> None:
        text_alignment = (
            "right"
            if self.layoutDirection() == Qt.LayoutDirection.RightToLeft
            else "left"
        )
        self.setStyleSheet(
            f"""
            QWidget#public_home_screen {{
                background-color: {OFF_WHITE};
                color: {TEXT_DARK};
            }}

            QLabel#home_title {{
                color: {CHARCOAL};
                {font(38, 900)}
            }}

            QLabel#home_subtitle {{
                color: {TEXT_MUTED};
                {font(20, 650)}
            }}

            QPushButton[homeCard="true"] {{
                background-color: {WHITE};
                color: {TEXT_DARK};
                border: 1px solid {BORDER};
                border-radius: {px(CARD_RADIUS + 8)};
                padding: {px(30)};
                text-align: {text_alignment};
                {font(22, 850)}
            }}

            QPushButton[homeCard="true"]:hover {{
                background-color: #FFF9F9;
                border: 2px solid {ECU_RED};
            }}

            QPushButton[homeCard="true"]:pressed {{
                background-color: {GOLD_LIGHT};
            }}

            QPushButton#home_info_card {{
                border-top: 8px solid {ECU_RED};
            }}

            QPushButton#home_chatbot_card,
            QPushButton#home_map_card {{
                border-top: 8px solid {CHARCOAL};
            }}
            """
        )

    def update_language(self, translations: dict[str, str]) -> None:
        """Refresh all visible home copy for the selected language."""
        self.home_title.setText(translations["home_title"])
        self.home_subtitle.setText(translations["home_subtitle"])
        self.home_info_card.setText(
            f"{translations['home_info_title']}\n{translations['home_info_subtitle']}"
        )
        self.home_chatbot_card.setText(
            f"{translations['home_chatbot_title']}\n{translations['home_chatbot_subtitle']}"
        )
        self.home_map_card.setText(
            f"{translations['home_map_title']}\n{translations['home_map_subtitle']}"
        )
        self._apply_styles()
