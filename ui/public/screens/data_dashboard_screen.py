"""Unified protected data management area inside the public dashboard."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.course_csv_controller import (
    export_courses_to_csv,
    import_courses_from_csv,
)
from controllers.event_csv_controller import (
    export_events_to_csv,
    import_events_from_csv,
)
from controllers.faculty_csv_controller import (
    export_faculties_to_csv,
    import_faculties_from_csv,
)
from controllers.faq_csv_controller import export_faq_to_csv, import_faq_from_csv
from controllers.professor_csv_controller import (
    export_professors_to_csv,
    import_professors_from_csv,
)
from controllers.rag.knowledge_store import load_knowledge_chunks
from controllers.rag.sync_external_sources import sync_external_sources_to_knowledge_base
from controllers.rag.sync_knowledge_base import sync_database_to_knowledge_base
from controllers.room_csv_controller import export_rooms_to_csv, import_rooms_from_csv
from database.connection import DB_NAME
from database.repositories.course_repository import (
    delete_course,
    get_all_courses,
    update_course,
)
from database.repositories.event_repository import (
    delete_event,
    get_all_events,
    update_event,
)
from database.repositories.faculty_repository import (
    delete_faculty,
    get_all_faculties,
    update_faculty,
)
from database.repositories.faq_repository import delete_faq, get_all_faqs, update_faq
from database.repositories.professor_repository import (
    delete_professor,
    get_all_professors,
    update_professor,
)
from database.repositories.room_repository import (
    delete_room,
    get_all_rooms,
    update_room,
)
from ui.public.theme import (
    BORDER,
    BUTTON_HEIGHT,
    CARD_PADDING,
    CARD_RADIUS,
    CHARCOAL,
    ECU_RED,
    ECU_RED_DARK,
    GOLD_LIGHT,
    LIGHT_GRAY,
    OFF_WHITE,
    PAGE_PADDING,
    TEXT_DARK,
    TEXT_MUTED,
    TOUCH_BUTTON_HEIGHT,
    WHITE,
    font,
    px,
)


DATASETS = {
    "Faculties": {
        "loader": get_all_faculties,
        "importer": import_faculties_from_csv,
        "exporter": export_faculties_to_csv,
        "deleter": delete_faculty,
        "columns": ("name", "description", "building", "dean_name"),
        "readonly": (),
        "updater": update_faculty,
    },
    "Rooms": {
        "loader": get_all_rooms,
        "importer": import_rooms_from_csv,
        "exporter": export_rooms_to_csv,
        "deleter": delete_room,
        "columns": (
            "room_name",
            "room_number",
            "building",
            "floor",
            "category",
            "description",
            "x_coord",
            "y_coord",
        ),
        "readonly": (),
        "updater": update_room,
    },
    "Professors": {
        "loader": get_all_professors,
        "importer": import_professors_from_csv,
        "exporter": export_professors_to_csv,
        "deleter": delete_professor,
        "columns": (
            "full_name",
            "title",
            "faculty_id",
            "faculty_name",
            "office_room_id",
            "office_room_name",
            "email",
            "phone",
            "office_hours",
            "photo_path",
            "bio",
        ),
        "readonly": ("faculty_name", "office_room_name"),
        "updater": update_professor,
    },
    "Courses": {
        "loader": get_all_courses,
        "importer": import_courses_from_csv,
        "exporter": export_courses_to_csv,
        "deleter": delete_course,
        "columns": (
            "course_code",
            "course_name",
            "faculty_id",
            "faculty_name",
            "professor_id",
            "professor_name",
            "room_id",
            "room_name",
            "schedule_day",
            "start_time",
            "end_time",
            "semester",
        ),
        "readonly": ("faculty_name", "professor_name", "room_name"),
        "updater": update_course,
    },
    "Events": {
        "loader": get_all_events,
        "importer": import_events_from_csv,
        "exporter": export_events_to_csv,
        "deleter": delete_event,
        "columns": (
            "title",
            "description",
            "location",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
        ),
        "readonly": (),
        "updater": update_event,
    },
    "FAQ": {
        "loader": get_all_faqs,
        "importer": import_faq_from_csv,
        "exporter": export_faq_to_csv,
        "deleter": delete_faq,
        "columns": ("question", "answer", "keywords", "category"),
        "readonly": (),
        "updater": update_faq,
    },
}


class DataDashboardScreen(QWidget):
    """Modern public-themed data dashboard with CSV and table editing tools."""

    def __init__(self, db_path=DB_NAME) -> None:
        """Create the protected data dashboard."""
        super().__init__()
        self.db_path = db_path
        self.setObjectName("data_dashboard_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._apply_styles()
        self.load_selected_dataset()

    def _build_ui(self) -> None:
        """Build selector, action buttons, status, and editable table."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(PAGE_PADDING, 24, PAGE_PADDING, PAGE_PADDING)
        page_layout.setSpacing(14)

        self.data_dashboard_title = QLabel("Data Management")
        self.data_dashboard_title.setObjectName("data_dashboard_title")
        self.data_dashboard_subtitle = QLabel(
            "Manage university data using CSV files and table editing."
        )
        self.data_dashboard_subtitle.setObjectName("data_dashboard_subtitle")
        self.data_dashboard_subtitle.setWordWrap(True)
        page_layout.addWidget(self.data_dashboard_title)
        page_layout.addWidget(self.data_dashboard_subtitle)

        toolbar = QFrame()
        toolbar.setObjectName("data_toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 14, 16, 14)
        toolbar_layout.setSpacing(10)

        self.data_dataset_selector = QComboBox()
        self.data_dataset_selector.setObjectName("data_dataset_selector")
        self.data_dataset_selector.addItems(DATASETS.keys())
        self.data_dataset_selector.currentTextChanged.connect(self.load_selected_dataset)
        toolbar_layout.addWidget(self.data_dataset_selector, stretch=1)

        self.data_upload_csv_button = QPushButton("Upload CSV")
        self.data_upload_csv_button.setObjectName("data_upload_csv_button")
        self.data_delete_row_button = QPushButton("Delete Selected Row")
        self.data_delete_row_button.setObjectName("data_delete_row_button")
        self.data_export_csv_button = QPushButton("Export CSV")
        self.data_export_csv_button.setObjectName("data_export_csv_button")
        self.data_save_edits_button = QPushButton("Save Edits")
        self.data_save_edits_button.setObjectName("data_save_edits_button")

        for button in (
            self.data_upload_csv_button,
            self.data_delete_row_button,
            self.data_export_csv_button,
            self.data_save_edits_button,
        ):
            button.setMinimumHeight(BUTTON_HEIGHT)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            toolbar_layout.addWidget(button)

        self.data_upload_csv_button.clicked.connect(self.upload_csv)
        self.data_delete_row_button.clicked.connect(self.delete_selected_row)
        self.data_export_csv_button.clicked.connect(self.export_csv)
        self.data_save_edits_button.clicked.connect(self.save_edits)
        page_layout.addWidget(toolbar)

        knowledge_panel = QFrame()
        knowledge_panel.setObjectName("knowledge_base_panel")
        knowledge_layout = QVBoxLayout(knowledge_panel)
        knowledge_layout.setContentsMargins(16, 14, 16, 14)
        knowledge_layout.setSpacing(10)

        knowledge_header_row = QHBoxLayout()
        knowledge_header_row.setSpacing(10)
        self.kb_section_title = QLabel("Knowledge Base")
        self.kb_section_title.setObjectName("kb_section_title")
        self.kb_status_label = QLabel("Ready to sync chatbot knowledge.")
        self.kb_status_label.setObjectName("kb_status_label")
        self.kb_status_label.setWordWrap(True)
        knowledge_header_row.addWidget(self.kb_section_title)
        knowledge_header_row.addWidget(self.kb_status_label, stretch=1)
        knowledge_layout.addLayout(knowledge_header_row)

        knowledge_button_row = QHBoxLayout()
        knowledge_button_row.setSpacing(10)
        self.kb_sync_database_button = QPushButton("Sync Database Knowledge")
        self.kb_sync_database_button.setObjectName("kb_sync_database_button")
        self.kb_sync_external_button = QPushButton("Sync Website/Documents")
        self.kb_sync_external_button.setObjectName("kb_sync_external_button")
        self.kb_rebuild_all_button = QPushButton("Rebuild All Knowledge")
        self.kb_rebuild_all_button.setObjectName("kb_rebuild_all_button")
        self.kb_status_button = QPushButton("Knowledge Status")
        self.kb_status_button.setObjectName("kb_status_button")

        for button in (
            self.kb_sync_database_button,
            self.kb_sync_external_button,
            self.kb_rebuild_all_button,
            self.kb_status_button,
        ):
            button.setMinimumHeight(BUTTON_HEIGHT)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            knowledge_button_row.addWidget(button)

        self.kb_sync_database_button.clicked.connect(self.sync_database_knowledge)
        self.kb_sync_external_button.clicked.connect(self.sync_external_knowledge)
        self.kb_rebuild_all_button.clicked.connect(self.rebuild_all_knowledge)
        self.kb_status_button.clicked.connect(self.show_knowledge_status)
        knowledge_layout.addLayout(knowledge_button_row)
        page_layout.addWidget(knowledge_panel)

        self.data_table = QTableWidget()
        self.data_table.setObjectName("data_table")
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.data_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        page_layout.addWidget(self.data_table, stretch=1)

        self.data_status_label = QLabel("")
        self.data_status_label.setObjectName("data_status_label")
        self.data_status_label.setWordWrap(True)
        page_layout.addWidget(self.data_status_label)

    def load_selected_dataset(self) -> None:
        """Load the selected dataset into the table without crashing."""
        dataset_name = self.data_dataset_selector.currentText()
        config = DATASETS[dataset_name]
        try:
            rows = config["loader"](self.db_path)
        except Exception as error:
            rows = []
            self._set_status(f"Could not load {dataset_name}: {error}")
        else:
            self._set_status(f"Loaded {len(rows)} {dataset_name} row(s).")
        self._populate_table(dataset_name, [dict(row) for row in rows])

    def upload_csv(self) -> None:
        """Import CSV rows for the selected dataset and reload the table."""
        csv_path, _ = QFileDialog.getOpenFileName(
            self,
            "Upload CSV",
            "",
            "CSV Files (*.csv)",
        )
        if not csv_path:
            return
        dataset_name = self.data_dataset_selector.currentText()
        try:
            result = DATASETS[dataset_name]["importer"](csv_path, self.db_path)
        except Exception as error:
            self._set_status(f"Some rows could not be imported: {error}")
        else:
            self._set_status(self._format_import_result(result))
        self.load_selected_dataset()

    def export_csv(self) -> None:
        """Export the selected dataset to a CSV path."""
        csv_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            f"{self.data_dataset_selector.currentText().lower()}.csv",
            "CSV Files (*.csv)",
        )
        if not csv_path:
            return
        try:
            count = DATASETS[self.data_dataset_selector.currentText()]["exporter"](
                csv_path,
                self.db_path,
            )
        except Exception as error:
            self._set_status(f"Could not export CSV: {error}")
            return
        self._set_status(f"Exported {count} row(s) to {Path(csv_path).name}.")

    def delete_selected_row(self) -> None:
        """Delete the currently selected row after confirmation."""
        row = self.data_table.currentRow()
        if row < 0:
            self._set_status("Select a row before deleting.")
            return
        answer = QMessageBox.question(
            self,
            "Delete row",
            "Delete the selected row?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        item = self.data_table.item(row, 0)
        record_id = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if record_id is None:
            self._set_status("Could not find the selected row id.")
            return
        try:
            deleted = DATASETS[self.data_dataset_selector.currentText()]["deleter"](
                int(record_id),
                self.db_path,
            )
        except Exception as error:
            self._set_status(f"Could not delete row: {error}")
            return
        self._set_status("Deleted selected row." if deleted else "Row was not found.")
        self.load_selected_dataset()

    def save_edits(self) -> None:
        """Persist safe editable fields for every visible row."""
        dataset_name = self.data_dataset_selector.currentText()
        config = DATASETS[dataset_name]
        saved = 0
        try:
            for row_index in range(self.data_table.rowCount()):
                record_id = self.data_table.item(row_index, 0).data(
                    Qt.ItemDataRole.UserRole
                )
                values = self._row_values(row_index, config["columns"])
                self._update_record(dataset_name, int(record_id), values)
                saved += 1
        except Exception as error:
            self._set_status(f"Some edits could not be saved: {error}")
            self.load_selected_dataset()
            return
        self._set_status(f"Saved edits for {saved} row(s).")
        self.load_selected_dataset()

    def sync_database_knowledge(self) -> None:
        """Sync managed database records into the chatbot knowledge store."""
        try:
            result = sync_database_to_knowledge_base(self.db_path)
        except Exception as error:
            self._set_kb_status(f"Could not sync database knowledge: {error}")
            return
        chunks_created = int(result.get("chunks_created", 0))
        self._set_kb_status(f"Synced {chunks_created} database knowledge chunk(s).")

    def sync_external_knowledge(self) -> None:
        """Sync website and document sources into the chatbot knowledge store."""
        try:
            result = sync_external_sources_to_knowledge_base(self.db_path)
        except Exception as error:
            self._set_kb_status(f"Could not sync website/documents: {error}")
            return
        website_chunks = int(result.get("website_chunks", 0))
        document_chunks = int(result.get("document_chunks", 0))
        errors = result.get("errors") or []
        message = (
            f"Synced {website_chunks} website chunk(s) and "
            f"{document_chunks} document chunk(s)."
        )
        if errors:
            message += f" Some sources need attention: {len(errors)} issue(s)."
        self._set_kb_status(message)

    def rebuild_all_knowledge(self) -> None:
        """Rebuild database, website, and document knowledge in one action."""
        try:
            database_result = sync_database_to_knowledge_base(self.db_path)
            external_result = sync_external_sources_to_knowledge_base(self.db_path)
        except Exception as error:
            self._set_kb_status(f"Could not rebuild all knowledge: {error}")
            return
        database_chunks = int(database_result.get("chunks_created", 0))
        website_chunks = int(external_result.get("website_chunks", 0))
        document_chunks = int(external_result.get("document_chunks", 0))
        self._set_kb_status(
            "Rebuilt knowledge base: "
            f"{database_chunks} database, {website_chunks} website, "
            f"{document_chunks} document chunk(s)."
        )

    def show_knowledge_status(self) -> None:
        """Show persisted chunk counts grouped by source."""
        try:
            chunks = load_knowledge_chunks(self.db_path)
        except Exception as error:
            self._set_kb_status(f"Could not read knowledge status: {error}")
            return
        if not chunks:
            self._set_kb_status("Knowledge base has no chunks yet.")
            return
        counts: dict[str, int] = {}
        for chunk in chunks:
            source = str(chunk.get("source") or "unknown")
            counts[source] = counts.get(source, 0) + 1
        grouped = ", ".join(
            f"{source}: {count}" for source, count in sorted(counts.items())
        )
        self._set_kb_status(f"Knowledge chunks: {len(chunks)} total ({grouped}).")

    def _populate_table(self, dataset_name: str, rows: list[dict]) -> None:
        """Fill the table with clean row numbers and hidden record ids."""
        config = DATASETS[dataset_name]
        columns = ("No.",) + config["columns"]
        self.data_table.clear()
        self.data_table.setColumnCount(len(columns))
        self.data_table.setHorizontalHeaderLabels(columns)
        self.data_table.setRowCount(len(rows))

        readonly = set(config["readonly"])
        for row_index, row in enumerate(rows):
            number_item = QTableWidgetItem(str(row_index + 1))
            number_item.setData(Qt.ItemDataRole.UserRole, row.get("id"))
            number_item.setFlags(number_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.data_table.setItem(row_index, 0, number_item)

            for column_index, column_name in enumerate(config["columns"], start=1):
                value = row.get(column_name)
                item = QTableWidgetItem("" if value is None else str(value))
                if column_name in readonly:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.data_table.setItem(row_index, column_index, item)
        self.data_table.resizeColumnsToContents()

    def _row_values(self, row_index: int, columns: tuple[str, ...]) -> dict:
        """Read one table row as a column/value dictionary."""
        values = {}
        for column_index, column_name in enumerate(columns, start=1):
            item = self.data_table.item(row_index, column_index)
            values[column_name] = item.text().strip() if item is not None else ""
        return values

    def _update_record(self, dataset_name: str, record_id: int, values: dict) -> None:
        """Dispatch one record update through the matching repository."""
        if dataset_name == "Faculties":
            update_faculty(
                record_id,
                values["name"],
                values["description"] or None,
                values["building"] or None,
                values["dean_name"] or None,
                self.db_path,
            )
        elif dataset_name == "Rooms":
            update_room(
                record_id,
                values["room_name"],
                values["room_number"],
                values["building"],
                int(values["floor"]),
                values["category"],
                values["description"] or None,
                self._optional_float(values["x_coord"]),
                self._optional_float(values["y_coord"]),
                self.db_path,
            )
        elif dataset_name == "Professors":
            update_professor(
                record_id,
                values["full_name"],
                values["title"] or None,
                int(values["faculty_id"]),
                self._optional_int(values["office_room_id"]),
                values["email"] or None,
                values["phone"] or None,
                values["office_hours"] or None,
                values["photo_path"] or None,
                values["bio"] or None,
                self.db_path,
            )
        elif dataset_name == "Courses":
            update_course(
                record_id,
                values["course_code"],
                values["course_name"],
                int(values["faculty_id"]),
                self._optional_int(values["professor_id"]),
                self._optional_int(values["room_id"]),
                values["schedule_day"],
                values["start_time"],
                values["end_time"],
                values["semester"] or None,
                self.db_path,
            )
        elif dataset_name == "Events":
            update_event(
                record_id,
                values["title"],
                values["description"] or None,
                values["location"] or None,
                values["start_date"],
                values["end_date"],
                values["start_time"] or None,
                values["end_time"] or None,
                self.db_path,
            )
        elif dataset_name == "FAQ":
            update_faq(
                record_id,
                values["question"],
                values["answer"],
                values["keywords"] or None,
                values["category"] or None,
                self.db_path,
            )

    def _format_import_result(self, result: dict) -> str:
        """Return friendly import feedback, including skipped rows."""
        imported = result.get("imported", result.get("created", 0))
        skipped = result.get("skipped", 0)
        if skipped:
            return f"Imported {imported} row(s). Skipped {skipped} row(s) with issues."
        return f"Imported {imported} row(s)."

    def _optional_int(self, value: str) -> int | None:
        """Convert optional integer text from the table."""
        return int(value) if value else None

    def _optional_float(self, value: str) -> float | None:
        """Convert optional float text from the table."""
        return float(value) if value else None

    def _set_status(self, message: str) -> None:
        """Update the dashboard status label."""
        self.data_status_label.setText(message)

    def _set_kb_status(self, message: str) -> None:
        """Update the knowledge base status label."""
        self.kb_status_label.setText(message)

    def _apply_styles(self) -> None:
        """Apply the modern public dashboard style."""
        self.setStyleSheet(
            f"""
            QWidget#data_dashboard_screen {{
                background-color: {OFF_WHITE};
                color: {TEXT_DARK};
                {font(17)}
            }}

            QLabel#data_dashboard_title {{
                color: {CHARCOAL};
                {font(32, 850)}
            }}

            QLabel#data_dashboard_subtitle,
            QLabel#data_status_label,
            QLabel#kb_status_label {{
                color: {TEXT_MUTED};
                {font(15, 650)}
            }}

            QLabel#kb_section_title {{
                color: {CHARCOAL};
                {font(18, 850)}
            }}

            QFrame#data_toolbar,
            QFrame#knowledge_base_panel {{
                background-color: {WHITE};
                border: 1px solid {BORDER};
                border-radius: {px(CARD_RADIUS)};
            }}

            QComboBox#data_dataset_selector {{
                background-color: {WHITE};
                color: {TEXT_DARK};
                border: 1px solid {BORDER};
                border-radius: {px(16)};
                padding: 0 {px(CARD_PADDING)};
                min-height: {px(BUTTON_HEIGHT)};
                {font(14, 750)}
            }}

            QPushButton {{
                background-color: {ECU_RED};
                color: {WHITE};
                border: none;
                border-radius: {px(16)};
                padding: 0 {px(16)};
                min-height: {px(BUTTON_HEIGHT)};
                {font(13, 800)}
            }}

            QPushButton:hover {{
                background-color: {ECU_RED_DARK};
            }}

            QPushButton:pressed {{
                background-color: {GOLD_LIGHT};
                color: {TEXT_DARK};
            }}

            QTableWidget#data_table {{
                background-color: {WHITE};
                alternate-background-color: {LIGHT_GRAY};
                color: {TEXT_DARK};
                gridline-color: {BORDER};
                border: 1px solid {BORDER};
                border-radius: {px(CARD_RADIUS)};
                selection-background-color: {GOLD_LIGHT};
                selection-color: {TEXT_DARK};
                {font(14, 550)}
            }}

            QHeaderView::section {{
                background-color: {CHARCOAL};
                color: {WHITE};
                border: none;
                padding: 10px;
                {font(13, 800)}
            }}
            """
        )

    def update_language(self, translations: dict[str, str]) -> None:
        """Refresh visible data dashboard controls."""
        self.data_dashboard_title.setText(translations["data_dashboard_title"])
        self.data_dashboard_subtitle.setText(translations["data_dashboard_subtitle"])
        self.data_upload_csv_button.setText(translations["data_upload_csv"])
        self.data_delete_row_button.setText(translations["data_delete_row"])
        self.data_export_csv_button.setText(translations["data_export_csv"])
        self.data_save_edits_button.setText(translations["data_save_edits"])
