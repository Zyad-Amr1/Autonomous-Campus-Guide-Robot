"""Read-only Admin Dashboard page for viewing university professors."""

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.connection import DB_NAME
from database.repositories.professor_repository import get_all_professors
from ui.shared.theme import BACKGROUND_COLOR, PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR


class ProfessorsPage(QWidget):
    """Display professor records and their joined academic/location details."""

    _COLUMNS = (
        ("ID", "id"),
        ("Full Name", "full_name"),
        ("Title", "title"),
        ("Faculty", "faculty_name"),
        ("Office Room", "office_room_name"),
        ("Email", "email"),
        ("Phone", "phone"),
        ("Office Hours", "office_hours"),
        ("Photo Path", "photo_path"),
        ("Bio", "bio"),
        ("Created At", "created_at"),
        ("Updated At", "updated_at"),
    )

    def __init__(self, db_path: str | Path = DB_NAME) -> None:
        """Build the professor table for the selected SQLite database."""
        super().__init__()
        self.db_path = db_path
        self._build_ui()
        self._apply_styles()
        self.load_professors()

    def _build_ui(self) -> None:
        """Create the page heading, refresh action, status, and table."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(4, 4, 4, 4)
        page_layout.setSpacing(18)

        heading_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title_label = QLabel("Professors")
        title_label.setObjectName("professors_page_title")
        subtitle_label = QLabel(
            "View university professors and academic staff managed by the ECU Robot system"
        )
        subtitle_label.setObjectName("professors_page_subtitle")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        self.refresh_professors_button = QPushButton("Refresh")
        self.refresh_professors_button.setObjectName("refresh_professors_button")
        self.refresh_professors_button.setMinimumSize(110, 42)
        self.refresh_professors_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_professors_button.clicked.connect(self.load_professors)

        heading_layout.addLayout(title_layout)
        heading_layout.addStretch()
        heading_layout.addWidget(self.refresh_professors_button)

        table_card = QFrame()
        table_card.setObjectName("professors_table_card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 16, 18, 18)
        table_layout.setSpacing(12)

        self.professors_status_label = QLabel("0 professors found")
        self.professors_status_label.setObjectName("professors_status_label")

        self.professors_table = QTableWidget()
        self.professors_table.setObjectName("professors_table")
        self.professors_table.setColumnCount(len(self._COLUMNS))
        self.professors_table.setHorizontalHeaderLabels(
            [heading for heading, _ in self._COLUMNS]
        )
        self.professors_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.professors_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.professors_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.professors_table.setAlternatingRowColors(True)
        self.professors_table.setShowGrid(False)
        self.professors_table.setWordWrap(False)
        self.professors_table.verticalHeader().setVisible(False)

        header = self.professors_table.horizontalHeader()
        header.setMinimumSectionSize(80)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for column_index in (1, 3, 4, 7, 9):
            header.setSectionResizeMode(column_index, QHeaderView.ResizeMode.Stretch)

        table_layout.addWidget(self.professors_status_label)
        table_layout.addWidget(self.professors_table)
        page_layout.addLayout(heading_layout)
        page_layout.addWidget(table_card, stretch=1)

    def load_professors(self) -> None:
        """Load current professors while keeping database failures non-fatal."""
        try:
            professors = get_all_professors(self.db_path)
        except sqlite3.Error:
            self.professors_table.setRowCount(0)
            self.professors_status_label.setText(
                "Unable to load professors due to a database error."
            )
            return

        self.professors_table.setRowCount(len(professors))
        for row_index, professor in enumerate(professors):
            for column_index, (_, field_name) in enumerate(self._COLUMNS):
                value = professor[field_name]
                item = QTableWidgetItem("" if value is None else str(value))
                if field_name == "id":
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.professors_table.setItem(row_index, column_index, item)

        self.professors_status_label.setText(
            f"{len(professors)} professors found"
        )

    def _apply_styles(self) -> None:
        """Apply dashboard-consistent colors and table presentation."""
        self.setStyleSheet(
            f"""
            ProfessorsPage {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                font-family: "Segoe UI", Arial, sans-serif;
            }}

            QLabel#professors_page_title {{
                color: {PRIMARY_COLOR};
                font-size: 27px;
                font-weight: 700;
            }}

            QLabel#professors_page_subtitle,
            QLabel#professors_status_label {{
                color: #64748B;
                font-size: 13px;
            }}

            QFrame#professors_table_card {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }}

            QTableWidget#professors_table {{
                background-color: #FFFFFF;
                alternate-background-color: #F8FAFC;
                color: {TEXT_COLOR};
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                selection-background-color: #DCE8F5;
                selection-color: {TEXT_COLOR};
            }}

            QHeaderView::section {{
                background-color: {PRIMARY_COLOR};
                color: #FFFFFF;
                border: none;
                padding: 10px 8px;
                font-size: 12px;
                font-weight: 700;
            }}

            QPushButton#refresh_professors_button {{
                background-color: {PRIMARY_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 0 18px;
                font-size: 14px;
                font-weight: 700;
                text-align: center;
            }}

            QPushButton#refresh_professors_button:hover {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
            }}
            """
        )
