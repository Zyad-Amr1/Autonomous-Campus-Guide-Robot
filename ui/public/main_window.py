"""Stable sidebar navigation shell for the ECU Smart Assistant."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.public.screens.placeholder_page import PlaceholderPage
from ui.public.theme import (
    APP_BACKGROUND_STYLE,
    GOLD,
    NAVY,
    NAVY_DARK,
    OFF_WHITE,
    SIDEBAR_BUTTON_STYLE,
    SIDEBAR_WIDTH,
    TOUCH_BUTTON_HEIGHT,
)


class PublicMainWindow(QMainWindow):
    """Display seven lightweight public placeholders with sidebar navigation."""

    _SIDEBAR_ITEMS = (
        ("home", "⌂  Home", "sidebar_home_button"),
        ("map", "◇  Map", "sidebar_map_button"),
        ("staff", "♟  Staff", "sidebar_staff_button"),
        ("schedule", "▤  Schedule", "sidebar_schedule_button"),
        ("news", "◆  News", "sidebar_news_button"),
        ("about", "ⓘ  About", "sidebar_about_button"),
        ("chat", "◉  Chat", "sidebar_chat_button"),
    )

    _PLACEHOLDER_PAGES = (
        ("Home", "Welcome to ECU Smart Assistant.", "⌂"),
        (
            "Campus Map",
            "Interactive room and building navigation will be connected here.",
            "◇",
        ),
        (
            "Staff Directory",
            "Professor and office search will be connected here.",
            "♟",
        ),
        (
            "Today's Schedule",
            "Course schedules and room details will be connected here.",
            "▤",
        ),
        (
            "Events & News",
            "Campus events and important dates will be connected here.",
            "◆",
        ),
        (
            "About ECU",
            "University information and faculties will be connected here.",
            "ⓘ",
        ),
        (
            "Chat Assistant",
            "The ECU question-answer chatbot will be connected here.",
            "◉",
        ),
    )

    def __init__(self) -> None:
        """Create the sidebar and seven-page placeholder stack."""
        super().__init__()
        self.setWindowTitle("ECU Smart Assistant")
        self.setObjectName("public_main_window")
        self.setMinimumSize(1280, 800)
        self.sidebar_buttons: dict[str, QPushButton] = {}
        self._build_ui()
        self.show_home()

    def _build_ui(self) -> None:
        """Build the lightweight two-column public navigation shell."""
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
        self.public_page_stack = self._create_page_stack()
        shell_layout.addWidget(sidebar)
        shell_layout.addWidget(self.public_page_stack, stretch=1)

    def _create_sidebar(self) -> QFrame:
        """Create and wire the touch-friendly public navigation rail."""
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

        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)
        for index, (key, label, object_name) in enumerate(self._SIDEBAR_ITEMS):
            button = QPushButton(label)
            button.setObjectName(object_name)
            button.setCheckable(True)
            button.setMinimumHeight(TOUCH_BUTTON_HEIGHT)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet(SIDEBAR_BUTTON_STYLE)
            method = getattr(self, f"show_{key}")
            button.clicked.connect(
                lambda checked=False, callback=method: callback()
            )
            self.nav_button_group.addButton(button, index)
            self.sidebar_buttons[key] = button
            setattr(self, object_name, button)
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()
        footer = QLabel("Egyptian Chinese University")
        footer.setObjectName("public_sidebar_footer")
        footer.setWordWrap(True)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color: {OFF_WHITE}; font-size: 11px;")
        sidebar_layout.addWidget(footer)
        return sidebar

    def _create_page_stack(self) -> QStackedWidget:
        """Create exactly seven themed blank placeholder pages."""
        page_stack = QStackedWidget()
        page_stack.setObjectName("public_page_stack")
        page_stack.setStyleSheet(
            f"""
            QStackedWidget#public_page_stack {{
                background-color: {NAVY_DARK};
                border: none;
            }}
            """
        )
        for title, subtitle, icon in self._PLACEHOLDER_PAGES:
            page_stack.addWidget(PlaceholderPage(title, subtitle, icon))
        return page_stack

    def set_active_nav(self, key: str) -> None:
        """Mark one visual sidebar item as the active section."""
        for button_key, button in self.sidebar_buttons.items():
            button.setChecked(button_key == key)

    def _show_page(self, index: int, key: str) -> None:
        """Switch to one placeholder and synchronize the active nav item."""
        self.public_page_stack.setCurrentIndex(index)
        self.set_active_nav(key)

    def show_home(self) -> None:
        """Show the Home placeholder."""
        self._show_page(0, "home")

    def show_map(self) -> None:
        """Show the Campus Map placeholder."""
        self._show_page(1, "map")

    def show_staff(self) -> None:
        """Show the Staff Directory placeholder."""
        self._show_page(2, "staff")

    def show_schedule(self) -> None:
        """Show the Schedule placeholder."""
        self._show_page(3, "schedule")

    def show_news(self) -> None:
        """Show the Events and News placeholder."""
        self._show_page(4, "news")

    def show_about(self) -> None:
        """Show the About ECU placeholder."""
        self._show_page(5, "about")

    def show_chat(self) -> None:
        """Show the Chat Assistant placeholder."""
        self._show_page(6, "chat")
