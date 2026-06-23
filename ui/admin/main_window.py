"""Admin Dashboard shell providing navigation for future management pages."""

from pathlib import Path

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

from database.connection import DB_NAME
from ui.admin.pages.dashboard_home_page import DashboardHomePage
from ui.admin.pages.faculties_page import FacultiesPage
from ui.admin.pages.professors_page import ProfessorsPage
from ui.admin.pages.rooms_page import RoomsPage
from ui.shared.theme import BACKGROUND_COLOR, PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR


class AdminMainWindow(QMainWindow):
    """Display the navigation shell for the authenticated Admin Panel."""

    _PAGE_DEFINITIONS = (
        ("dashboard_home", "Dashboard Home", "nav_dashboard_home"),
        ("faculties", "Faculties", "nav_faculties"),
        ("professors", "Professors", "nav_professors"),
        ("rooms", "Rooms", "nav_rooms"),
        ("courses", "Courses", "nav_courses"),
        ("events", "Events", "nav_events"),
        ("faq", "FAQ", "nav_faq"),
        ("csv", "CSV Import/Export", "nav_csv"),
        ("logs", "Logs", "nav_logs"),
    )

    def __init__(
        self,
        current_admin: dict,
        db_path: str | Path = DB_NAME,
    ) -> None:
        """Build the dashboard shell for the authenticated administrator."""
        super().__init__()
        self.current_admin = current_admin
        self.db_path = db_path
        self.nav_buttons: dict[str, QPushButton] = {}
        self.setWindowTitle("ECU Robot Admin Panel")
        self.resize(1200, 750)
        self.setMinimumSize(1000, 650)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        """Create the sidebar, header, and placeholder page stack."""
        central_widget = QWidget()
        central_widget.setObjectName("admin_central_widget")
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = self._create_sidebar()
        content_area = self._create_content_area()
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_area, stretch=1)

    def _create_sidebar(self) -> QFrame:
        """Create fixed navigation for all planned Admin Dashboard sections."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 26, 18, 24)
        sidebar_layout.setSpacing(8)

        brand_label = QLabel("ECU ROBOT")
        brand_label.setObjectName("sidebar_brand")
        brand_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label = QLabel("ADMIN PANEL")
        subtitle_label.setObjectName("sidebar_subtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sidebar_layout.addWidget(brand_label)
        sidebar_layout.addWidget(subtitle_label)
        sidebar_layout.addSpacing(24)

        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)

        for index, (key, title, object_name) in enumerate(self._PAGE_DEFINITIONS):
            button = QPushButton(title)
            button.setObjectName(object_name)
            button.setCheckable(True)
            button.setMinimumHeight(44)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, page_index=index: self.page_stack.setCurrentIndex(
                    page_index
                )
            )
            self.nav_button_group.addButton(button, index)
            self.nav_buttons[key] = button
            sidebar_layout.addWidget(button)

        self.nav_buttons["dashboard_home"].setChecked(True)
        sidebar_layout.addStretch()

        footer_label = QLabel("Egyptian Chinese University")
        footer_label.setObjectName("sidebar_footer")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setWordWrap(True)
        sidebar_layout.addWidget(footer_label)
        return sidebar

    def _create_content_area(self) -> QWidget:
        """Create the authenticated header and future page container."""
        content_area = QWidget()
        content_area.setObjectName("content_area")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(30, 24, 30, 30)
        content_layout.setSpacing(22)

        header = QFrame()
        header.setObjectName("dashboard_header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 16, 24, 16)

        title_label = QLabel("Admin Dashboard")
        title_label.setObjectName("dashboard_title")
        admin_name = self.current_admin.get("full_name", "Administrator")
        admin_label = QLabel(f"Logged in as: {admin_name}")
        admin_label.setObjectName("logged_in_admin")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(admin_label)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("page_stack")
        self.dashboard_home_page = DashboardHomePage(self.db_path)
        self.page_stack.addWidget(self.dashboard_home_page)
        self.faculties_page = FacultiesPage(self.db_path)
        self.page_stack.addWidget(self.faculties_page)
        self.professors_page = ProfessorsPage(self.db_path)
        self.page_stack.addWidget(self.professors_page)
        self.rooms_page = RoomsPage(self.db_path)
        self.page_stack.addWidget(self.rooms_page)
        for _, title, _ in self._PAGE_DEFINITIONS[4:]:
            self.page_stack.addWidget(self._create_placeholder_page(title))

        content_layout.addWidget(header)
        content_layout.addWidget(self.page_stack, stretch=1)
        return content_area

    @staticmethod
    def _create_placeholder_page(title: str) -> QWidget:
        """Create one documented placeholder for a future dashboard phase."""
        page = QFrame()
        page.setObjectName("placeholder_page")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(40, 40, 40, 40)
        page_layout.addStretch()

        title_label = QLabel(title)
        title_label.setObjectName("placeholder_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label = QLabel("This page will be implemented in a future phase.")
        message_label.setObjectName("placeholder_message")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        page_layout.addWidget(title_label)
        page_layout.addWidget(message_label)
        page_layout.addStretch()
        return page

    def _apply_styles(self) -> None:
        """Apply the shared ECU palette to the dashboard shell."""
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget#admin_central_widget, QWidget#content_area {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                font-family: "Segoe UI", Arial, sans-serif;
            }}

            QFrame#sidebar {{
                background-color: {PRIMARY_COLOR};
            }}

            QLabel#sidebar_brand {{
                color: #FFFFFF;
                font-size: 23px;
                font-weight: 800;
            }}

            QLabel#sidebar_subtitle {{
                color: {SECONDARY_COLOR};
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 2px;
            }}

            QPushButton {{
                background-color: transparent;
                color: #DCE7F3;
                border: none;
                border-radius: 8px;
                padding: 0 14px;
                text-align: left;
                font-size: 14px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.10);
                color: #FFFFFF;
            }}

            QPushButton:checked {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
            }}

            QLabel#sidebar_footer {{
                color: #AFC2D6;
                font-size: 11px;
            }}

            QFrame#dashboard_header, QFrame#placeholder_page {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }}

            QLabel#dashboard_title {{
                color: {PRIMARY_COLOR};
                font-size: 24px;
                font-weight: 700;
            }}

            QLabel#logged_in_admin {{
                color: #64748B;
                font-size: 13px;
            }}

            QLabel#placeholder_title {{
                color: {PRIMARY_COLOR};
                font-size: 27px;
                font-weight: 700;
            }}

            QLabel#placeholder_message {{
                color: #64748B;
                font-size: 15px;
            }}
            """
        )
