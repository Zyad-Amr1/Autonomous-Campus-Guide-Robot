"""Read-only Admin Dashboard page for viewing university faculties."""

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
from database.repositories.faculty_repository import get_all_faculties
from ui.shared.theme import BACKGROUND_COLOR, PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR


class FacultiesPage(QWidget):
    """Display faculty records in a professional read-only table."""

    _COLUMNS = (
        ("ID", "id"),
        ("Name", "name"),
        ("Description", "description"),
        ("Building", "building"),
        ("Dean Name", "dean_name"),
        ("Created At", "created_at"),
        ("Updated At", "updated_at"),
    )

    def __init__(self, db_path: str | Path = DB_NAME) -> None:
        """Build the faculty table for the selected SQLite database."""
        super().__init__()
        self.db_path = db_path
        self._build_ui()
        self._apply_styles()
        self.load_faculties()

    def _build_ui(self) -> None:
        """Create the page heading, refresh action, status, and table."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(4, 4, 4, 4)
        page_layout.setSpacing(18)

        heading_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title_label = QLabel("Faculties")
        title_label.setObjectName("faculties_page_title")
        subtitle_label = QLabel(
            "View university faculties managed by the ECU Robot system"
        )
        subtitle_label.setObjectName("faculties_page_subtitle")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        self.refresh_faculties_button = QPushButton("Refresh")
        self.refresh_faculties_button.setObjectName("refresh_faculties_button")
        self.refresh_faculties_button.setMinimumSize(110, 42)
        self.refresh_faculties_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_faculties_button.clicked.connect(self.load_faculties)

        heading_layout.addLayout(title_layout)
        heading_layout.addStretch()
        heading_layout.addWidget(self.refresh_faculties_button)

        table_card = QFrame()
        table_card.setObjectName("faculties_table_card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 16, 18, 18)
        table_layout.setSpacing(12)

        self.faculties_status_label = QLabel("0 faculties found")
        self.faculties_status_label.setObjectName("faculties_status_label")

        self.faculties_table = QTableWidget()
        self.faculties_table.setObjectName("faculties_table")
        self.faculties_table.setColumnCount(len(self._COLUMNS))
        self.faculties_table.setHorizontalHeaderLabels(
            [heading for heading, _ in self._COLUMNS]
        )
        self.faculties_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.faculties_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.faculties_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.faculties_table.setAlternatingRowColors(True)
        self.faculties_table.setShowGrid(False)
        self.faculties_table.verticalHeader().setVisible(False)

        header = self.faculties_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        table_layout.addWidget(self.faculties_status_label)
        table_layout.addWidget(self.faculties_table)
        page_layout.addLayout(heading_layout)
        page_layout.addWidget(table_card, stretch=1)

    def load_faculties(self) -> None:
        """Load current faculty rows while keeping database failures non-fatal."""
        try:
            faculties = get_all_faculties(self.db_path)
        except sqlite3.Error:
            self.faculties_table.setRowCount(0)
            self.faculties_status_label.setText(
                "Unable to load faculties due to a database error."
            )
            return

        self.faculties_table.setRowCount(len(faculties))
        for row_index, faculty in enumerate(faculties):
            for column_index, (_, field_name) in enumerate(self._COLUMNS):
                value = faculty[field_name]
                item = QTableWidgetItem("" if value is None else str(value))
                if field_name == "id":
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.faculties_table.setItem(row_index, column_index, item)

        self.faculties_status_label.setText(f"{len(faculties)} faculties found")

    def _apply_styles(self) -> None:
        """Apply dashboard-consistent colors and table presentation."""
        self.setStyleSheet(
            f"""
            FacultiesPage {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                font-family: "Segoe UI", Arial, sans-serif;
            }}

            QLabel#faculties_page_title {{
                color: {PRIMARY_COLOR};
                font-size: 27px;
                font-weight: 700;
            }}

            QLabel#faculties_page_subtitle,
            QLabel#faculties_status_label {{
                color: #64748B;
                font-size: 13px;
            }}

            QFrame#faculties_table_card {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }}

            QTableWidget#faculties_table {{
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

            QPushButton#refresh_faculties_button {{
                background-color: {PRIMARY_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 0 18px;
                font-size: 14px;
                font-weight: 700;
                text-align: center;
            }}

            QPushButton#refresh_faculties_button:hover {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
            }}
            """
        )
