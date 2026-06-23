"""Admin Dashboard page for viewing and managing university professors."""

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from controllers.professor_csv_controller import (
    export_professors_to_csv,
    import_professors_from_csv,
)
from database.connection import DB_NAME
from database.repositories.faculty_repository import get_all_faculties
from database.repositories.professor_repository import (
    create_professor,
    delete_professor,
    get_all_professors,
    get_professor_by_id,
    update_professor,
)
from database.repositories.room_repository import get_all_rooms
from ui.shared.theme import BACKGROUND_COLOR, PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR


class ProfessorFormDialog(QDialog):
    """Collect and validate professor details for create and edit actions."""

    def __init__(
        self,
        parent: QWidget | None = None,
        db_path: str | Path = DB_NAME,
        professor_data: dict | None = None,
    ) -> None:
        """Build the form, load related records, and optionally pre-fill it."""
        super().__init__(parent)
        self.db_path = db_path
        self.setWindowTitle("Edit Professor" if professor_data else "Add Professor")
        self.setModal(True)
        self.setMinimumWidth(560)
        self._build_ui()
        self._load_faculty_options()
        self._load_room_options()
        self._apply_styles()

        if professor_data:
            self._populate_form(professor_data)

    def _build_ui(self) -> None:
        """Create the labeled professor fields and explicit form actions."""
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(28, 24, 28, 24)
        dialog_layout.setSpacing(18)

        title_label = QLabel(self.windowTitle())
        title_label.setObjectName("professor_form_title")
        dialog_layout.addWidget(title_label)

        form_layout = QFormLayout()
        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(12)

        self.professor_full_name_input = QLineEdit()
        self.professor_full_name_input.setObjectName("professor_full_name_input")
        self.professor_title_input = QLineEdit()
        self.professor_title_input.setObjectName("professor_title_input")
        self.professor_faculty_combo = QComboBox()
        self.professor_faculty_combo.setObjectName("professor_faculty_combo")
        self.professor_office_room_combo = QComboBox()
        self.professor_office_room_combo.setObjectName(
            "professor_office_room_combo"
        )
        self.professor_email_input = QLineEdit()
        self.professor_email_input.setObjectName("professor_email_input")
        self.professor_phone_input = QLineEdit()
        self.professor_phone_input.setObjectName("professor_phone_input")
        self.professor_office_hours_input = QLineEdit()
        self.professor_office_hours_input.setObjectName(
            "professor_office_hours_input"
        )
        self.professor_photo_path_input = QLineEdit()
        self.professor_photo_path_input.setObjectName("professor_photo_path_input")
        self.browse_professor_photo_button = QPushButton("Browse")
        self.browse_professor_photo_button.setObjectName(
            "browse_professor_photo_button"
        )
        self.browse_professor_photo_button.clicked.connect(self.browse_photo)
        self.professor_bio_input = QTextEdit()
        self.professor_bio_input.setObjectName("professor_bio_input")
        self.professor_bio_input.setMaximumHeight(100)

        photo_layout = QHBoxLayout()
        photo_layout.setContentsMargins(0, 0, 0, 0)
        photo_layout.addWidget(self.professor_photo_path_input, stretch=1)
        photo_layout.addWidget(self.browse_professor_photo_button)

        form_layout.addRow("Full Name *", self.professor_full_name_input)
        form_layout.addRow("Title", self.professor_title_input)
        form_layout.addRow("Faculty *", self.professor_faculty_combo)
        form_layout.addRow("Office Room", self.professor_office_room_combo)
        form_layout.addRow("Email", self.professor_email_input)
        form_layout.addRow("Phone", self.professor_phone_input)
        form_layout.addRow("Office Hours", self.professor_office_hours_input)
        form_layout.addRow("Photo Path", photo_layout)
        form_layout.addRow("Bio", self.professor_bio_input)
        dialog_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_professor_button = QPushButton("Cancel")
        self.cancel_professor_button.setObjectName("cancel_professor_button")
        self.save_professor_button = QPushButton("Save")
        self.save_professor_button.setObjectName("save_professor_button")
        self.cancel_professor_button.clicked.connect(self.reject)
        self.save_professor_button.clicked.connect(self._validate_and_accept)
        button_layout.addWidget(self.cancel_professor_button)
        button_layout.addWidget(self.save_professor_button)
        dialog_layout.addLayout(button_layout)

    def _load_faculty_options(self) -> None:
        """Populate the required faculty combo with stable database IDs."""
        self.professor_faculty_combo.addItem("Select faculty", None)
        for faculty in get_all_faculties(self.db_path):
            self.professor_faculty_combo.addItem(faculty["name"], faculty["id"])

    def _load_room_options(self) -> None:
        """Populate optional office rooms with stable database IDs."""
        self.professor_office_room_combo.addItem("No office room", None)
        for room in get_all_rooms(self.db_path):
            room_label = f"{room['room_name']} - {room['room_number']}"
            self.professor_office_room_combo.addItem(room_label, room["id"])

    def _populate_form(self, professor_data: dict) -> None:
        """Fill controls from an existing professor repository row."""
        if hasattr(professor_data, "keys"):
            professor_data = {
                key: professor_data[key] for key in professor_data.keys()
            }
        self.professor_full_name_input.setText(
            professor_data.get("full_name") or ""
        )
        self.professor_title_input.setText(professor_data.get("title") or "")
        self.professor_email_input.setText(professor_data.get("email") or "")
        self.professor_phone_input.setText(professor_data.get("phone") or "")
        self.professor_office_hours_input.setText(
            professor_data.get("office_hours") or ""
        )
        self.professor_photo_path_input.setText(
            professor_data.get("photo_path") or ""
        )
        self.professor_bio_input.setPlainText(professor_data.get("bio") or "")

        faculty_index = self.professor_faculty_combo.findData(
            professor_data.get("faculty_id")
        )
        if faculty_index >= 0:
            self.professor_faculty_combo.setCurrentIndex(faculty_index)

        room_index = self.professor_office_room_combo.findData(
            professor_data.get("office_room_id")
        )
        if room_index >= 0:
            self.professor_office_room_combo.setCurrentIndex(room_index)

    def browse_photo(self) -> None:
        """Select a professor image and copy its path into the form."""
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Professor Photo",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
        )
        if selected_path:
            self.professor_photo_path_input.setText(selected_path)

    def get_form_data(self) -> dict:
        """Return normalized values compatible with the professor repository."""
        return {
            "full_name": self.professor_full_name_input.text().strip(),
            "title": self.professor_title_input.text().strip(),
            "faculty_id": self.professor_faculty_combo.currentData(),
            "office_room_id": self.professor_office_room_combo.currentData(),
            "email": self.professor_email_input.text().strip(),
            "phone": self.professor_phone_input.text().strip(),
            "office_hours": self.professor_office_hours_input.text().strip(),
            "photo_path": self.professor_photo_path_input.text().strip(),
            "bio": self.professor_bio_input.toPlainText().strip(),
        }

    def _validate_and_accept(self) -> None:
        """Accept the form only when its required values are present."""
        if not self.professor_full_name_input.text().strip():
            QMessageBox.warning(
                self,
                "Invalid Professor",
                "Professor full name is required.",
            )
            return
        if self.professor_faculty_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Invalid Professor",
                "Please select a faculty.",
            )
            return
        self.accept()

    def _apply_styles(self) -> None:
        """Style the professor form consistently with the dashboard."""
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: #FFFFFF;
                color: {TEXT_COLOR};
                font-family: "Segoe UI", Arial, sans-serif;
            }}
            QLabel#professor_form_title {{
                color: {PRIMARY_COLOR};
                font-size: 23px;
                font-weight: 700;
            }}
            QLineEdit, QComboBox, QTextEdit {{
                border: 1px solid #CBD5E1;
                border-radius: 7px;
                padding: 7px;
                font-size: 14px;
            }}
            QPushButton {{
                min-height: 36px;
                border-radius: 7px;
                padding: 0 16px;
                font-weight: 700;
            }}
            QPushButton#save_professor_button,
            QPushButton#browse_professor_photo_button {{
                background-color: {PRIMARY_COLOR};
                color: #FFFFFF;
                border: none;
            }}
            QPushButton#cancel_professor_button {{
                background-color: #E2E8F0;
                color: {TEXT_COLOR};
                border: none;
            }}
            """
        )


class ProfessorsPage(QWidget):
    """Display professor records and their joined academic/location details."""

    _COLUMNS = (
        ("No.", None),
        ("Full Name", "full_name"),
        ("Title", "title"),
        ("Faculty", "faculty_name"),
        ("Office Room", "office_room_name"),
        ("Email", "email"),
        ("Phone", "phone"),
        ("Office Hours", "office_hours"),
        ("Photo Path", "photo_path"),
        ("Bio", "bio"),
    )

    _FACULTY_ID_ROLE = int(Qt.ItemDataRole.UserRole) + 1
    _OFFICE_ROOM_ID_ROLE = int(Qt.ItemDataRole.UserRole) + 2

    def __init__(self, db_path: str | Path = DB_NAME) -> None:
        """Build the professor table for the selected SQLite database."""
        super().__init__()
        self.db_path = db_path
        self.has_unsaved_changes = False
        self.is_loading_table = False
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
        self.refresh_professors_button.setHidden(True)

        heading_layout.addLayout(title_layout)
        heading_layout.addStretch()

        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        self.professors_toolbar_layout = action_layout
        self.add_professor_button = QPushButton("Add Professor")
        self.add_professor_button.setObjectName("add_professor_button")
        self.add_professor_button.setHidden(True)
        self.edit_professor_button = QPushButton("Edit Selected")
        self.edit_professor_button.setObjectName("edit_professor_button")
        self.edit_professor_button.setHidden(True)
        self.upload_professors_csv_button = QPushButton("Upload CSV")
        self.upload_professors_csv_button.setObjectName(
            "upload_professors_csv_button"
        )
        self.delete_professor_button = QPushButton("Delete Selected Row")
        self.delete_professor_button.setObjectName("delete_professor_button")
        self.export_professors_csv_button = QPushButton("Export CSV")
        self.export_professors_csv_button.setObjectName(
            "export_professors_csv_button"
        )
        self.save_professors_table_button = QPushButton("Save Edits")
        self.save_professors_table_button.setObjectName(
            "save_professors_table_button"
        )
        for button in (
            self.upload_professors_csv_button,
            self.delete_professor_button,
            self.export_professors_csv_button,
            self.save_professors_table_button,
        ):
            button.setMinimumSize(150, 40)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            action_layout.addWidget(button)
        action_layout.addStretch()

        self.add_professor_button.clicked.connect(self.add_professor)
        self.edit_professor_button.clicked.connect(self.edit_selected_professor)
        self.upload_professors_csv_button.clicked.connect(self.upload_csv)
        self.delete_professor_button.clicked.connect(
            self.delete_selected_professor
        )
        self.export_professors_csv_button.clicked.connect(self.export_csv)
        self.save_professors_table_button.clicked.connect(
            self.save_table_changes
        )

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
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked
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
        self.professors_table.itemChanged.connect(self._handle_item_changed)

        header = self.professors_table.horizontalHeader()
        header.setMinimumSectionSize(80)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for column_index in (1, 3, 4, 7, 9):
            header.setSectionResizeMode(column_index, QHeaderView.ResizeMode.Stretch)

        table_layout.addWidget(self.professors_status_label)
        table_layout.addWidget(self.professors_table)
        page_layout.addLayout(heading_layout)
        page_layout.addLayout(action_layout)
        page_layout.addWidget(table_card, stretch=1)

    def load_professors(self) -> None:
        """Load current professors while keeping database failures non-fatal."""
        self.is_loading_table = True
        try:
            try:
                professors = get_all_professors(self.db_path)
            except sqlite3.Error:
                self.professors_table.setRowCount(0)
                self.has_unsaved_changes = False
                self.professors_status_label.setText(
                    "Unable to load professors due to a database error."
                )
                return

            self.professors_table.setRowCount(len(professors))
            for row_index, professor in enumerate(professors):
                for column_index, (_, field_name) in enumerate(self._COLUMNS):
                    value = (
                        row_index + 1
                        if field_name is None
                        else professor[field_name]
                    )
                    item = QTableWidgetItem("" if value is None else str(value))
                    if column_index == 0:
                        item.setData(
                            Qt.ItemDataRole.UserRole,
                            professor["id"],
                        )
                        item.setData(
                            self._FACULTY_ID_ROLE,
                            professor["faculty_id"],
                        )
                        item.setData(
                            self._OFFICE_ROOM_ID_ROLE,
                            professor["office_room_id"],
                        )
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if column_index in (0, 3, 4):
                        item.setFlags(
                            item.flags() & ~Qt.ItemFlag.ItemIsEditable
                        )
                    self.professors_table.setItem(row_index, column_index, item)

            self.has_unsaved_changes = False
            self.professors_status_label.setText(
                f"{len(professors)} professors found"
            )
        finally:
            self.is_loading_table = False

    def _handle_item_changed(self, item: QTableWidgetItem) -> None:
        """Track edits only for supported business columns."""
        if self.is_loading_table or item.column() not in (1, 2, 5, 6, 7, 8, 9):
            return
        self.has_unsaved_changes = True
        self.professors_status_label.setText("Unsaved changes")

    def _selected_professor_id(self) -> int | None:
        """Return the stable ID from the selected table row, when available."""
        selected_rows = self.professors_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        id_item = self.professors_table.item(selected_rows[0].row(), 0)
        if id_item is None:
            return None
        professor_id = id_item.data(Qt.ItemDataRole.UserRole)
        return int(professor_id) if professor_id is not None else None

    def upload_csv(self) -> None:
        """Select a CSV and immediately import its valid rows into SQLite."""
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Professors CSV",
            "",
            "CSV Files (*.csv)",
        )
        if not selected_path:
            return

        try:
            summary = import_professors_from_csv(selected_path, self.db_path)
        except (FileNotFoundError, ValueError, UnicodeError) as error:
            QMessageBox.warning(self, "Professor CSV Import", str(error))
            return
        except (OSError, sqlite3.Error) as error:
            QMessageBox.critical(self, "Professor CSV Import", str(error))
            return

        self.load_professors()
        message = (
            f"Created: {summary['created']}\n"
            f"Updated: {summary['updated']}\n"
            f"Skipped: {summary['skipped']}\n"
            f"Errors: {len(summary['errors'])}"
        )
        if summary["errors"]:
            if any("does not exist" in error for error in summary["errors"]):
                message += (
                    "\n\nSome professor rows were skipped because their "
                    "faculty_id or office_room_id does not exist.\n"
                    "Import order should be:\n"
                    "faculties.csv → rooms.csv → professors.csv"
                )
            short_errors = "\n".join(summary["errors"][:3])
            if len(summary["errors"]) > 3:
                short_errors += "\nAdditional errors were omitted."
            message += f"\n\n{short_errors}"
        QMessageBox.information(self, "Professor CSV Import", message)

    def export_csv(self) -> None:
        """Select a destination and export current professor records."""
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Professors CSV",
            "professors.csv",
            "CSV Files (*.csv)",
        )
        if not selected_path:
            return

        destination_path = Path(selected_path)
        if destination_path.suffix.lower() != ".csv":
            destination_path = Path(f"{destination_path}.csv")
        try:
            exported_count = export_professors_to_csv(
                destination_path,
                self.db_path,
            )
        except (OSError, sqlite3.Error, ValueError) as error:
            QMessageBox.critical(self, "Professor CSV Export", str(error))
            return
        QMessageBox.information(
            self,
            "Professor CSV Export",
            f"Exported {exported_count} professors successfully.",
        )

    def save_table_changes(self) -> None:
        """Validate and persist editable professor fields in every row."""
        professor_rows: list[tuple[int, dict]] = []
        for row_index in range(self.professors_table.rowCount()):
            id_item = self.professors_table.item(row_index, 0)
            professor_id = id_item.data(Qt.ItemDataRole.UserRole)
            form_data = {
                "full_name": self.professors_table.item(row_index, 1)
                .text()
                .strip(),
                "title": self.professors_table.item(row_index, 2).text().strip(),
                "faculty_id": id_item.data(self._FACULTY_ID_ROLE),
                "office_room_id": id_item.data(self._OFFICE_ROOM_ID_ROLE),
                "email": self.professors_table.item(row_index, 5).text().strip(),
                "phone": self.professors_table.item(row_index, 6).text().strip(),
                "office_hours": self.professors_table.item(row_index, 7)
                .text()
                .strip(),
                "photo_path": self.professors_table.item(row_index, 8)
                .text()
                .strip(),
                "bio": self.professors_table.item(row_index, 9).text().strip(),
            }
            if not form_data["full_name"]:
                QMessageBox.warning(
                    self,
                    "Invalid Professor",
                    "Professor full name cannot be empty.",
                )
                return
            professor_rows.append((int(professor_id), form_data))

        try:
            for professor_id, form_data in professor_rows:
                if not update_professor(
                    professor_id,
                    db_path=self.db_path,
                    **form_data,
                ):
                    raise ValueError(
                        f"Professor record {professor_id} could not be updated."
                    )
        except ValueError as error:
            QMessageBox.warning(self, "Professor Error", str(error))
            return
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Professor Error", str(error))
            return

        self.has_unsaved_changes = False
        self.load_professors()
        self.professors_status_label.setText("Changes saved successfully.")

    def add_professor(self) -> None:
        """Create a professor from an accepted form and reload the table."""
        dialog = ProfessorFormDialog(self, self.db_path)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            create_professor(db_path=self.db_path, **dialog.get_form_data())
        except (ValueError, sqlite3.Error) as error:
            QMessageBox.critical(self, "Professor Error", str(error))
            return
        self.load_professors()

    def edit_selected_professor(self) -> None:
        """Update the selected professor from a pre-filled form."""
        professor_id = self._selected_professor_id()
        if professor_id is None:
            QMessageBox.warning(
                self,
                "No Professor Selected",
                "Please select a professor to edit.",
            )
            return

        try:
            professor = get_professor_by_id(professor_id, self.db_path)
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Professor Error", str(error))
            return
        if professor is None:
            QMessageBox.warning(
                self,
                "Professor Not Found",
                "The selected professor could not be found.",
            )
            return

        professor_data = {key: professor[key] for key in professor.keys()}
        dialog = ProfessorFormDialog(self, self.db_path, professor_data)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            updated = update_professor(
                professor_id,
                db_path=self.db_path,
                **dialog.get_form_data(),
            )
        except (ValueError, sqlite3.Error) as error:
            QMessageBox.critical(self, "Professor Error", str(error))
            return
        if not updated:
            QMessageBox.warning(
                self,
                "Professor Not Found",
                "The selected professor could not be updated.",
            )
            return
        self.load_professors()

    def delete_selected_professor(self) -> None:
        """Confirm and delete the selected professor record."""
        professor_id = self._selected_professor_id()
        if professor_id is None:
            QMessageBox.warning(
                self,
                "No Professor Selected",
                "Please select a professor to delete.",
            )
            return

        confirmation = QMessageBox.question(
            self,
            "Delete Professor",
            "Are you sure you want to delete the selected professor?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            deleted = delete_professor(professor_id, self.db_path)
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Professor Error", str(error))
            return
        if not deleted:
            QMessageBox.warning(
                self,
                "Professor Not Found",
                "The selected professor could not be deleted.",
            )
            return
        self.load_professors()

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

            QPushButton#refresh_professors_button,
            QPushButton#add_professor_button,
            QPushButton#edit_professor_button,
            QPushButton#delete_professor_button,
            QPushButton#upload_professors_csv_button,
            QPushButton#export_professors_csv_button,
            QPushButton#save_professors_table_button {{
                background-color: {PRIMARY_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 0 18px;
                font-size: 14px;
                font-weight: 700;
                text-align: center;
            }}

            QPushButton#refresh_professors_button:hover,
            QPushButton#add_professor_button:hover,
            QPushButton#edit_professor_button:hover,
            QPushButton#delete_professor_button:hover,
            QPushButton#upload_professors_csv_button:hover,
            QPushButton#export_professors_csv_button:hover,
            QPushButton#save_professors_table_button:hover {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
            }}
            """
        )
