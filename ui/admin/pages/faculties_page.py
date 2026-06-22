"""Admin Dashboard page for viewing and managing university faculties."""

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.connection import DB_NAME
from database.repositories.faculty_repository import (
    create_faculty,
    delete_faculty,
    get_all_faculties,
    get_faculty_by_id,
    update_faculty,
)
from ui.shared.theme import BACKGROUND_COLOR, PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR


class FacultyFormDialog(QDialog):
    """Collect and validate faculty data for add and edit operations."""

    def __init__(
        self,
        parent: QWidget | None = None,
        faculty_data: dict | None = None,
    ) -> None:
        """Build an empty form or pre-fill it with an existing faculty."""
        super().__init__(parent)
        self.setWindowTitle("Edit Faculty" if faculty_data else "Add Faculty")
        self.setModal(True)
        self.setMinimumWidth(480)
        self._build_ui()
        self._apply_styles()

        if faculty_data:
            self._populate_form(faculty_data)

    def _build_ui(self) -> None:
        """Create labeled form fields and explicit save/cancel actions."""
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(28, 26, 28, 24)
        dialog_layout.setSpacing(20)

        title_label = QLabel(self.windowTitle())
        title_label.setObjectName("faculty_form_title")

        form_layout = QFormLayout()
        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(14)

        self.faculty_name_input = QLineEdit()
        self.faculty_name_input.setObjectName("faculty_name_input")
        self.faculty_name_input.setPlaceholderText("Faculty name")

        self.faculty_description_input = QTextEdit()
        self.faculty_description_input.setObjectName("faculty_description_input")
        self.faculty_description_input.setPlaceholderText("Faculty description")
        self.faculty_description_input.setMaximumHeight(100)

        self.faculty_building_input = QLineEdit()
        self.faculty_building_input.setObjectName("faculty_building_input")
        self.faculty_building_input.setPlaceholderText("Building")

        self.faculty_dean_name_input = QLineEdit()
        self.faculty_dean_name_input.setObjectName("faculty_dean_name_input")
        self.faculty_dean_name_input.setPlaceholderText("Dean name")

        form_layout.addRow("Name *", self.faculty_name_input)
        form_layout.addRow("Description", self.faculty_description_input)
        form_layout.addRow("Building", self.faculty_building_input)
        form_layout.addRow("Dean Name", self.faculty_dean_name_input)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_faculty_button = QPushButton("Cancel")
        self.cancel_faculty_button.setObjectName("cancel_faculty_button")
        self.save_faculty_button = QPushButton("Save")
        self.save_faculty_button.setObjectName("save_faculty_button")
        self.cancel_faculty_button.clicked.connect(self.reject)
        self.save_faculty_button.clicked.connect(self._validate_and_accept)
        button_layout.addWidget(self.cancel_faculty_button)
        button_layout.addWidget(self.save_faculty_button)

        dialog_layout.addWidget(title_label)
        dialog_layout.addLayout(form_layout)
        dialog_layout.addLayout(button_layout)

    def _populate_form(self, faculty_data: dict) -> None:
        """Populate controls with values from the selected faculty record."""
        self.faculty_name_input.setText(faculty_data.get("name") or "")
        self.faculty_description_input.setPlainText(
            faculty_data.get("description") or ""
        )
        self.faculty_building_input.setText(faculty_data.get("building") or "")
        self.faculty_dean_name_input.setText(
            faculty_data.get("dean_name") or ""
        )

    def get_form_data(self) -> dict:
        """Return normalized values ready for the faculty repository."""
        return {
            "name": self.faculty_name_input.text().strip(),
            "description": self.faculty_description_input.toPlainText().strip(),
            "building": self.faculty_building_input.text().strip(),
            "dean_name": self.faculty_dean_name_input.text().strip(),
        }

    def _validate_and_accept(self) -> None:
        """Accept the dialog only when its required faculty name is present."""
        if not self.faculty_name_input.text().strip():
            QMessageBox.warning(
                self,
                "Invalid Faculty",
                "Faculty name is required.",
            )
            return
        self.accept()

    def _apply_styles(self) -> None:
        """Style the form consistently with the Admin Dashboard."""
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: #FFFFFF;
                color: {TEXT_COLOR};
                font-family: "Segoe UI", Arial, sans-serif;
            }}

            QLabel#faculty_form_title {{
                color: {PRIMARY_COLOR};
                font-size: 23px;
                font-weight: 700;
            }}

            QLineEdit, QTextEdit {{
                border: 1px solid #CBD5E1;
                border-radius: 7px;
                padding: 8px;
                font-size: 14px;
            }}

            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {PRIMARY_COLOR};
            }}

            QPushButton {{
                min-width: 90px;
                min-height: 38px;
                border-radius: 7px;
                font-weight: 700;
            }}

            QPushButton#save_faculty_button {{
                background-color: {PRIMARY_COLOR};
                color: #FFFFFF;
                border: none;
            }}

            QPushButton#cancel_faculty_button {{
                background-color: #E2E8F0;
                color: {TEXT_COLOR};
                border: none;
            }}
            """
        )


class FacultiesPage(QWidget):
    """Display and manage faculty records through a read-only table."""

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
        self.has_unsaved_changes = False
        self.is_loading_table = False
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

        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        self.add_faculty_button = QPushButton("Add Faculty")
        self.add_faculty_button.setObjectName("add_faculty_button")
        self.edit_faculty_button = QPushButton("Edit Selected")
        self.edit_faculty_button.setObjectName("edit_faculty_button")
        self.delete_faculty_button = QPushButton("Delete Selected")
        self.delete_faculty_button.setObjectName("delete_faculty_button")
        self.save_faculties_table_button = QPushButton("Save Table Changes")
        self.save_faculties_table_button.setObjectName(
            "save_faculties_table_button"
        )
        self.revert_faculties_table_button = QPushButton("Revert Changes")
        self.revert_faculties_table_button.setObjectName(
            "revert_faculties_table_button"
        )

        for button in (
            self.add_faculty_button,
            self.edit_faculty_button,
            self.delete_faculty_button,
            self.save_faculties_table_button,
            self.revert_faculties_table_button,
        ):
            button.setMinimumHeight(40)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.add_faculty_button.clicked.connect(self.add_faculty)
        self.edit_faculty_button.clicked.connect(self.edit_selected_faculty)
        self.delete_faculty_button.clicked.connect(self.delete_selected_faculty)
        self.save_faculties_table_button.clicked.connect(self.save_table_changes)
        self.revert_faculties_table_button.clicked.connect(
            self.revert_table_changes
        )
        action_layout.addWidget(self.add_faculty_button)
        action_layout.addWidget(self.edit_faculty_button)
        action_layout.addWidget(self.delete_faculty_button)
        action_layout.addStretch()
        action_layout.addWidget(self.revert_faculties_table_button)
        action_layout.addWidget(self.save_faculties_table_button)

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
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked
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
        self.faculties_table.itemChanged.connect(self._handle_item_changed)

        header = self.faculties_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        table_layout.addWidget(self.faculties_status_label)
        table_layout.addWidget(self.faculties_table)
        page_layout.addLayout(heading_layout)
        page_layout.addLayout(action_layout)
        page_layout.addWidget(table_card, stretch=1)

    def load_faculties(self) -> None:
        """Load current faculty rows while keeping database failures non-fatal."""
        self.is_loading_table = True
        try:
            try:
                faculties = get_all_faculties(self.db_path)
            except sqlite3.Error:
                self.faculties_table.setRowCount(0)
                self.has_unsaved_changes = False
                self.faculties_status_label.setText(
                    "Unable to load faculties due to a database error."
                )
                return

            self.faculties_table.setRowCount(len(faculties))
            for row_index, faculty in enumerate(faculties):
                for column_index, (_, field_name) in enumerate(self._COLUMNS):
                    value = faculty[field_name]
                    item = QTableWidgetItem("" if value is None else str(value))
                    if column_index in (0, 5, 6):
                        item.setFlags(
                            item.flags() & ~Qt.ItemFlag.ItemIsEditable
                        )
                    if field_name == "id":
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.faculties_table.setItem(row_index, column_index, item)

            self.has_unsaved_changes = False
            self.faculties_status_label.setText(
                f"{len(faculties)} faculties found"
            )
        finally:
            self.is_loading_table = False

    def _handle_item_changed(self, item: QTableWidgetItem) -> None:
        """Track edits only for business columns outside table-loading cycles."""
        if self.is_loading_table or item.column() not in (1, 2, 3, 4):
            return
        self.has_unsaved_changes = True
        self.faculties_status_label.setText("Unsaved changes")

    def save_table_changes(self) -> None:
        """Validate and persist every inline-edited faculty business row."""
        faculty_rows: list[tuple[int, dict]] = []
        for row_index in range(self.faculties_table.rowCount()):
            faculty_id = int(self.faculties_table.item(row_index, 0).text())
            form_data = {
                "name": self.faculties_table.item(row_index, 1).text().strip(),
                "description": self.faculties_table.item(row_index, 2)
                .text()
                .strip(),
                "building": self.faculties_table.item(row_index, 3).text().strip(),
                "dean_name": self.faculties_table.item(row_index, 4).text().strip(),
            }
            if not form_data["name"]:
                QMessageBox.warning(
                    self,
                    "Invalid Faculty",
                    "Faculty name cannot be empty.",
                )
                return
            faculty_rows.append((faculty_id, form_data))

        try:
            for faculty_id, form_data in faculty_rows:
                if not update_faculty(
                    faculty_id,
                    db_path=self.db_path,
                    **form_data,
                ):
                    raise ValueError(
                        f"Faculty record {faculty_id} could not be updated."
                    )
        except ValueError as error:
            QMessageBox.warning(self, "Faculty Error", str(error))
            return
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Faculty Error", str(error))
            return

        self.has_unsaved_changes = False
        self.load_faculties()
        self.faculties_status_label.setText("Changes saved successfully.")

    def revert_table_changes(self) -> None:
        """Discard inline edits and restore the latest repository values."""
        self.load_faculties()
        self.has_unsaved_changes = False
        self.faculties_status_label.setText("Changes reverted.")

    def _selected_faculty_id(self) -> int | None:
        """Return the selected row's stable faculty identifier when available."""
        selected_rows = self.faculties_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        id_item = self.faculties_table.item(selected_rows[0].row(), 0)
        return int(id_item.text()) if id_item is not None else None

    def add_faculty(self) -> None:
        """Open the faculty form and create a record when it is accepted."""
        dialog = FacultyFormDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            create_faculty(db_path=self.db_path, **dialog.get_form_data())
        except (ValueError, sqlite3.Error) as error:
            QMessageBox.critical(self, "Faculty Error", str(error))
            return
        self.load_faculties()

    def edit_selected_faculty(self) -> None:
        """Edit the currently selected faculty through a pre-filled form."""
        faculty_id = self._selected_faculty_id()
        if faculty_id is None:
            QMessageBox.warning(
                self,
                "No Faculty Selected",
                "Please select a faculty to edit.",
            )
            return

        try:
            faculty = get_faculty_by_id(faculty_id, self.db_path)
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Faculty Error", str(error))
            return
        if faculty is None:
            QMessageBox.warning(
                self,
                "Faculty Not Found",
                "The selected faculty could not be found.",
            )
            return

        faculty_data = {key: faculty[key] for key in faculty.keys()}
        dialog = FacultyFormDialog(self, faculty_data)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            updated = update_faculty(
                faculty_id,
                db_path=self.db_path,
                **dialog.get_form_data(),
            )
        except (ValueError, sqlite3.Error) as error:
            QMessageBox.critical(self, "Faculty Error", str(error))
            return
        if not updated:
            QMessageBox.warning(
                self,
                "Faculty Not Updated",
                "The selected faculty could not be updated.",
            )
            return
        self.load_faculties()

    def delete_selected_faculty(self) -> None:
        """Confirm and delete the currently selected faculty record."""
        faculty_id = self._selected_faculty_id()
        if faculty_id is None:
            QMessageBox.warning(
                self,
                "No Faculty Selected",
                "Please select a faculty to delete.",
            )
            return

        confirmation = QMessageBox.question(
            self,
            "Delete Faculty",
            "Are you sure you want to delete the selected faculty?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            deleted = delete_faculty(faculty_id, self.db_path)
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Faculty Error", str(error))
            return
        if not deleted:
            QMessageBox.warning(
                self,
                "Faculty Not Deleted",
                "The selected faculty could not be deleted.",
            )
            return
        self.load_faculties()

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

            QPushButton#refresh_faculties_button,
            QPushButton#add_faculty_button,
            QPushButton#edit_faculty_button,
            QPushButton#delete_faculty_button,
            QPushButton#save_faculties_table_button,
            QPushButton#revert_faculties_table_button {{
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

            QPushButton#edit_faculty_button {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
            }}

            QPushButton#save_faculties_table_button {{
                background-color: #047857;
            }}

            QPushButton#revert_faculties_table_button {{
                background-color: #64748B;
            }}

            QPushButton#delete_faculty_button {{
                background-color: #B91C1C;
            }}

            QPushButton#add_faculty_button:hover,
            QPushButton#edit_faculty_button:hover {{
                background-color: #D99A00;
                color: {TEXT_COLOR};
            }}

            QPushButton#delete_faculty_button:hover {{
                background-color: #991B1B;
            }}

            QPushButton#save_faculties_table_button:hover {{
                background-color: #065F46;
            }}

            QPushButton#revert_faculties_table_button:hover {{
                background-color: #475569;
            }}
            """
        )
