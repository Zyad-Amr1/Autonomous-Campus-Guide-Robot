"""Protected public-dashboard gate for future data management access."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.public.theme import (
    BORDER,
    BUTTON_HEIGHT,
    CARD_PADDING,
    CARD_RADIUS,
    CHARCOAL,
    ECU_RED,
    ECU_RED_DARK,
    GOLD_LIGHT,
    OFF_WHITE,
    PAGE_PADDING,
    TEXT_DARK,
    TEXT_MUTED,
    TOUCH_BUTTON_HEIGHT,
    WHITE,
    font,
    px,
)


class AdminGateScreen(QWidget):
    """Display a modern password gate before future data tools."""

    ADMIN_PASSWORD = "admin123"

    def __init__(self, parent_window=None) -> None:
        """Build the public-themed protected access screen."""
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("admin_gate_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        """Arrange the password form inside a public-dashboard card."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(
            PAGE_PADDING * 2,
            PAGE_PADDING * 2,
            PAGE_PADDING * 2,
            PAGE_PADDING * 2,
        )
        page_layout.addStretch()

        card = QFrame()
        card.setObjectName("admin_gate_card")
        card.setMinimumWidth(560)
        card.setMaximumWidth(720)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 34, 36, 34)
        card_layout.setSpacing(18)

        eyebrow = QLabel("Protected Area")
        eyebrow.setObjectName("admin_gate_eyebrow")
        title = QLabel("Admin Data Access")
        title.setObjectName("admin_gate_title")
        subtitle = QLabel("Enter admin password to manage university data.")
        subtitle.setObjectName("admin_gate_subtitle")
        subtitle.setWordWrap(True)

        self.admin_password_input = QLineEdit()
        self.admin_password_input.setObjectName("admin_password_input")
        self.admin_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.admin_password_input.setPlaceholderText("Password")
        self.admin_password_input.setMinimumHeight(BUTTON_HEIGHT)

        self.admin_unlock_button = QPushButton("Unlock")
        self.admin_unlock_button.setObjectName("admin_unlock_button")
        self.admin_unlock_button.setMinimumHeight(BUTTON_HEIGHT)
        self.admin_unlock_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.admin_unlock_button.clicked.connect(self.validate_password)

        self.admin_gate_status_label = QLabel("")
        self.admin_gate_status_label.setObjectName("admin_gate_status_label")
        self.admin_gate_status_label.setWordWrap(True)

        card_layout.addWidget(eyebrow)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.admin_password_input)
        card_layout.addWidget(self.admin_unlock_button)
        card_layout.addWidget(self.admin_gate_status_label)

        page_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        page_layout.addStretch()

    def validate_password(self) -> None:
        """Check the temporary gate password and update status text."""
        if self.admin_password_input.text() == self.ADMIN_PASSWORD:
            self.admin_gate_status_label.setText(
                "Access granted. Opening data dashboard."
            )
            if self.parent_window is not None:
                self.parent_window.show_data_dashboard()
            return
        self.admin_gate_status_label.setText("Incorrect password. Please try again.")

    def _apply_styles(self) -> None:
        """Apply the ECU public dashboard visual language."""
        self.setStyleSheet(
            f"""
            QWidget#admin_gate_screen {{
                background-color: {OFF_WHITE};
                color: {TEXT_DARK};
                {font(18)}
            }}

            QFrame#admin_gate_card {{
                background-color: {WHITE};
                border: 1px solid {BORDER};
                border-radius: {px(CARD_RADIUS + 6)};
            }}

            QLabel#admin_gate_eyebrow {{
                color: {ECU_RED};
                {font(13, 850)}
            }}

            QLabel#admin_gate_title {{
                color: {CHARCOAL};
                {font(32, 850)}
            }}

            QLabel#admin_gate_subtitle {{
                color: {TEXT_MUTED};
                {font(16, 600)}
            }}

            QLineEdit#admin_password_input {{
                background-color: {OFF_WHITE};
                color: {TEXT_DARK};
                border: 1px solid {BORDER};
                border-radius: {px(18)};
                padding: 0 {px(CARD_PADDING)};
                min-height: {px(BUTTON_HEIGHT)};
                {font(17, 650)}
            }}

            QLineEdit#admin_password_input:focus {{
                border: 2px solid {ECU_RED};
            }}

            QPushButton#admin_unlock_button {{
                background-color: {ECU_RED};
                color: {WHITE};
                border: none;
                border-radius: {px(18)};
                padding: 0 {px(CARD_PADDING)};
                min-height: {px(BUTTON_HEIGHT)};
                {font(18, 800)}
            }}

            QPushButton#admin_unlock_button:hover {{
                background-color: {ECU_RED_DARK};
            }}

            QPushButton#admin_unlock_button:pressed {{
                background-color: {GOLD_LIGHT};
                color: {TEXT_DARK};
            }}

            QLabel#admin_gate_status_label {{
                color: {TEXT_MUTED};
                {font(15, 700)}
                min-height: {px(28)};
            }}
            """
        )
