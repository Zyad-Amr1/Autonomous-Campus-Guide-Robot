"""Modern touch-first home screen for the ECU public dashboard."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.public.theme import (
    CARD_RADIUS,
    GOLD,
    GOLD_LIGHT,
    HEADER_FONT_SIZE,
    LIGHT_GRAY,
    NAVY,
    NAVY_DARK,
    NAVY_LIGHT,
    OFF_WHITE,
    PAGE_PADDING,
    TEXT_DARK,
    TOUCH_BUTTON_HEIGHT,
    WHITE,
    font,
    px,
)


class HomeScreen(QWidget):
    """Show the public dashboard welcome header and large action tiles."""

    def __init__(self, parent_window=None) -> None:
        """Build the home screen and optionally connect tile callbacks."""
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("public_home_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        """Arrange welcome copy, three large cards, and secondary tiles."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(
            PAGE_PADDING * 2,
            PAGE_PADDING * 2,
            PAGE_PADDING * 2,
            PAGE_PADDING * 2,
        )
        page_layout.setSpacing(26)

        self.home_welcome_title = QLabel("Welcome to ECU Smart Assistant")
        self.home_welcome_title.setObjectName("home_welcome_title")
        self.home_welcome_title.setWordWrap(True)

        self.home_welcome_subtitle = QLabel(
            "Choose what you need from the robot guide."
        )
        self.home_welcome_subtitle.setObjectName("home_welcome_subtitle")
        self.home_welcome_subtitle.setWordWrap(True)

        page_layout.addWidget(self.home_welcome_title)
        page_layout.addWidget(self.home_welcome_subtitle)

        main_tiles = QGridLayout()
        main_tiles.setSpacing(18)
        self.home_map_tile = self._create_tile(
            "🗺️ Campus Map",
            "home_map_tile",
            "map",
            is_primary=True,
        )
        self.home_chat_tile = self._create_tile(
            "💬 Ask Chatbot",
            "home_chat_tile",
            "chat",
            is_primary=True,
        )
        self.home_info_tile = self._create_tile(
            "🏛️ University Info",
            "home_info_tile",
            "about",
            is_primary=True,
        )
        main_tiles.addWidget(self.home_map_tile, 0, 0)
        main_tiles.addWidget(self.home_chat_tile, 0, 1)
        main_tiles.addWidget(self.home_info_tile, 0, 2)
        page_layout.addLayout(main_tiles, stretch=2)

        secondary_tiles = QGridLayout()
        secondary_tiles.setSpacing(14)
        self.home_staff_tile = self._create_tile(
            "👨‍🏫 Staff",
            "home_staff_tile",
            "staff",
        )
        self.home_schedule_tile = self._create_tile(
            "📚 Schedule",
            "home_schedule_tile",
            "schedule",
        )
        self.home_news_tile = self._create_tile(
            "📰 News",
            "home_news_tile",
            "news",
        )
        self.home_about_tile = self._create_tile(
            "🏛️ About ECU",
            "home_about_tile",
            "about",
        )
        secondary_tiles.addWidget(self.home_staff_tile, 0, 0)
        secondary_tiles.addWidget(self.home_schedule_tile, 0, 1)
        secondary_tiles.addWidget(self.home_news_tile, 0, 2)
        secondary_tiles.addWidget(self.home_about_tile, 0, 3)
        page_layout.addLayout(secondary_tiles, stretch=1)
        page_layout.addStretch()

    def _create_tile(
        self,
        text: str,
        object_name: str,
        navigation_key: str,
        *,
        is_primary: bool = False,
    ) -> QPushButton:
        """Create one large, touch-friendly home tile."""
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setProperty("tileRole", "primary" if is_primary else "secondary")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(TOUCH_BUTTON_HEIGHT * (2 if is_primary else 1))
        button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        callback = getattr(self.parent_window, f"show_{navigation_key}", None)
        if callback is not None:
            button.clicked.connect(callback)
        return button

    def _apply_styles(self) -> None:
        """Apply the shared ECU public dashboard visual language."""
        self.setStyleSheet(
            f"""
            QWidget#public_home_screen {{
                background-color: {NAVY_DARK};
                color: {WHITE};
                {font(18)}
            }}

            QLabel#home_welcome_title {{
                color: {WHITE};
                {font(HEADER_FONT_SIZE, 800)}
            }}

            QLabel#home_welcome_subtitle {{
                color: {LIGHT_GRAY};
                {font(18, 500)}
            }}

            QPushButton[tileRole="primary"] {{
                background-color: {OFF_WHITE};
                color: {TEXT_DARK};
                border: 2px solid {GOLD};
                border-radius: {px(CARD_RADIUS)};
                padding: 0 {px(PAGE_PADDING)};
                text-align: left;
                {font(24, 800)}
            }}

            QPushButton[tileRole="primary"]:hover {{
                background-color: {GOLD_LIGHT};
                border-color: {GOLD_LIGHT};
            }}

            QPushButton[tileRole="primary"]:pressed {{
                background-color: {GOLD};
            }}

            QPushButton[tileRole="secondary"] {{
                background-color: {NAVY_LIGHT};
                color: {OFF_WHITE};
                border: 1px solid {NAVY};
                border-radius: {px(CARD_RADIUS)};
                padding: 0 {px(22)};
                text-align: left;
                {font(18, 700)}
            }}

            QPushButton[tileRole="secondary"]:hover {{
                background-color: {NAVY};
                border-color: {GOLD_LIGHT};
            }}

            QPushButton[tileRole="secondary"]:pressed {{
                background-color: {NAVY_DARK};
            }}
            """
        )
