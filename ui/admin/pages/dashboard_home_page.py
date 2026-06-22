"""Live summary-card page for the ECU Robot Admin Dashboard."""

import sqlite3
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database.connection import DB_NAME
from database.repositories.course_repository import count_courses
from database.repositories.event_repository import count_events
from database.repositories.faculty_repository import count_faculties
from database.repositories.faq_repository import count_faqs
from database.repositories.log_repository import count_logs
from database.repositories.professor_repository import count_professors
from database.repositories.room_repository import count_rooms
from ui.shared.theme import BACKGROUND_COLOR, PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR


class DashboardHomePage(QWidget):
    """Display live database totals for the main administration domains."""

    _CARD_DEFINITIONS = (
        (
            "Faculties",
            "Academic faculties registered in the system",
            "count_faculties_label",
            count_faculties,
        ),
        (
            "Professors",
            "Faculty members available to students",
            "count_professors_label",
            count_professors,
        ),
        (
            "Rooms",
            "Campus rooms and navigation destinations",
            "count_rooms_label",
            count_rooms,
        ),
        (
            "Courses",
            "Course schedules available to the assistant",
            "count_courses_label",
            count_courses,
        ),
        (
            "Events",
            "University events and announcements",
            "count_events_label",
            count_events,
        ),
        (
            "FAQs",
            "Common questions available for matching",
            "count_faqs_label",
            count_faqs,
        ),
        (
            "Visitor Logs",
            "Recorded Public Assistant interactions",
            "count_logs_label",
            count_logs,
        ),
    )

    def __init__(self, db_path: str | Path = DB_NAME) -> None:
        """Build the summary-card page for the selected database."""
        super().__init__()
        self.db_path = db_path
        self._count_sources: list[tuple[QLabel, Callable]] = []
        self._build_ui()
        self._apply_styles()
        self.refresh_counts()

    def _build_ui(self) -> None:
        """Create the page heading, refresh action, and summary-card grid."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(4, 4, 4, 4)
        page_layout.setSpacing(24)

        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title_label = QLabel("Dashboard Home")
        title_label.setObjectName("dashboard_home_title")
        subtitle_label = QLabel("Overview of ECU Robot system data")
        subtitle_label.setObjectName("dashboard_home_subtitle")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        self.refresh_dashboard_button = QPushButton("Refresh")
        self.refresh_dashboard_button.setObjectName("refresh_dashboard_button")
        self.refresh_dashboard_button.setMinimumSize(110, 42)
        self.refresh_dashboard_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_dashboard_button.clicked.connect(self.refresh_counts)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_dashboard_button)

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(18)
        cards_layout.setVerticalSpacing(18)

        for index, (title, description, object_name, counter) in enumerate(
            self._CARD_DEFINITIONS
        ):
            card, count_label = self._create_summary_card(
                title,
                description,
                object_name,
            )
            setattr(self, object_name, count_label)
            self._count_sources.append((count_label, counter))
            cards_layout.addWidget(card, index // 3, index % 3)

        page_layout.addLayout(header_layout)
        page_layout.addLayout(cards_layout)
        page_layout.addStretch()

    @staticmethod
    def _create_summary_card(
        title: str,
        description: str,
        count_object_name: str,
    ) -> tuple[QFrame, QLabel]:
        """Create one professional count card and return its value label."""
        card = QFrame()
        card.setObjectName("summary_card")
        card.setMinimumSize(220, 150)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("summary_card_title")
        count_label = QLabel("0")
        count_label.setObjectName(count_object_name)
        count_label.setProperty("role", "summary_count")
        description_label = QLabel(description)
        description_label.setObjectName("summary_card_description")
        description_label.setWordWrap(True)

        card_layout.addWidget(title_label)
        card_layout.addWidget(count_label)
        card_layout.addWidget(description_label)
        return card, count_label

    def refresh_counts(self) -> None:
        """Refresh each live total independently so one database error stays local."""
        for count_label, count_function in self._count_sources:
            try:
                count_value = count_function(self.db_path)
            except sqlite3.Error:
                count_value = 0
            count_label.setText(str(count_value))

    def _apply_styles(self) -> None:
        """Apply the shared ECU palette to the modern summary-card layout."""
        self.setStyleSheet(
            f"""
            DashboardHomePage {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                font-family: "Segoe UI", Arial, sans-serif;
            }}

            QLabel#dashboard_home_title {{
                color: {PRIMARY_COLOR};
                font-size: 27px;
                font-weight: 700;
            }}

            QLabel#dashboard_home_subtitle {{
                color: #64748B;
                font-size: 14px;
            }}

            QFrame#summary_card {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }}

            QLabel#summary_card_title {{
                color: {PRIMARY_COLOR};
                font-size: 15px;
                font-weight: 700;
            }}

            QLabel[role="summary_count"] {{
                color: {SECONDARY_COLOR};
                font-size: 34px;
                font-weight: 800;
            }}

            QLabel#summary_card_description {{
                color: #64748B;
                font-size: 12px;
            }}

            QPushButton#refresh_dashboard_button {{
                background-color: {PRIMARY_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 0 18px;
                font-size: 14px;
                font-weight: 700;
                text-align: center;
            }}

            QPushButton#refresh_dashboard_button:hover {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
            }}
            """
        )
