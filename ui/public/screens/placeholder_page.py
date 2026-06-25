"""Reusable blank placeholder for public dashboard navigation sections."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from ui.public.theme import (
    CARD_STYLE,
    GLASS_CARD_STYLE,
    GOLD,
    HEADER_STYLE,
    NAVY_DARK,
    PAGE_PADDING,
    SUBTITLE_STYLE,
    TEXT_DARK,
)


class PlaceholderPage(QWidget):
    """Display a modern holding card for a future public feature."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon: str = "INFO",
    ) -> None:
        """Build one themed placeholder without loading feature logic."""
        super().__init__()
        self.setObjectName("public_placeholder_page")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui(title, subtitle, icon)

    def _build_ui(self, title: str, subtitle: str, icon: str) -> None:
        """Arrange the icon, section identity, and next-step message."""
        self.setStyleSheet(
            f"""
            QWidget#public_placeholder_page {{
                background-color: {NAVY_DARK};
                border: none;
            }}
            """
        )
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(
            PAGE_PADDING * 2,
            PAGE_PADDING * 2,
            PAGE_PADDING * 2,
            PAGE_PADDING * 2,
        )
        page_layout.addStretch()

        card = QFrame()
        card.setObjectName("public_placeholder_card")
        card.setMinimumHeight(440)
        card.setStyleSheet(
            GLASS_CARD_STYLE.replace(
                "QFrame {",
                "QFrame#public_placeholder_card {",
                1,
            )
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(52, 46, 52, 46)
        card_layout.setSpacing(18)

        self.placeholder_icon_label = QLabel(icon)
        self.placeholder_icon_label.setObjectName("placeholder_icon_label")
        self.placeholder_icon_label.setFixedSize(82, 64)
        self.placeholder_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_icon_label.setStyleSheet(
            f"""
            QLabel#placeholder_icon_label {{
                background-color: {GOLD};
                color: {NAVY_DARK};
                border: none;
                border-radius: 15px;
                font-size: 25px;
                font-weight: 800;
            }}
            """
        )
        self.placeholder_title_label = QLabel(title)
        self.placeholder_title_label.setObjectName("placeholder_title_label")
        self.placeholder_title_label.setStyleSheet(HEADER_STYLE)
        self.placeholder_subtitle_label = QLabel(subtitle)
        self.placeholder_subtitle_label.setObjectName(
            "placeholder_subtitle_label"
        )
        self.placeholder_subtitle_label.setWordWrap(True)
        self.placeholder_subtitle_label.setStyleSheet(SUBTITLE_STYLE)
        self.placeholder_message_label = QLabel(
            "This section is ready for the next development step."
        )
        self.placeholder_message_label.setObjectName("placeholder_message_label")
        self.placeholder_message_label.setWordWrap(True)
        self.placeholder_message_label.setStyleSheet(
            CARD_STYLE.replace(
                "QFrame {",
                "QLabel#placeholder_message_label {",
                1,
            )
            + f"\nQLabel#placeholder_message_label {{ color: {TEXT_DARK}; }}"
        )

        card_layout.addWidget(self.placeholder_icon_label)
        card_layout.addWidget(self.placeholder_title_label)
        card_layout.addWidget(self.placeholder_subtitle_label)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.placeholder_message_label)
        card_layout.addStretch()

        page_layout.addWidget(card)
        page_layout.addStretch()

    def update_text(self, title: str, subtitle: str, message: str) -> None:
        """Refresh visible placeholder copy after a language change."""
        self.placeholder_title_label.setText(title)
        self.placeholder_subtitle_label.setText(subtitle)
        self.placeholder_message_label.setText(message)
