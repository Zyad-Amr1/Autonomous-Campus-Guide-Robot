"""Modern touch-first home screen for the ECU public dashboard."""

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.public.theme import (
    BORDER,
    CARD_PADDING,
    CARD_RADIUS,
    CHARCOAL,
    ECU_RED,
    GOLD_LIGHT,
    HEADER_FONT_SIZE,
    OFF_WHITE,
    PAGE_PADDING,
    TEXT_DARK,
    TEXT_MUTED,
    TOUCH_BUTTON_HEIGHT,
    WHITE,
    font,
    px,
)


class HomeScreen(QWidget):
    """Show the public dashboard welcome header and large action tiles."""

    QUICK_ASK_QUESTIONS = (
        "Where is the library?",
        "How can I find my classroom?",
        "Who can help me with admissions?",
        "What events are available today?",
    )

    def __init__(self, parent_window=None) -> None:
        """Build the home screen and optionally connect tile callbacks."""
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("public_home_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        """Arrange the branded header, hero panel, cards, and quick asks."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(
            PAGE_PADDING + 10,
            PAGE_PADDING,
            PAGE_PADDING + 10,
            PAGE_PADDING,
        )
        page_layout.setSpacing(18)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(18)
        header_copy = QVBoxLayout()
        header_copy.setSpacing(3)
        self.home_brand_label = QLabel("ECU Smart Assistant")
        self.home_brand_label.setObjectName("home_brand_label")
        self.home_brand_subtitle = QLabel("Public guidance dashboard")
        self.home_brand_subtitle.setObjectName("home_brand_subtitle")
        header_copy.addWidget(self.home_brand_label)
        header_copy.addWidget(self.home_brand_subtitle)
        self.home_header_badge = QLabel("Egyptian Chinese University")
        self.home_header_badge.setObjectName("home_header_badge")
        self.home_header_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addLayout(header_copy)
        header_layout.addStretch()
        header_layout.addWidget(self.home_header_badge)
        page_layout.addLayout(header_layout)

        hero_card = QFrame()
        hero_card.setObjectName("home_hero_card")
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(30, 24, 26, 24)
        hero_layout.setSpacing(28)
        hero_copy = QVBoxLayout()
        hero_copy.setSpacing(8)

        self.home_welcome_title = QLabel("Welcome to ECU Smart Assistant")
        self.home_welcome_title.setObjectName("home_welcome_title")
        self.home_welcome_title.setWordWrap(True)
        self.home_welcome_subtitle = QLabel(
            "Find your way, ask questions, and explore university information."
        )
        self.home_welcome_subtitle.setObjectName("home_welcome_subtitle")
        self.home_welcome_subtitle.setWordWrap(True)
        hero_copy.addWidget(self.home_welcome_title)
        hero_copy.addWidget(self.home_welcome_subtitle)
        hero_copy.addStretch()

        self.home_time_block = QFrame()
        self.home_time_block.setObjectName("home_time_block")
        time_layout = QVBoxLayout(self.home_time_block)
        time_layout.setContentsMargins(22, 16, 22, 16)
        time_layout.setSpacing(4)
        now = QDateTime.currentDateTime()
        self.home_time_label = QLabel(now.toString("h:mm AP"))
        self.home_time_label.setObjectName("home_time_label")
        self.home_date_label = QLabel(now.toString("dddd, MMMM d"))
        self.home_date_label.setObjectName("home_date_label")
        self.home_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.home_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_layout.addWidget(self.home_time_label)
        time_layout.addWidget(self.home_date_label)

        hero_layout.addLayout(hero_copy, stretch=1)
        hero_layout.addWidget(self.home_time_block)
        page_layout.addWidget(hero_card)

        self.home_explore_title = QLabel("Main actions")
        self.home_explore_title.setObjectName("home_explore_title")
        page_layout.addWidget(self.home_explore_title)

        explore_tiles = QGridLayout()
        explore_tiles.setSpacing(14)
        self.home_map_tile = self._create_tile(
            "Campus Map\nNavigate buildings and services",
            "home_map_tile",
            "map",
        )
        self.home_chat_tile = self._create_tile(
            "Ask Assistant\nGet quick answers",
            "home_chat_tile",
            "chat",
        )
        self.home_about_tile = self._create_tile(
            "University Info\nExplore ECU information",
            "home_about_tile",
            "about",
        )
        explore_tiles.addWidget(self.home_map_tile, 0, 0)
        explore_tiles.addWidget(self.home_chat_tile, 0, 1)
        explore_tiles.addWidget(self.home_about_tile, 0, 2)
        page_layout.addLayout(explore_tiles)

        self.home_secondary_title = QLabel("More services")
        self.home_secondary_title.setObjectName("home_secondary_title")
        page_layout.addWidget(self.home_secondary_title)

        secondary_tiles = QGridLayout()
        secondary_tiles.setSpacing(14)
        self.home_staff_tile = self._create_tile(
            "Staff Directory\nFind professors and offices",
            "home_staff_tile",
            "staff",
        )
        self.home_schedule_tile = self._create_tile(
            "Today's Schedule\nView classes and rooms",
            "home_schedule_tile",
            "schedule",
        )
        self.home_news_tile = self._create_tile(
            "Events & News\nSee campus updates",
            "home_news_tile",
            "news",
        )
        self.home_info_tile = QPushButton(self)
        self.home_info_tile.setObjectName("home_info_tile")
        self.home_info_tile.setText("Data Access\nProtected university data")
        self.home_info_tile.setProperty("tileRole", "explore")
        self.home_info_tile.setMinimumHeight(118)
        self.home_info_tile.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.home_info_tile.setCursor(Qt.CursorShape.PointingHandCursor)
        callback = getattr(self.parent_window, "show_data", None)
        if callback is not None:
            self.home_info_tile.clicked.connect(callback)
        secondary_tiles.addWidget(self.home_staff_tile, 0, 0)
        secondary_tiles.addWidget(self.home_schedule_tile, 0, 1)
        secondary_tiles.addWidget(self.home_news_tile, 0, 2)
        secondary_tiles.addWidget(self.home_info_tile, 0, 3)
        page_layout.addLayout(secondary_tiles, stretch=1)

        self.quick_ask_title = QLabel("Quick Ask")
        self.quick_ask_title.setObjectName("quick_ask_title")
        page_layout.addWidget(self.quick_ask_title)

        self.quick_ask_section = QWidget()
        self.quick_ask_section.setObjectName("quick_ask_section")
        quick_ask_layout = QHBoxLayout(self.quick_ask_section)
        quick_ask_layout.setContentsMargins(0, 0, 0, 0)
        quick_ask_layout.setSpacing(12)
        self.quick_ask_chips: list[QPushButton] = []
        for index, question in enumerate(self.QUICK_ASK_QUESTIONS, start=1):
            chip = self._create_quick_ask_chip(index, question)
            self.quick_ask_chips.append(chip)
            setattr(self, f"quick_ask_chip_{index}", chip)
            quick_ask_layout.addWidget(chip)
        page_layout.addWidget(self.quick_ask_section)

    def _create_tile(
        self,
        text: str,
        object_name: str,
        navigation_key: str,
    ) -> QPushButton:
        """Create one touch-friendly Explore card."""
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setProperty("tileRole", "explore")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(118)
        button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        callback = getattr(self.parent_window, f"show_{navigation_key}", None)
        if callback is not None:
            button.clicked.connect(callback)
        return button

    def _create_quick_ask_chip(self, index: int, question: str) -> QPushButton:
        """Create one suggested chatbot question chip."""
        chip = QPushButton(question)
        chip.setObjectName(f"quick_ask_chip_{index}")
        chip.setProperty("tileRole", "quickAsk")
        chip.setCursor(Qt.CursorShape.PointingHandCursor)
        chip.setMinimumHeight(TOUCH_BUTTON_HEIGHT)
        chip.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        callback = getattr(self.parent_window, "open_chat_with_question", None)
        if callback is not None:
            chip.clicked.connect(
                lambda checked=False, text=question: callback(text)
            )
        return chip

    def _apply_styles(self) -> None:
        """Apply the shared ECU public dashboard visual language."""
        self.setStyleSheet(
            f"""
            QWidget#public_home_screen {{
                background-color: {OFF_WHITE};
                color: {TEXT_DARK};
                {font(18)}
            }}

            QLabel#home_brand_label {{
                color: {CHARCOAL};
                {font(24, 850)}
            }}

            QLabel#home_brand_subtitle {{
                color: {TEXT_MUTED};
                {font(13, 650)}
            }}

            QLabel#home_header_badge {{
                background-color: {WHITE};
                color: {TEXT_DARK};
                border: 1px solid {BORDER};
                border-radius: {px(18)};
                padding: 8px 18px;
                {font(12, 800)}
            }}

            QFrame#home_hero_card {{
                background-color: {CHARCOAL};
                border: 1px solid #34373C;
                border-radius: {px(CARD_RADIUS + 6)};
            }}

            QLabel#home_welcome_title {{
                color: {WHITE};
                {font(HEADER_FONT_SIZE, 800)}
            }}

            QLabel#home_welcome_subtitle {{
                color: #E5E7EB;
                {font(18, 500)}
            }}

            QFrame#home_time_block {{
                background-color: {WHITE};
                border: 1px solid rgba(215, 25, 32, 90);
                border-radius: {px(CARD_RADIUS)};
            }}

            QLabel#home_time_label {{
                color: {TEXT_DARK};
                {font(28, 850)}
            }}

            QLabel#home_date_label {{
                color: {TEXT_MUTED};
                {font(13, 700)}
            }}

            QLabel#home_explore_title,
            QLabel#home_secondary_title,
            QLabel#quick_ask_title {{
                color: {CHARCOAL};
                {font(20, 850)}
            }}

            QPushButton[tileRole="explore"] {{
                background-color: {WHITE};
                color: {TEXT_DARK};
                border: 1px solid {BORDER};
                border-radius: {px(CARD_RADIUS)};
                padding: {px(14)} {px(CARD_PADDING)};
                text-align: left;
                {font(17, 800)}
            }}

            QPushButton[tileRole="explore"]:hover {{
                background-color: #FFF9F9;
                border-color: {ECU_RED};
            }}

            QPushButton[tileRole="explore"]:pressed {{
                background-color: {GOLD_LIGHT};
            }}

            QWidget#quick_ask_section {{
                background-color: transparent;
            }}

            QPushButton[tileRole="quickAsk"] {{
                background-color: {WHITE};
                color: {TEXT_DARK};
                border: 1px solid {BORDER};
                border-radius: {px(TOUCH_BUTTON_HEIGHT // 2)};
                padding: 0 {px(18)};
                text-align: left;
                {font(14, 700)}
            }}

            QPushButton[tileRole="quickAsk"]:hover {{
                background-color: #FFF9F9;
                border-color: {ECU_RED};
            }}

            QPushButton[tileRole="quickAsk"]:pressed {{
                background-color: {GOLD_LIGHT};
            }}
            """
        )
