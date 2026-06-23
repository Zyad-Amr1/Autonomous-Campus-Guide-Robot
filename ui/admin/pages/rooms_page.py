"""Read-only Admin Dashboard page for viewing university rooms."""

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
from database.repositories.room_repository import get_all_rooms
from ui.shared.theme import BACKGROUND_COLOR, PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR


class RoomsPage(QWidget):
    """Display campus room and map-coordinate records in a read-only table."""

    _COLUMNS = (
        ("No.", None),
        ("Room Name", "room_name"),
        ("Room Number", "room_number"),
        ("Building", "building"),
        ("Floor", "floor"),
        ("Category", "category"),
        ("Description", "description"),
        ("X Coord", "x_coord"),
        ("Y Coord", "y_coord"),
    )

    def __init__(self, db_path: str | Path = DB_NAME) -> None:
        """Build the rooms table for the selected SQLite database."""
        super().__init__()
        self.db_path = db_path
        self._build_ui()
        self._apply_styles()
        self.load_rooms()

    def _build_ui(self) -> None:
        """Create the page heading, refresh action, status, and rooms table."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(4, 4, 4, 4)
        page_layout.setSpacing(18)

        heading_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title_label = QLabel("Rooms")
        title_label.setObjectName("rooms_page_title")
        subtitle_label = QLabel(
            "View campus rooms, buildings, floors, and map coordinates"
        )
        subtitle_label.setObjectName("rooms_page_subtitle")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        self.refresh_rooms_button = QPushButton("Refresh")
        self.refresh_rooms_button.setObjectName("refresh_rooms_button")
        self.refresh_rooms_button.setMinimumSize(110, 42)
        self.refresh_rooms_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_rooms_button.clicked.connect(self.load_rooms)

        heading_layout.addLayout(title_layout)
        heading_layout.addStretch()
        heading_layout.addWidget(self.refresh_rooms_button)

        table_card = QFrame()
        table_card.setObjectName("rooms_table_card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 16, 18, 18)
        table_layout.setSpacing(12)

        self.rooms_status_label = QLabel("0 rooms found")
        self.rooms_status_label.setObjectName("rooms_status_label")

        self.rooms_table = QTableWidget()
        self.rooms_table.setObjectName("rooms_table")
        self.rooms_table.setColumnCount(len(self._COLUMNS))
        self.rooms_table.setHorizontalHeaderLabels(
            [heading for heading, _ in self._COLUMNS]
        )
        self.rooms_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.rooms_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.rooms_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.rooms_table.setAlternatingRowColors(True)
        self.rooms_table.setShowGrid(False)
        self.rooms_table.setWordWrap(False)
        self.rooms_table.verticalHeader().setVisible(False)

        header = self.rooms_table.horizontalHeader()
        header.setMinimumSectionSize(75)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for column_index in (1, 3, 6):
            header.setSectionResizeMode(column_index, QHeaderView.ResizeMode.Stretch)

        table_layout.addWidget(self.rooms_status_label)
        table_layout.addWidget(self.rooms_table)
        page_layout.addLayout(heading_layout)
        page_layout.addWidget(table_card, stretch=1)

    def load_rooms(self) -> None:
        """Load room rows while keeping database failures non-fatal."""
        try:
            rooms = get_all_rooms(self.db_path)
        except sqlite3.Error:
            self.rooms_table.setRowCount(0)
            self.rooms_status_label.setText(
                "Unable to load rooms due to a database error."
            )
            return

        self.rooms_table.setRowCount(len(rooms))
        for row_index, room in enumerate(rooms):
            for column_index, (_, field_name) in enumerate(self._COLUMNS):
                value = row_index + 1 if field_name is None else room[field_name]
                item = QTableWidgetItem("" if value is None else str(value))
                if column_index == 0:
                    item.setData(Qt.ItemDataRole.UserRole, room["id"])
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.rooms_table.setItem(row_index, column_index, item)

        self.rooms_status_label.setText(f"{len(rooms)} rooms found")

    def _apply_styles(self) -> None:
        """Apply dashboard-consistent colors and table presentation."""
        self.setStyleSheet(
            f"""
            RoomsPage {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                font-family: "Segoe UI", Arial, sans-serif;
            }}

            QLabel#rooms_page_title {{
                color: {PRIMARY_COLOR};
                font-size: 27px;
                font-weight: 700;
            }}

            QLabel#rooms_page_subtitle,
            QLabel#rooms_status_label {{
                color: #64748B;
                font-size: 13px;
            }}

            QFrame#rooms_table_card {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }}

            QTableWidget#rooms_table {{
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

            QPushButton#refresh_rooms_button {{
                background-color: {PRIMARY_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 0 18px;
                font-size: 14px;
                font-weight: 700;
                text-align: center;
            }}

            QPushButton#refresh_rooms_button:hover {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
            }}
            """
        )
