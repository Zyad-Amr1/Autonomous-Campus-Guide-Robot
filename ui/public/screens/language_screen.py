"""Language onboarding screen for the public ECU kiosk."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from ui.public.theme import (
    BORDER,
    CHARCOAL,
    ECU_RED,
    ECU_RED_DARK,
    OFF_WHITE,
    TEXT_MUTED,
    WHITE,
    font,
    px,
)


class LanguageSelectionScreen(QWidget):
    """Let visitors choose the public dashboard language before navigation."""

    def __init__(self, parent_window=None) -> None:
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("language_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(96, 72, 96, 72)
        layout.setSpacing(22)
        layout.addStretch()

        self.title_label = QLabel("ECU Smart Assistant")
        self.title_label.setObjectName("language_screen_title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_label = QLabel("Touchscreen Campus Guide")
        self.subtitle_label.setObjectName("language_screen_subtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.choose_english_button = QPushButton("English")
        self.choose_english_button.setObjectName("choose_english_button")
        self.choose_arabic_button = QPushButton("العربية")
        self.choose_arabic_button.setObjectName("choose_arabic_button")

        for button in (self.choose_english_button, self.choose_arabic_button):
            button.setMinimumHeight(92)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.choose_english_button.clicked.connect(
            lambda checked=False: self._choose_language("en")
        )
        self.choose_arabic_button.clicked.connect(
            lambda checked=False: self._choose_language("ar")
        )

        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addSpacing(28)
        layout.addWidget(self.choose_english_button)
        layout.addWidget(self.choose_arabic_button)
        layout.addStretch()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#language_screen {{
                background-color: {OFF_WHITE};
                color: {CHARCOAL};
            }}

            QLabel#language_screen_title {{
                color: {CHARCOAL};
                {font(44, 900)}
            }}

            QLabel#language_screen_subtitle {{
                color: {TEXT_MUTED};
                {font(22, 650)}
            }}

            QPushButton#choose_english_button,
            QPushButton#choose_arabic_button {{
                background-color: {WHITE};
                color: {CHARCOAL};
                border: 1px solid {BORDER};
                border-radius: {px(24)};
                padding: 0 {px(28)};
                {font(28, 850)}
            }}

            QPushButton#choose_english_button:hover,
            QPushButton#choose_arabic_button:hover {{
                border: 2px solid {ECU_RED};
                background-color: #FFF9F9;
            }}

            QPushButton#choose_english_button:pressed,
            QPushButton#choose_arabic_button:pressed {{
                background-color: {ECU_RED};
                color: {WHITE};
                border-color: {ECU_RED_DARK};
            }}
            """
        )

    def _choose_language(self, language: str) -> None:
        callback = getattr(self.parent_window, "select_language", None)
        if callback is not None:
            callback(language)
