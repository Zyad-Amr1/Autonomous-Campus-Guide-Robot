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
    FLOATING_CHAT_BUTTON_STYLE,
    GOLD,
    NAVY,
    NAVY_DARK,
    OFF_WHITE,
    SIDEBAR_BUTTON_STYLE,
    SIDEBAR_WIDTH,
    TOUCH_BUTTON_HEIGHT,
)
from ui.public.translations import TRANSLATIONS


class PublicMainWindow(QMainWindow):
    """Display seven lightweight public placeholders with sidebar navigation."""

    _SIDEBAR_ITEMS = (
        ("home", "sidebar_home_button"),
        ("map", "sidebar_map_button"),
        ("staff", "sidebar_staff_button"),
        ("schedule", "sidebar_schedule_button"),
        ("news", "sidebar_news_button"),
        ("about", "sidebar_about_button"),
        ("chat", "sidebar_chat_button"),
    )

    _PLACEHOLDER_PAGES = (
        ("home", "HOME"),
        ("map", "MAP"),
        ("staff", "STAFF"),
        ("schedule", "TIME"),
        ("news", "NEWS"),
        ("about", "INFO"),
        ("chat", "CHAT"),
    )

    def __init__(self) -> None:
        """Create the sidebar and seven-page placeholder stack."""
        super().__init__()
        self.current_language = "en"
        self.setObjectName("public_main_window")
        self.setMinimumSize(1280, 800)
        self.sidebar_buttons: dict[str, QPushButton] = {}
        self.placeholder_pages: dict[str, PlaceholderPage] = {}
        self._build_ui()
        self.apply_language()
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
        content = self._create_content()
        shell_layout.addWidget(sidebar)
        shell_layout.addWidget(content, stretch=1)

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

        self.app_title_label = QLabel()
        self.app_title_label.setObjectName("public_sidebar_title")
        self.app_title_label.setStyleSheet(
            f"color: {GOLD}; font-size: 25px; font-weight: 800;"
        )
        self.app_subtitle_label = QLabel()
        self.app_subtitle_label.setObjectName("public_sidebar_subtitle")
        self.app_subtitle_label.setStyleSheet(
            f"color: {OFF_WHITE}; font-size: 13px; font-weight: 600;"
        )
        sidebar_layout.addWidget(self.app_title_label)
        sidebar_layout.addWidget(self.app_subtitle_label)
        sidebar_layout.addSpacing(24)

        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)
        for index, (key, object_name) in enumerate(self._SIDEBAR_ITEMS):
            button = QPushButton()
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

        self.language_toggle_button = QPushButton()
        self.language_toggle_button.setObjectName("language_toggle_button")
        self.language_toggle_button.setMinimumHeight(TOUCH_BUTTON_HEIGHT)
        self.language_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.language_toggle_button.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        self.language_toggle_button.clicked.connect(
            lambda checked=False: self.toggle_language()
        )
        sidebar_layout.addWidget(self.language_toggle_button)

        sidebar_layout.addStretch()
        footer = QLabel("Egyptian Chinese University")
        footer.setObjectName("public_sidebar_footer")
        footer.setWordWrap(True)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color: {OFF_WHITE}; font-size: 11px;")
        sidebar_layout.addWidget(footer)
        return sidebar

    def _create_content(self) -> QFrame:
        """Create the page stack and persistent bottom-right Ask Me action."""
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
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.public_page_stack = self._create_page_stack()
        content_layout.addWidget(self.public_page_stack, stretch=1)

        floating_row = QHBoxLayout()
        floating_row.setContentsMargins(0, 0, 28, 24)
        floating_row.addStretch()
        self.floating_ask_button = QPushButton()
        self.floating_ask_button.setObjectName("floating_ask_button")
        self.floating_ask_button.setMinimumSize(150, TOUCH_BUTTON_HEIGHT)
        self.floating_ask_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.floating_ask_button.setStyleSheet(
            FLOATING_CHAT_BUTTON_STYLE
            + """
            QPushButton#floating_ask_button {
                min-width: 150px;
                max-width: 190px;
                padding: 0 24px;
            }
            """
        )
        self.floating_ask_button.clicked.connect(
            lambda checked=False: self.show_chat()
        )
        floating_row.addWidget(self.floating_ask_button)
        content_layout.addLayout(floating_row)
        return content

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
        for key, icon in self._PLACEHOLDER_PAGES:
            page = PlaceholderPage("", "", icon)
            self.placeholder_pages[key] = page
            page_stack.addWidget(page)
        return page_stack

    def toggle_language(self) -> None:
        """Switch between English and Arabic public dashboard copy."""
        self.current_language = "ar" if self.current_language == "en" else "en"
        self.apply_language()

    def apply_language(self) -> None:
        """Apply the current language to visible text and layout direction."""
        translations = TRANSLATIONS[self.current_language]
        is_arabic = self.current_language == "ar"
        direction = (
            Qt.LayoutDirection.RightToLeft
            if is_arabic
            else Qt.LayoutDirection.LeftToRight
        )
        sidebar_alignment = "right" if is_arabic else "left"

        self.setLayoutDirection(direction)
        self.centralWidget().setLayoutDirection(direction)
        self.public_page_stack.setLayoutDirection(direction)
        self.setWindowTitle(translations["app_title"].replace("\n", " "))
        self.app_title_label.setText(translations["app_title"])
        self.app_subtitle_label.setText(translations["app_subtitle"])
        self.language_toggle_button.setText(translations["language_toggle"])
        self.floating_ask_button.setText(translations["ask_me"])
        self.floating_ask_button.setLayoutDirection(direction)

        for key, button in self.sidebar_buttons.items():
            button.setText(translations[key])
            button.setLayoutDirection(direction)
            button.setStyleSheet(
                SIDEBAR_BUTTON_STYLE.replace(
                    "text-align: left;",
                    f"text-align: {sidebar_alignment};",
                )
            )

        self.language_toggle_button.setLayoutDirection(direction)
        self.language_toggle_button.setStyleSheet(
            SIDEBAR_BUTTON_STYLE.replace(
                "text-align: left;",
                f"text-align: {sidebar_alignment};",
            )
        )

        for key, page in self.placeholder_pages.items():
            page.setLayoutDirection(direction)
            page.update_text(
                translations[f"placeholder_{key}_title"],
                translations[f"placeholder_{key}_subtitle"],
                translations["placeholder_message"],
            )

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
