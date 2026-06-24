"""Reusable themed placeholder for future public robot features."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PlaceholderScreen(QWidget):
    """Show a friendly holding page that can return safely to home."""

    def __init__(
        self,
        title: str,
        subtitle: str,
        icon: str = "✨",
        parent_window=None,
    ) -> None:
        """Build one public feature placeholder with optional navigation."""
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("placeholder_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui(title, subtitle, icon)
        self._apply_styles()

    def _build_ui(self, title: str, subtitle: str, icon: str) -> None:
        """Arrange the feature identity and central coming-soon card."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(70, 48, 70, 48)
        page_layout.addStretch()

        card = QFrame()
        card.setObjectName("placeholder_card")
        card.setMaximumWidth(780)
        card.setMinimumHeight(470)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(64, 50, 64, 48)
        card_layout.setSpacing(18)

        self.placeholder_icon_label = QLabel(icon)
        self.placeholder_icon_label.setObjectName("placeholder_icon_label")
        self.placeholder_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_title_label = QLabel(title)
        self.placeholder_title_label.setObjectName("placeholder_title_label")
        self.placeholder_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_subtitle_label = QLabel(subtitle)
        self.placeholder_subtitle_label.setObjectName("placeholder_subtitle_label")
        self.placeholder_subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_subtitle_label.setWordWrap(True)
        self.placeholder_message_label = QLabel(
            "This feature will be connected soon."
        )
        self.placeholder_message_label.setObjectName("placeholder_message_label")
        self.placeholder_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.back_home_button = QPushButton("←  Back to Home")
        self.back_home_button.setObjectName("back_home_button")
        self.back_home_button.setMinimumSize(240, 60)
        self.back_home_button.setCursor(Qt.CursorShape.PointingHandCursor)

        callback: Callable | None = getattr(
            self.parent_window,
            "show_home",
            None,
        )
        if callback is not None:
            self.back_home_button.clicked.connect(callback)

        card_layout.addWidget(self.placeholder_icon_label)
        card_layout.addWidget(self.placeholder_title_label)
        card_layout.addWidget(self.placeholder_subtitle_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.placeholder_message_label)
        card_layout.addStretch()
        card_layout.addWidget(
            self.back_home_button,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        page_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        page_layout.addStretch()

    def _apply_styles(self) -> None:
        """Apply the same premium kiosk palette as the public home page."""
        self.setStyleSheet(
            """
            QWidget#placeholder_screen {
                background-color: #07182D;
                color: #FFFFFF;
                font-family: "Segoe UI", Arial, sans-serif;
            }

            QFrame#placeholder_card {
                background-color: #102A46;
                border: 1px solid #315371;
                border-radius: 28px;
            }

            QLabel#placeholder_icon_label {
                color: #F6C85F;
                font-size: 66px;
            }

            QLabel#placeholder_title_label {
                color: #FFFFFF;
                font-size: 35px;
                font-weight: 800;
            }

            QLabel#placeholder_subtitle_label {
                color: #BED0E2;
                font-size: 17px;
            }

            QLabel#placeholder_message_label {
                background-color: rgba(7, 24, 45, 0.48);
                color: #F6C85F;
                border: 1px solid #294967;
                border-radius: 15px;
                padding: 17px 22px;
                font-size: 15px;
                font-weight: 650;
            }

            QPushButton#back_home_button {
                background-color: #F6C85F;
                color: #10233A;
                border: none;
                border-radius: 16px;
                padding: 0 26px;
                font-size: 16px;
                font-weight: 800;
            }

            QPushButton#back_home_button:hover {
                background-color: #FFE092;
            }

            QPushButton#back_home_button:pressed {
                background-color: #E5B84E;
            }
            """
        )
