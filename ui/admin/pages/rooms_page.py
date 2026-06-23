"""Read-only Admin Dashboard page for viewing university rooms."""

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.room_csv_controller import export_rooms_to_csv, import_rooms_from_csv
from database.connection import DB_NAME
from database.repositories.room_repository import (
    delete_room,
    get_all_rooms,
    update_room,
)
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
        self.has_unsaved_changes = False
        self.is_loading_table = False
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
            "Manage campus rooms, buildings, floors, categories, and map coordinates"
        )
        subtitle_label.setObjectName("rooms_page_subtitle")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        self.refresh_rooms_button = QPushButton("Refresh")
        self.refresh_rooms_button.setObjectName("refresh_rooms_button")
        self.refresh_rooms_button.setMinimumSize(110, 42)
        self.refresh_rooms_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_rooms_button.clicked.connect(self.load_rooms)
        self.refresh_rooms_button.setHidden(True)

        heading_layout.addLayout(title_layout)
        heading_layout.addStretch()

        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        self.rooms_toolbar_layout = action_layout
        self.upload_rooms_csv_button = QPushButton("Upload CSV")
        self.upload_rooms_csv_button.setObjectName("upload_rooms_csv_button")
        self.delete_room_button = QPushButton("Delete Selected Row")
        self.delete_room_button.setObjectName("delete_room_button")
        self.export_rooms_csv_button = QPushButton("Export CSV")
        self.export_rooms_csv_button.setObjectName("export_rooms_csv_button")
        self.save_rooms_table_button = QPushButton("Save Edits")
        self.save_rooms_table_button.setObjectName("save_rooms_table_button")
        for button in (
            self.upload_rooms_csv_button,
            self.delete_room_button,
            self.export_rooms_csv_button,
            self.save_rooms_table_button,
        ):
            button.setMinimumSize(150, 40)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            action_layout.addWidget(button)
        action_layout.addStretch()

        self.upload_rooms_csv_button.clicked.connect(self.upload_csv)
        self.delete_room_button.clicked.connect(self.delete_selected_room)
        self.export_rooms_csv_button.clicked.connect(self.export_csv)
        self.save_rooms_table_button.clicked.connect(self.save_table_changes)

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
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked
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
        self.rooms_table.itemChanged.connect(self._handle_item_changed)

        header = self.rooms_table.horizontalHeader()
        header.setMinimumSectionSize(75)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for column_index in (1, 3, 6):
            header.setSectionResizeMode(column_index, QHeaderView.ResizeMode.Stretch)

        table_layout.addWidget(self.rooms_status_label)
        table_layout.addWidget(self.rooms_table)
        page_layout.addLayout(heading_layout)
        page_layout.addLayout(action_layout)
        page_layout.addWidget(table_card, stretch=1)

    def load_rooms(self) -> None:
        """Load room rows while keeping database failures non-fatal."""
        self.is_loading_table = True
        try:
            try:
                rooms = get_all_rooms(self.db_path)
            except sqlite3.Error:
                self.rooms_table.setRowCount(0)
                self.has_unsaved_changes = False
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
                        item.setFlags(
                            item.flags() & ~Qt.ItemFlag.ItemIsEditable
                        )
                    self.rooms_table.setItem(row_index, column_index, item)

            self.has_unsaved_changes = False
            self.rooms_status_label.setText(f"{len(rooms)} rooms found")
        finally:
            self.is_loading_table = False

    def _handle_item_changed(self, item: QTableWidgetItem) -> None:
        """Track edits to room business fields outside loading cycles."""
        if self.is_loading_table or item.column() == 0:
            return
        self.has_unsaved_changes = True
        self.rooms_status_label.setText("Unsaved changes")

    def _selected_room_id(self) -> int | None:
        """Return the selected row's stable room identifier when available."""
        selected_rows = self.rooms_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        id_item = self.rooms_table.item(selected_rows[0].row(), 0)
        if id_item is None:
            return None
        room_id = id_item.data(Qt.ItemDataRole.UserRole)
        return int(room_id) if room_id is not None else None

    def upload_csv(self) -> None:
        """Select a CSV and immediately import its valid room rows."""
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Rooms CSV",
            "",
            "CSV Files (*.csv)",
        )
        if not selected_path:
            return

        try:
            summary = import_rooms_from_csv(selected_path, self.db_path)
        except (FileNotFoundError, ValueError, UnicodeError) as error:
            QMessageBox.warning(self, "Room CSV Import", str(error))
            return
        except (OSError, sqlite3.Error) as error:
            QMessageBox.critical(self, "Room CSV Import", str(error))
            return

        self.load_rooms()
        message = (
            f"Created: {summary['created']}\n"
            f"Updated: {summary['updated']}\n"
            f"Skipped: {summary['skipped']}\n"
            f"Errors: {len(summary['errors'])}"
        )
        if summary["errors"]:
            short_errors = "\n".join(summary["errors"][:3])
            if len(summary["errors"]) > 3:
                short_errors += "\nAdditional errors were omitted."
            message += f"\n\n{short_errors}"
        QMessageBox.information(self, "Room CSV Import", message)

    def export_csv(self) -> None:
        """Select a destination and export current room records."""
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Rooms CSV",
            "rooms.csv",
            "CSV Files (*.csv)",
        )
        if not selected_path:
            return

        destination_path = Path(selected_path)
        if destination_path.suffix.lower() != ".csv":
            destination_path = Path(f"{destination_path}.csv")
        try:
            exported_count = export_rooms_to_csv(
                destination_path,
                self.db_path,
            )
        except (OSError, sqlite3.Error, ValueError) as error:
            QMessageBox.critical(self, "Room CSV Export", str(error))
            return
        QMessageBox.information(
            self,
            "Room CSV Export",
            f"Exported {exported_count} rooms successfully.",
        )

    @staticmethod
    def _parse_floor(value: str) -> int:
        """Convert the required floor value to an integer."""
        if not value:
            raise ValueError("Floor is required.")
        try:
            return int(value)
        except ValueError as error:
            raise ValueError("Floor must be an integer.") from error

    @staticmethod
    def _parse_optional_coordinate(value: str, field_name: str) -> float | None:
        """Convert an optional table coordinate to a float."""
        if not value:
            return None
        try:
            return float(value)
        except ValueError as error:
            raise ValueError(f"{field_name} must be numeric.") from error

    def save_table_changes(self) -> None:
        """Validate and persist every inline-edited room row."""
        room_rows: list[tuple[int, dict]] = []
        for row_index in range(self.rooms_table.rowCount()):
            id_item = self.rooms_table.item(row_index, 0)
            room_id = id_item.data(Qt.ItemDataRole.UserRole)
            required_values = {
                "room_name": self.rooms_table.item(row_index, 1).text().strip(),
                "room_number": self.rooms_table.item(row_index, 2).text().strip(),
                "building": self.rooms_table.item(row_index, 3).text().strip(),
                "category": self.rooms_table.item(row_index, 5).text().strip(),
            }
            missing_fields = [
                field_name
                for field_name, value in required_values.items()
                if not value
            ]
            if missing_fields:
                QMessageBox.warning(
                    self,
                    "Invalid Room",
                    "Required room fields cannot be empty: "
                    f"{', '.join(missing_fields)}.",
                )
                return
            try:
                floor = self._parse_floor(
                    self.rooms_table.item(row_index, 4).text().strip()
                )
                x_coord = self._parse_optional_coordinate(
                    self.rooms_table.item(row_index, 7).text().strip(),
                    "X coordinate",
                )
                y_coord = self._parse_optional_coordinate(
                    self.rooms_table.item(row_index, 8).text().strip(),
                    "Y coordinate",
                )
            except ValueError as error:
                QMessageBox.warning(self, "Invalid Room", str(error))
                return

            room_rows.append(
                (
                    int(room_id),
                    {
                        **required_values,
                        "floor": floor,
                        "description": self.rooms_table.item(row_index, 6)
                        .text()
                        .strip(),
                        "x_coord": x_coord,
                        "y_coord": y_coord,
                    },
                )
            )

        try:
            for room_id, room_data in room_rows:
                if not update_room(
                    room_id,
                    db_path=self.db_path,
                    **room_data,
                ):
                    raise ValueError(f"Room record {room_id} could not be updated.")
        except ValueError as error:
            QMessageBox.warning(self, "Room Error", str(error))
            return
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Room Error", str(error))
            return

        self.has_unsaved_changes = False
        self.load_rooms()
        self.rooms_status_label.setText("Changes saved successfully.")

    def delete_selected_room(self) -> None:
        """Confirm and delete the selected room using its internal ID."""
        room_id = self._selected_room_id()
        if room_id is None:
            QMessageBox.warning(
                self,
                "No Room Selected",
                "Please select a room to delete.",
            )
            return

        confirmation = QMessageBox.question(
            self,
            "Delete Room",
            "Are you sure you want to delete the selected room?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            deleted = delete_room(room_id, self.db_path)
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Room Error", str(error))
            return
        if not deleted:
            QMessageBox.warning(
                self,
                "Room Not Found",
                "The selected room could not be deleted.",
            )
            return
        self.load_rooms()
        self.rooms_status_label.setText("Room deleted successfully.")

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

            QPushButton#refresh_rooms_button,
            QPushButton#upload_rooms_csv_button,
            QPushButton#delete_room_button,
            QPushButton#export_rooms_csv_button,
            QPushButton#save_rooms_table_button {{
                background-color: {PRIMARY_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 0 18px;
                font-size: 14px;
                font-weight: 700;
                text-align: center;
            }}

            QPushButton#refresh_rooms_button:hover,
            QPushButton#upload_rooms_csv_button:hover,
            QPushButton#delete_room_button:hover,
            QPushButton#export_rooms_csv_button:hover,
            QPushButton#save_rooms_table_button:hover {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
            }}
            """
        )
