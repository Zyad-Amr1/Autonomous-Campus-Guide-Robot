"""Admin Login Window for secure access to robot management tools."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from controllers.auth_controller import AuthController
from database.connection import DB_NAME
from ui.shared.theme import (
    BACKGROUND_COLOR,
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    TEXT_COLOR,
)


class LoginWindow(QWidget):
    """Present and process secure Admin Panel login credentials."""

    login_successful = Signal(dict)

    def __init__(self, db_path: str | Path = DB_NAME) -> None:
        """Configure the window and construct its centered login card."""
        super().__init__()
        self.auth_controller = AuthController(db_path)
        self.current_admin: dict | None = None
        self.setWindowTitle("ECU Robot Admin Panel - Login")
        self.resize(900, 600)
        self.setMinimumSize(760, 520)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        """Create and arrange the academic administration login controls."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(48, 48, 48, 48)
        page_layout.addStretch()

        login_card = QFrame()
        login_card.setObjectName("login_card")
        login_card.setMaximumWidth(460)
        login_card.setMinimumWidth(400)

        shadow = QGraphicsDropShadowEffect(login_card)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(15, 23, 42, 45))
        login_card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(login_card)
        card_layout.setContentsMargins(48, 50, 48, 50)
        card_layout.setSpacing(16)

        header_label = QLabel("ECU Robot Admin Panel")
        header_label.setObjectName("header_label")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel(
            "Secure university guidance robot management system"
        )
        subtitle_label.setObjectName("subtitle_label")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setWordWrap(True)

        self.username_input = QLineEdit()
        self.username_input.setObjectName("username_input")
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(48)

        self.password_input = QLineEdit()
        self.password_input.setObjectName("password_input")
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(48)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error_label")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setMinimumHeight(20)

        self.login_button = QPushButton("Login")
        self.login_button.setObjectName("login_button")
        self.login_button.setMinimumHeight(48)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.clicked.connect(self.handle_login)

        card_layout.addWidget(header_label)
        card_layout.addWidget(subtitle_label)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.error_label)
        card_layout.addWidget(self.login_button)

        page_layout.addWidget(login_card, alignment=Qt.AlignmentFlag.AlignCenter)
        page_layout.addStretch()

    def handle_login(self) -> None:
        """Authenticate the entered credentials without opening a dashboard yet."""
        admin = self.auth_controller.login(
            self.username_input.text(),
            self.password_input.text(),
        )

        if admin is None:
            self.current_admin = None
            self.error_label.setText("Invalid username or password.")
            self.error_label.setVisible(True)
            return

        self.current_admin = admin
        self.error_label.clear()
        self.login_successful.emit(admin)

    def _apply_styles(self) -> None:
        """Apply the shared ECU color palette to the login experience."""
        self.setStyleSheet(
            f"""
            LoginWindow {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                font-family: "Segoe UI", Arial, sans-serif;
            }}

            QFrame#login_card {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 18px;
            }}

            QLabel#header_label {{
                color: {PRIMARY_COLOR};
                font-size: 28px;
                font-weight: 700;
            }}

            QLabel#subtitle_label {{
                color: #64748B;
                font-size: 14px;
            }}

            QLineEdit {{
                background-color: #FFFFFF;
                color: {TEXT_COLOR};
                border: 1px solid #CBD5E1;
                border-radius: 9px;
                padding: 0 14px;
                font-size: 15px;
                selection-background-color: {PRIMARY_COLOR};
            }}

            QLineEdit:focus {{
                border: 2px solid {PRIMARY_COLOR};
            }}

            QLabel#error_label {{
                color: #B91C1C;
                font-size: 13px;
            }}

            QPushButton#login_button {{
                background-color: {PRIMARY_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: 9px;
                font-size: 15px;
                font-weight: 700;
            }}

            QPushButton#login_button:hover {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
            }}

            QPushButton#login_button:pressed {{
                background-color: #D99A00;
            }}
            """
        )
