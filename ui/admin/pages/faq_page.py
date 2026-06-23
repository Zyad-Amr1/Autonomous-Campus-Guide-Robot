"""Admin page for CSV-driven robot FAQ management."""

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from controllers.faq_csv_controller import export_faq_to_csv, import_faq_from_csv
from database.connection import DB_NAME
from database.repositories.faq_repository import delete_faq, get_all_faqs, update_faq
from ui.shared.theme import BACKGROUND_COLOR, PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR


class FAQPage(QWidget):
    """Display and edit robot question-and-answer records."""

    _COLUMNS = (("No.", None), ("Question", "question"), ("Answer", "answer"), ("Keywords", "keywords"), ("Category", "category"))

    def __init__(self, db_path: str | Path = DB_NAME) -> None:
        super().__init__()
        self.db_path = db_path
        self.is_loading_table = False
        self._build_ui()
        self._apply_styles()
        self.load_faq()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self); layout.setContentsMargins(4, 4, 4, 4); layout.setSpacing(18)
        heading = QVBoxLayout()
        title = QLabel("FAQ"); title.setObjectName("faq_page_title")
        subtitle = QLabel("Manage robot questions, answers, keywords, and categories"); subtitle.setObjectName("faq_page_subtitle")
        heading.addWidget(title); heading.addWidget(subtitle)
        toolbar = QHBoxLayout(); self.faq_toolbar_layout = toolbar
        self.upload_faq_csv_button = QPushButton("Upload CSV"); self.upload_faq_csv_button.setObjectName("upload_faq_csv_button")
        self.delete_faq_button = QPushButton("Delete Selected Row"); self.delete_faq_button.setObjectName("delete_faq_button")
        self.export_faq_csv_button = QPushButton("Export CSV"); self.export_faq_csv_button.setObjectName("export_faq_csv_button")
        self.save_faq_table_button = QPushButton("Save Edits"); self.save_faq_table_button.setObjectName("save_faq_table_button")
        for button in (self.upload_faq_csv_button, self.delete_faq_button, self.export_faq_csv_button, self.save_faq_table_button):
            button.setMinimumSize(150, 40); toolbar.addWidget(button)
        toolbar.addStretch()
        self.upload_faq_csv_button.clicked.connect(self.upload_csv); self.delete_faq_button.clicked.connect(self.delete_selected_faq)
        self.export_faq_csv_button.clicked.connect(self.export_csv); self.save_faq_table_button.clicked.connect(self.save_table_changes)
        card = QFrame(); card.setObjectName("faq_table_card"); card_layout = QVBoxLayout(card)
        self.faq_status_label = QLabel("0 FAQ entries found"); self.faq_status_label.setObjectName("faq_status_label")
        self.faq_table = QTableWidget(); self.faq_table.setObjectName("faq_table")
        self.faq_table.setColumnCount(len(self._COLUMNS)); self.faq_table.setHorizontalHeaderLabels([label for label, _ in self._COLUMNS])
        self.faq_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed | QAbstractItemView.EditTrigger.SelectedClicked)
        self.faq_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.faq_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.faq_table.setAlternatingRowColors(True); self.faq_table.setShowGrid(False); self.faq_table.verticalHeader().setVisible(False)
        self.faq_table.itemChanged.connect(self._item_changed)
        header = self.faq_table.horizontalHeader(); header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch); header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        card_layout.addWidget(self.faq_status_label); card_layout.addWidget(self.faq_table)
        layout.addLayout(heading); layout.addLayout(toolbar); layout.addWidget(card, stretch=1)

    def load_faq(self) -> None:
        """Load FAQ rows with sequential display numbers and internal IDs."""
        self.is_loading_table = True
        try:
            try: faqs = get_all_faqs(self.db_path)
            except sqlite3.Error:
                self.faq_table.setRowCount(0); self.faq_status_label.setText("Unable to load FAQ due to a database error."); return
            self.faq_table.setRowCount(len(faqs))
            for row, faq in enumerate(faqs):
                for column, (_, field) in enumerate(self._COLUMNS):
                    value = row + 1 if field is None else faq[field]
                    item = QTableWidgetItem("" if value is None else str(value))
                    if column == 0:
                        item.setData(Qt.ItemDataRole.UserRole, faq["id"]); item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable); item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.faq_table.setItem(row, column, item)
            self.faq_status_label.setText(f"{len(faqs)} FAQ entries found")
        finally: self.is_loading_table = False

    def _item_changed(self, item: QTableWidgetItem) -> None:
        if not self.is_loading_table and item.column() > 0: self.faq_status_label.setText("Unsaved changes")

    def _selected_id(self) -> int | None:
        rows = self.faq_table.selectionModel().selectedRows()
        if not rows: return None
        value = self.faq_table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return int(value) if value is not None else None

    def upload_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import FAQ CSV", "", "CSV Files (*.csv)")
        if not path: return
        try: summary = import_faq_from_csv(path, self.db_path)
        except (FileNotFoundError, ValueError, UnicodeError) as error: QMessageBox.warning(self, "FAQ CSV Import", str(error)); return
        except (OSError, sqlite3.Error) as error: QMessageBox.critical(self, "FAQ CSV Import", str(error)); return
        self.load_faq(); message = f"Created: {summary['created']}\nUpdated: {summary['updated']}\nSkipped: {summary['skipped']}\nErrors: {len(summary['errors'])}"
        if summary["errors"]: message += "\n\n" + "\n".join(summary["errors"][:3])
        QMessageBox.information(self, "FAQ CSV Import", message)

    def export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export FAQ CSV", "faq.csv", "CSV Files (*.csv)")
        if not path: return
        destination = Path(path)
        if destination.suffix.lower() != ".csv": destination = Path(f"{destination}.csv")
        try: count = export_faq_to_csv(destination, self.db_path)
        except (OSError, sqlite3.Error, ValueError) as error: QMessageBox.critical(self, "FAQ CSV Export", str(error)); return
        QMessageBox.information(self, "FAQ CSV Export", f"Exported {count} FAQ entries successfully.")

    def save_table_changes(self) -> None:
        rows = []
        for row in range(self.faq_table.rowCount()):
            data = {"question": self.faq_table.item(row, 1).text().strip(), "answer": self.faq_table.item(row, 2).text().strip(), "keywords": self.faq_table.item(row, 3).text().strip(), "category": self.faq_table.item(row, 4).text().strip()}
            if not data["question"] or not data["answer"]: QMessageBox.warning(self, "Invalid FAQ", "Question and answer are required."); return
            faq_id = self.faq_table.item(row, 0).data(Qt.ItemDataRole.UserRole); rows.append((int(faq_id), data))
        try:
            for faq_id, data in rows:
                if not update_faq(faq_id, db_path=self.db_path, **data): raise ValueError(f"FAQ record {faq_id} could not be updated.")
        except ValueError as error: QMessageBox.warning(self, "FAQ Error", str(error)); return
        except sqlite3.Error as error: QMessageBox.critical(self, "FAQ Error", str(error)); return
        self.load_faq(); self.faq_status_label.setText("Changes saved successfully.")

    def delete_selected_faq(self) -> None:
        faq_id = self._selected_id()
        if faq_id is None: QMessageBox.warning(self, "No FAQ Selected", "Please select an FAQ entry to delete."); return
        answer = QMessageBox.question(self, "Delete FAQ", "Are you sure you want to delete the selected FAQ entry?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes: return
        try: deleted = delete_faq(faq_id, self.db_path)
        except sqlite3.Error as error: QMessageBox.critical(self, "FAQ Error", str(error)); return
        if not deleted: QMessageBox.warning(self, "FAQ Not Found", "The selected FAQ entry could not be deleted."); return
        self.load_faq(); self.faq_status_label.setText("FAQ entry deleted successfully.")

    def _apply_styles(self) -> None:
        self.setStyleSheet(f"""
            FAQPage {{ background: {BACKGROUND_COLOR}; color: {TEXT_COLOR}; font-family: "Segoe UI"; }}
            QLabel#faq_page_title {{ color: {PRIMARY_COLOR}; font-size: 27px; font-weight: 700; }}
            QLabel#faq_page_subtitle, QLabel#faq_status_label {{ color: #64748B; }}
            QFrame#faq_table_card {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }}
            QTableWidget#faq_table {{ background: #FFFFFF; alternate-background-color: #F8FAFC; border: 1px solid #E2E8F0; selection-background-color: #DCE8F5; }}
            QHeaderView::section {{ background: {PRIMARY_COLOR}; color: #FFFFFF; border: none; padding: 10px; font-weight: 700; }}
            QPushButton {{ background: {PRIMARY_COLOR}; color: #FFFFFF; border: none; border-radius: 8px; padding: 0 18px; font-weight: 700; }}
            QPushButton:hover {{ background: {SECONDARY_COLOR}; color: {TEXT_COLOR}; }}
        """)
