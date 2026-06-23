"""Headless tests for the FAQ CSV editing workflow."""

import csv, os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from database.init_db import initialize_database
from database.repositories.faq_repository import create_faq, delete_faq, get_all_faqs, get_faq_by_id
from ui.admin.pages.faq_page import FAQPage


def _app(): return QApplication.instance() or QApplication([])
def _db(tmp_path): path = tmp_path / "test.db"; initialize_database(path); return path
def _faq(db): return create_faq("Where is admissions?", "Main Building", "admissions", "Campus", db)


def test_faq_page_has_correct_toolbar_buttons(tmp_path):
    app = _app(); page = FAQPage(_db(tmp_path))
    try: assert app; assert [page.faq_toolbar_layout.itemAt(i).widget().objectName() for i in range(4)] == ["upload_faq_csv_button", "delete_faq_button", "export_faq_csv_button", "save_faq_table_button"]
    finally: page.close()
def test_faq_page_visible_columns_match_expected(tmp_path):
    app = _app(); page = FAQPage(_db(tmp_path))
    try: assert app; assert [page.faq_table.horizontalHeaderItem(i).text() for i in range(5)] == ["No.", "Question", "Answer", "Keywords", "Category"]
    finally: page.close()
def test_faq_page_upload_csv_automatically_imports_rows(tmp_path, monkeypatch):
    db = _db(tmp_path); path = tmp_path / "faq.csv"; path.write_text("question,answer,keywords,category\nWhere is admissions?,Main Building,admissions,Campus\n", encoding="utf-8"); monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(path), "CSV")); monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None); app = _app(); page = FAQPage(db)
    try: assert app; page.upload_csv(); assert len(get_all_faqs(db)) == 1
    finally: page.close()
def test_faq_page_export_csv_writes_file(tmp_path, monkeypatch):
    db = _db(tmp_path); _faq(db); path = tmp_path / "faq_export"; monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(path), "CSV")); monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None); app = _app(); page = FAQPage(db)
    try:
        assert app; page.export_csv()
        with (tmp_path / "faq_export.csv").open("r", encoding="utf-8-sig", newline="") as file: assert list(csv.reader(file))[1][1] == "Where is admissions?"
    finally: page.close()
def test_faq_page_save_edits_updates_database(tmp_path):
    db = _db(tmp_path); faq_id = _faq(db); app = _app(); page = FAQPage(db)
    try: assert app; page.faq_table.item(0, 2).setText("Updated Building"); page.save_table_changes(); assert get_faq_by_id(faq_id, db)["answer"] == "Updated Building"
    finally: page.close()
def test_faq_page_delete_selected_row_removes_database_row(tmp_path, monkeypatch):
    db = _db(tmp_path); faq_id = _faq(db); monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes); app = _app(); page = FAQPage(db)
    try: assert app; page.faq_table.selectRow(0); page.delete_selected_faq(); assert get_faq_by_id(faq_id, db) is None
    finally: page.close()
def test_faq_page_uses_row_numbers_and_internal_ids(tmp_path):
    db = _db(tmp_path); old = _faq(db); delete_faq(old, db); faq_id = _faq(db); app = _app(); page = FAQPage(db)
    try: assert app; item = page.faq_table.item(0, 0); assert item.text() == "1"; assert item.data(Qt.ItemDataRole.UserRole) == faq_id
    finally: page.close()
