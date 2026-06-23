"""Admin page for CSV-driven university event management."""

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from controllers.event_csv_controller import export_events_to_csv, import_events_from_csv
from database.connection import DB_NAME
from database.repositories.event_repository import delete_event, get_all_events, update_event
from ui.shared.theme import BACKGROUND_COLOR, PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR


class EventsPage(QWidget):
    """Display and edit university event records in a clean table."""

    _COLUMNS = (
        ("No.", None), ("Title", "title"), ("Description", "description"),
        ("Location", "location"), ("Start Date", "start_date"),
        ("End Date", "end_date"), ("Start Time", "start_time"),
        ("End Time", "end_time"),
    )

    def __init__(self, db_path: str | Path = DB_NAME) -> None:
        """Build the Events page for the selected database."""
        super().__init__()
        self.setObjectName("events_page")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.db_path = db_path
        self.is_loading_table = False
        self._build_ui()
        self._apply_styles()
        self.load_events()

    def _build_ui(self) -> None:
        """Create the heading, standard toolbar, status, and event table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(18)
        heading = QVBoxLayout()
        title = QLabel("Events")
        title.setObjectName("events_page_title")
        subtitle = QLabel("Manage university events, deadlines, and campus activities")
        subtitle.setObjectName("events_page_subtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        toolbar = QHBoxLayout()
        self.events_toolbar_layout = toolbar
        self.upload_events_csv_button = QPushButton("Upload CSV")
        self.upload_events_csv_button.setObjectName("upload_events_csv_button")
        self.delete_event_button = QPushButton("Delete Selected Row")
        self.delete_event_button.setObjectName("delete_event_button")
        self.export_events_csv_button = QPushButton("Export CSV")
        self.export_events_csv_button.setObjectName("export_events_csv_button")
        self.save_events_table_button = QPushButton("Save Edits")
        self.save_events_table_button.setObjectName("save_events_table_button")
        for button in (self.upload_events_csv_button, self.delete_event_button, self.export_events_csv_button, self.save_events_table_button):
            button.setMinimumSize(150, 40)
            toolbar.addWidget(button)
        toolbar.addStretch()
        self.upload_events_csv_button.clicked.connect(self.upload_csv)
        self.delete_event_button.clicked.connect(self.delete_selected_event)
        self.export_events_csv_button.clicked.connect(self.export_csv)
        self.save_events_table_button.clicked.connect(self.save_table_changes)
        card = QFrame()
        card.setObjectName("events_table_card")
        card_layout = QVBoxLayout(card)
        self.events_status_label = QLabel("0 events found")
        self.events_status_label.setObjectName("events_status_label")
        self.events_table = QTableWidget()
        self.events_table.setObjectName("events_table")
        self.events_table.setColumnCount(len(self._COLUMNS))
        self.events_table.setHorizontalHeaderLabels([label for label, _ in self._COLUMNS])
        self.events_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed | QAbstractItemView.EditTrigger.SelectedClicked)
        self.events_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.events_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.events_table.setAlternatingRowColors(True)
        self.events_table.setShowGrid(False)
        self.events_table.verticalHeader().setVisible(False)
        self.events_table.itemChanged.connect(self._item_changed)
        header = self.events_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for column in (1, 2, 3):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        card_layout.addWidget(self.events_status_label)
        card_layout.addWidget(self.events_table)
        layout.addLayout(heading)
        layout.addLayout(toolbar)
        layout.addWidget(card, stretch=1)

    def load_events(self) -> None:
        """Load event rows with sequential numbers and internal IDs."""
        self.is_loading_table = True
        try:
            try:
                events = get_all_events(self.db_path)
            except sqlite3.Error:
                self.events_table.setRowCount(0)
                self.events_status_label.setText("Unable to load events due to a database error.")
                return
            self.events_table.setRowCount(len(events))
            for row, event in enumerate(events):
                for column, (_, field) in enumerate(self._COLUMNS):
                    value = row + 1 if field is None else event[field]
                    item = QTableWidgetItem("" if value is None else str(value))
                    if column == 0:
                        item.setData(Qt.ItemDataRole.UserRole, event["id"])
                        item.setFlags(
                            Qt.ItemFlag.ItemIsEnabled
                            | Qt.ItemFlag.ItemIsSelectable
                        )
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    else:
                        item.setFlags(
                            Qt.ItemFlag.ItemIsEnabled
                            | Qt.ItemFlag.ItemIsSelectable
                            | Qt.ItemFlag.ItemIsEditable
                        )
                    self.events_table.setItem(row, column, item)
            self.events_status_label.setText(f"{len(events)} events found")
        finally:
            self.is_loading_table = False

    def _item_changed(self, item: QTableWidgetItem) -> None:
        if not self.is_loading_table and item.column() > 0:
            self.events_status_label.setText("Unsaved changes")

    def _selected_id(self) -> int | None:
        rows = self.events_table.selectionModel().selectedRows()
        if not rows:
            return None
        value = self.events_table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return int(value) if value is not None else None

    def upload_csv(self) -> None:
        """Select and automatically import an event CSV."""
        path, _ = QFileDialog.getOpenFileName(self, "Import Events CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            summary = import_events_from_csv(path, self.db_path)
        except (FileNotFoundError, ValueError, UnicodeError) as error:
            QMessageBox.warning(self, "Event CSV Import", str(error)); return
        except (OSError, sqlite3.Error) as error:
            QMessageBox.critical(self, "Event CSV Import", str(error)); return
        self.load_events()
        message = f"Created: {summary['created']}\nUpdated: {summary['updated']}\nSkipped: {summary['skipped']}\nErrors: {len(summary['errors'])}"
        if summary["errors"]:
            message += "\n\n" + "\n".join(summary["errors"][:3])
        QMessageBox.information(self, "Event CSV Import", message)

    def export_csv(self) -> None:
        """Export current events to CSV."""
        path, _ = QFileDialog.getSaveFileName(self, "Export Events CSV", "events.csv", "CSV Files (*.csv)")
        if not path:
            return
        destination = Path(path)
        if destination.suffix.lower() != ".csv":
            destination = Path(f"{destination}.csv")
        try:
            count = export_events_to_csv(destination, self.db_path)
        except (OSError, sqlite3.Error, ValueError) as error:
            QMessageBox.critical(self, "Event CSV Export", str(error)); return
        QMessageBox.information(self, "Event CSV Export", f"Exported {count} events successfully.")

    def save_table_changes(self) -> None:
        """Validate required event fields and persist table edits."""
        rows = []
        for row in range(self.events_table.rowCount()):
            data = {
                "title": self.events_table.item(row, 1).text().strip(),
                "description": self.events_table.item(row, 2).text().strip(),
                "location": self.events_table.item(row, 3).text().strip(),
                "start_date": self.events_table.item(row, 4).text().strip(),
                "end_date": self.events_table.item(row, 5).text().strip(),
                "start_time": self.events_table.item(row, 6).text().strip(),
                "end_time": self.events_table.item(row, 7).text().strip(),
            }
            if not data["title"] or not data["start_date"]:
                QMessageBox.warning(self, "Invalid Event", "Title and start date are required."); return
            event_id = self.events_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            rows.append((int(event_id), data))
        try:
            for event_id, data in rows:
                if not update_event(event_id, db_path=self.db_path, **data):
                    raise ValueError(f"Event record {event_id} could not be updated.")
        except ValueError as error:
            QMessageBox.warning(self, "Event Error", str(error)); return
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Event Error", str(error)); return
        self.load_events()
        self.events_status_label.setText("Changes saved successfully.")

    def delete_selected_event(self) -> None:
        """Confirm and delete the selected event."""
        event_id = self._selected_id()
        if event_id is None:
            QMessageBox.warning(self, "No Event Selected", "Please select an event to delete."); return
        answer = QMessageBox.question(self, "Delete Event", "Are you sure you want to delete the selected event?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            deleted = delete_event(event_id, self.db_path)
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Event Error", str(error)); return
        if not deleted:
            QMessageBox.warning(self, "Event Not Found", "The selected event could not be deleted."); return
        self.load_events()
        self.events_status_label.setText("Event deleted successfully.")

    def _apply_styles(self) -> None:
        self.setStyleSheet(f"""
            QWidget#events_page {{ background-color: {BACKGROUND_COLOR}; color: {TEXT_COLOR}; font-family: "Segoe UI"; }}
            QLabel#events_page_title {{ color: {PRIMARY_COLOR}; font-size: 27px; font-weight: 700; }}
            QLabel#events_page_subtitle, QLabel#events_status_label {{ color: #64748B; }}
            QFrame#events_table_card {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }}
            QTableWidget#events_table {{ background-color: #FFFFFF; alternate-background-color: #F8FAFC; color: #0F172A; gridline-color: #E2E8F0; border: 1px solid #E2E8F0; selection-background-color: #DBEAFE; selection-color: #0F172A; }}
            QTableWidget#events_table::item {{ color: #0F172A; }}
            QTableWidget#events_table::item:selected {{ background-color: #DBEAFE; color: #0F172A; }}
            QHeaderView::section {{ background: {PRIMARY_COLOR}; color: #FFFFFF; border: none; padding: 10px; font-weight: 700; }}
            QPushButton {{ background: {PRIMARY_COLOR}; color: #FFFFFF; border: none; border-radius: 8px; padding: 0 18px; font-weight: 700; }}
            QPushButton:hover {{ background: {SECONDARY_COLOR}; color: {TEXT_COLOR}; }}
        """)
