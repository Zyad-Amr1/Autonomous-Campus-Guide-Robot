"""Admin page for CSV-driven course schedule management."""

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from controllers.course_csv_controller import export_courses_to_csv, import_courses_from_csv
from database.connection import DB_NAME
from database.repositories.course_repository import delete_course, get_all_courses, update_course
from ui.shared.theme import BACKGROUND_COLOR, PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR


class CoursesPage(QWidget):
    """Display and edit course schedules while preserving relationship IDs."""

    _COLUMNS = (
        ("No.", None), ("Course Code", "course_code"),
        ("Course Name", "course_name"), ("Faculty", "faculty_name"),
        ("Professor", "professor_name"), ("Room", "room_name"),
        ("Day", "schedule_day"), ("Start Time", "start_time"),
        ("End Time", "end_time"), ("Semester", "semester"),
    )
    _FACULTY_ROLE = int(Qt.ItemDataRole.UserRole) + 1
    _PROFESSOR_ROLE = int(Qt.ItemDataRole.UserRole) + 2
    _ROOM_ROLE = int(Qt.ItemDataRole.UserRole) + 3

    def __init__(self, db_path: str | Path = DB_NAME) -> None:
        """Build the course page for the selected SQLite database."""
        super().__init__()
        self.db_path = db_path
        self.is_loading_table = False
        self._build_ui()
        self._apply_styles()
        self.load_courses()

    def _build_ui(self) -> None:
        """Create the heading, four-action toolbar, status, and table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(18)
        heading = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Courses")
        title.setObjectName("courses_page_title")
        subtitle = QLabel("Manage course schedules, professors, rooms, and semesters")
        subtitle.setObjectName("courses_page_subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        heading.addLayout(titles)
        heading.addStretch()

        toolbar = QHBoxLayout()
        self.courses_toolbar_layout = toolbar
        self.upload_courses_csv_button = QPushButton("Upload CSV")
        self.upload_courses_csv_button.setObjectName("upload_courses_csv_button")
        self.delete_course_button = QPushButton("Delete Selected Row")
        self.delete_course_button.setObjectName("delete_course_button")
        self.export_courses_csv_button = QPushButton("Export CSV")
        self.export_courses_csv_button.setObjectName("export_courses_csv_button")
        self.save_courses_table_button = QPushButton("Save Edits")
        self.save_courses_table_button.setObjectName("save_courses_table_button")
        for button in (
            self.upload_courses_csv_button, self.delete_course_button,
            self.export_courses_csv_button, self.save_courses_table_button,
        ):
            button.setMinimumSize(150, 40)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            toolbar.addWidget(button)
        toolbar.addStretch()
        self.upload_courses_csv_button.clicked.connect(self.upload_csv)
        self.delete_course_button.clicked.connect(self.delete_selected_course)
        self.export_courses_csv_button.clicked.connect(self.export_csv)
        self.save_courses_table_button.clicked.connect(self.save_table_changes)

        card = QFrame()
        card.setObjectName("courses_table_card")
        card_layout = QVBoxLayout(card)
        self.courses_status_label = QLabel("0 courses found")
        self.courses_status_label.setObjectName("courses_status_label")
        self.courses_table = QTableWidget()
        self.courses_table.setObjectName("courses_table")
        self.courses_table.setColumnCount(len(self._COLUMNS))
        self.courses_table.setHorizontalHeaderLabels([label for label, _ in self._COLUMNS])
        self.courses_table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked
        )
        self.courses_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.courses_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.courses_table.setAlternatingRowColors(True)
        self.courses_table.setShowGrid(False)
        self.courses_table.verticalHeader().setVisible(False)
        self.courses_table.itemChanged.connect(self._handle_item_changed)
        header = self.courses_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for column in (2, 3, 4, 5):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        card_layout.addWidget(self.courses_status_label)
        card_layout.addWidget(self.courses_table)
        layout.addLayout(heading)
        layout.addLayout(toolbar)
        layout.addWidget(card, stretch=1)

    def load_courses(self) -> None:
        """Load joined course rows and their stable relationship identifiers."""
        self.is_loading_table = True
        try:
            try:
                courses = get_all_courses(self.db_path)
            except sqlite3.Error:
                self.courses_table.setRowCount(0)
                self.courses_status_label.setText("Unable to load courses due to a database error.")
                return
            self.courses_table.setRowCount(len(courses))
            for row_index, course in enumerate(courses):
                for column_index, (_, field) in enumerate(self._COLUMNS):
                    value = row_index + 1 if field is None else course[field]
                    item = QTableWidgetItem("" if value is None else str(value))
                    if column_index == 0:
                        item.setData(Qt.ItemDataRole.UserRole, course["id"])
                        item.setData(self._FACULTY_ROLE, course["faculty_id"])
                        item.setData(self._PROFESSOR_ROLE, course["professor_id"])
                        item.setData(self._ROOM_ROLE, course["room_id"])
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if column_index in (0, 3, 4, 5):
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.courses_table.setItem(row_index, column_index, item)
            self.courses_status_label.setText(f"{len(courses)} courses found")
        finally:
            self.is_loading_table = False

    def _handle_item_changed(self, item: QTableWidgetItem) -> None:
        """Report unsaved changes for editable course cells."""
        if not self.is_loading_table and item.column() in (1, 2, 6, 7, 8, 9):
            self.courses_status_label.setText("Unsaved changes")

    def _selected_id(self) -> int | None:
        """Return the internal ID of the selected course row."""
        rows = self.courses_table.selectionModel().selectedRows()
        if not rows:
            return None
        value = self.courses_table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return int(value) if value is not None else None

    def upload_csv(self) -> None:
        """Select and automatically import a strict course CSV."""
        path, _ = QFileDialog.getOpenFileName(self, "Import Courses CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            summary = import_courses_from_csv(path, self.db_path)
        except (FileNotFoundError, ValueError, UnicodeError) as error:
            QMessageBox.warning(self, "Course CSV Import", str(error))
            return
        except (OSError, sqlite3.Error) as error:
            QMessageBox.critical(self, "Course CSV Import", str(error))
            return
        self.load_courses()
        message = (
            f"Created: {summary['created']}\nUpdated: {summary['updated']}\n"
            f"Skipped: {summary['skipped']}\nErrors: {len(summary['errors'])}"
        )
        if summary["errors"]:
            message += "\n\n" + "\n".join(summary["errors"][:3])
        QMessageBox.information(self, "Course CSV Import", message)

    def export_csv(self) -> None:
        """Export all courses to a chosen CSV destination."""
        path, _ = QFileDialog.getSaveFileName(self, "Export Courses CSV", "courses.csv", "CSV Files (*.csv)")
        if not path:
            return
        destination = Path(path)
        if destination.suffix.lower() != ".csv":
            destination = Path(f"{destination}.csv")
        try:
            count = export_courses_to_csv(destination, self.db_path)
        except (OSError, sqlite3.Error, ValueError) as error:
            QMessageBox.critical(self, "Course CSV Export", str(error))
            return
        QMessageBox.information(self, "Course CSV Export", f"Exported {count} courses successfully.")

    def save_table_changes(self) -> None:
        """Persist editable fields while retaining relationship IDs."""
        rows = []
        for row in range(self.courses_table.rowCount()):
            id_item = self.courses_table.item(row, 0)
            data = {
                "course_code": self.courses_table.item(row, 1).text().strip(),
                "course_name": self.courses_table.item(row, 2).text().strip(),
                "faculty_id": id_item.data(self._FACULTY_ROLE),
                "professor_id": id_item.data(self._PROFESSOR_ROLE),
                "room_id": id_item.data(self._ROOM_ROLE),
                "schedule_day": self.courses_table.item(row, 6).text().strip(),
                "start_time": self.courses_table.item(row, 7).text().strip(),
                "end_time": self.courses_table.item(row, 8).text().strip(),
                "semester": self.courses_table.item(row, 9).text().strip(),
            }
            if not data["course_code"] or not data["course_name"] or data["faculty_id"] is None:
                QMessageBox.warning(self, "Invalid Course", "Course code, course name, and faculty are required.")
                return
            rows.append((int(id_item.data(Qt.ItemDataRole.UserRole)), data))
        try:
            for course_id, data in rows:
                if not update_course(course_id, db_path=self.db_path, **data):
                    raise ValueError(f"Course record {course_id} could not be updated.")
        except ValueError as error:
            QMessageBox.warning(self, "Course Error", str(error))
            return
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Course Error", str(error))
            return
        self.load_courses()
        self.courses_status_label.setText("Changes saved successfully.")

    def delete_selected_course(self) -> None:
        """Confirm and delete the selected course by internal ID."""
        course_id = self._selected_id()
        if course_id is None:
            QMessageBox.warning(self, "No Course Selected", "Please select a course to delete.")
            return
        answer = QMessageBox.question(
            self, "Delete Course", "Are you sure you want to delete the selected course?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            deleted = delete_course(course_id, self.db_path)
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Course Error", str(error))
            return
        if not deleted:
            QMessageBox.warning(self, "Course Not Found", "The selected course could not be deleted.")
            return
        self.load_courses()
        self.courses_status_label.setText("Course deleted successfully.")

    def _apply_styles(self) -> None:
        """Apply the shared professional dashboard presentation."""
        self.setStyleSheet(f"""
            CoursesPage {{ background-color: {BACKGROUND_COLOR}; color: {TEXT_COLOR}; font-family: "Segoe UI"; }}
            QLabel#courses_page_title {{ color: {PRIMARY_COLOR}; font-size: 27px; font-weight: 700; }}
            QLabel#courses_page_subtitle, QLabel#courses_status_label {{ color: #64748B; font-size: 13px; }}
            QFrame#courses_table_card {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }}
            QTableWidget#courses_table {{ background: #FFFFFF; alternate-background-color: #F8FAFC; border: 1px solid #E2E8F0; selection-background-color: #DCE8F5; }}
            QHeaderView::section {{ background: {PRIMARY_COLOR}; color: #FFFFFF; border: none; padding: 10px 8px; font-weight: 700; }}
            QPushButton {{ background: {PRIMARY_COLOR}; color: #FFFFFF; border: none; border-radius: 8px; padding: 0 18px; font-weight: 700; }}
            QPushButton:hover {{ background: {SECONDARY_COLOR}; color: {TEXT_COLOR}; }}
        """)
