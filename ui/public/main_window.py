"""Stable fullscreen shell for the ECU Smart Assistant public dashboard."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.public.theme import (
    APP_BACKGROUND_STYLE,
    CARD_PADDING,
    GLASS_CARD_STYLE,
    GOLD,
    HEADER_STYLE,
    NAVY,
    NAVY_DARK,
    OFF_WHITE,
    SIDEBAR_BUTTON_STYLE,
    SIDEBAR_WIDTH,
    SUBTITLE_STYLE,
    TOUCH_BUTTON_HEIGHT,
    WHITE,
)


class PublicMainWindow(QMainWindow):
    """Display the fast, touch-friendly public dashboard shell."""

    _SIDEBAR_ITEMS = (
        ("⌂  Home", "sidebar_home_button"),
        ("◇  Map", "sidebar_map_button"),
        ("♟  Staff", "sidebar_staff_button"),
        ("▤  Schedule", "sidebar_schedule_button"),
        ("◆  News", "sidebar_news_button"),
        ("ⓘ  About", "sidebar_about_button"),
        ("◉  Chat", "sidebar_chat_button"),
    )

    def __init__(self) -> None:
        """Create one sidebar and one static content card without navigation."""
        super().__init__()
        self.setWindowTitle("ECU Smart Assistant")
        self.setObjectName("public_main_window")
        self.setMinimumSize(1280, 800)
        self.sidebar_buttons: dict[str, QPushButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the two-column public shell using lightweight Qt widgets."""
        central_widget = QWidget()
        central_widget.setObjectName("public_shell_central_widget")
        central_widget.setStyleSheet(
            APP_BACKGROUND_STYLE.replace(
                "QWidget {",
                "QWidget#public_shell_central_widget {",
                1,
            )
        )
        self.setCentralWidget(central_widget)

        shell_layout = QHBoxLayout(central_widget)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        sidebar = self._create_sidebar()
        content = self._create_content()
        shell_layout.addWidget(sidebar)
        shell_layout.addWidget(content, stretch=1)

    def _create_sidebar(self) -> QFrame:
        """Create the visual-only navigation rail for future public pages."""
        sidebar = QFrame()
        sidebar.setObjectName("public_shell_sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setStyleSheet(
            f"""
            QFrame#public_shell_sidebar {{
                background-color: {NAVY};
                border: none;
            }}
            """
        )

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(22, 34, 22, 28)
        sidebar_layout.setSpacing(12)

        app_title = QLabel("ECU Smart\nAssistant")
        app_title.setObjectName("public_sidebar_title")
        app_title.setStyleSheet(
            f"color: {GOLD}; font-size: 25px; font-weight: 800;"
        )
        app_subtitle = QLabel("Public Robot Guide")
        app_subtitle.setObjectName("public_sidebar_subtitle")
        app_subtitle.setStyleSheet(
            f"color: {OFF_WHITE}; font-size: 13px; font-weight: 600;"
        )
        sidebar_layout.addWidget(app_title)
        sidebar_layout.addWidget(app_subtitle)
        sidebar_layout.addSpacing(24)

        for label, object_name in self._SIDEBAR_ITEMS:
            button = QPushButton(label)
            button.setObjectName(object_name)
            button.setMinimumHeight(TOUCH_BUTTON_HEIGHT)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet(SIDEBAR_BUTTON_STYLE)
            self.sidebar_buttons[object_name] = button
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()
        footer = QLabel("Egyptian Chinese University")
        footer.setObjectName("public_sidebar_footer")
        footer.setWordWrap(True)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color: {OFF_WHITE}; font-size: 11px;")
        sidebar_layout.addWidget(footer)
        return sidebar

    def _create_content(self) -> QFrame:
        """Create the static welcome card for this shell-only sub-step."""
        content = QFrame()
        content.setObjectName("public_shell_content")
        content.setStyleSheet(
            f"""
            QFrame#public_shell_content {{
                background-color: {NAVY_DARK};
                border: none;
            }}
            """
        )

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(64, 64, 64, 64)
        content_layout.addStretch()

        welcome_card = QFrame()
        welcome_card.setObjectName("public_shell_welcome_card")
        welcome_card.setMinimumHeight(420)
        welcome_card.setStyleSheet(
            GLASS_CARD_STYLE.replace(
                "QFrame {",
                "QFrame#public_shell_welcome_card {",
                1,
            )
        )
        card_layout = QVBoxLayout(welcome_card)
        card_layout.setContentsMargins(
            CARD_PADDING * 2,
            CARD_PADDING * 2,
            CARD_PADDING * 2,
            CARD_PADDING * 2,
        )
        card_layout.setSpacing(20)

        eyebrow = QLabel("PUBLIC ROBOT DASHBOARD")
        eyebrow.setObjectName("public_shell_eyebrow")
        eyebrow.setStyleSheet(
            f"color: {GOLD}; font-size: 14px; font-weight: 800;"
        )
        self.public_shell_title = QLabel("Welcome to ECU Smart Assistant")
        self.public_shell_title.setObjectName("public_shell_title")
        self.public_shell_title.setStyleSheet(HEADER_STYLE)
        self.public_shell_subtitle = QLabel(
            "Public dashboard shell is ready. Navigation will be connected "
            "in the next step."
        )
        self.public_shell_subtitle.setObjectName("public_shell_subtitle")
        self.public_shell_subtitle.setWordWrap(True)
        self.public_shell_subtitle.setStyleSheet(SUBTITLE_STYLE)
        future_features = QLabel(
            "Campus Map   •   Chatbot   •   University Information"
        )
        future_features.setObjectName("public_shell_future_features")
        future_features.setWordWrap(True)
        future_features.setStyleSheet(
            f"""
            color: {WHITE};
            background-color: rgba(255, 255, 255, 20);
            border: 1px solid rgba(255, 255, 255, 45);
            border-radius: 16px;
            padding: 18px 22px;
            font-size: 18px;
            font-weight: 600;
            """
        )

        card_layout.addWidget(eyebrow)
        card_layout.addWidget(self.public_shell_title)
        card_layout.addWidget(self.public_shell_subtitle)
        card_layout.addSpacing(14)
        card_layout.addWidget(future_features)
        card_layout.addStretch()

        content_layout.addWidget(welcome_card)
        content_layout.addStretch()
        return content
