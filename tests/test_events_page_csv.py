"""Headless tests for the Events CSV editing workflow."""

import csv, os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from database.init_db import initialize_database
from database.repositories.event_repository import create_event, delete_event, get_all_events, get_event_by_id
from ui.admin.pages.events_page import EventsPage


def _app(): return QApplication.instance() or QApplication([])
def _db(tmp_path): path = tmp_path / "test.db"; initialize_database(path); return path
def _event(db): return create_event("Open Day", "Welcome", "Campus", "2026-07-01", "2026-07-01", "10:00", "14:00", db)


def test_events_page_has_correct_toolbar_buttons(tmp_path):
    app = _app(); page = EventsPage(_db(tmp_path))
    try: assert app; assert [page.events_toolbar_layout.itemAt(i).widget().objectName() for i in range(4)] == ["upload_events_csv_button", "delete_event_button", "export_events_csv_button", "save_events_table_button"]
    finally: page.close()
def test_events_page_visible_columns_match_expected(tmp_path):
    app = _app(); page = EventsPage(_db(tmp_path))
    try: assert app; assert [page.events_table.horizontalHeaderItem(i).text() for i in range(8)] == ["No.", "Title", "Description", "Location", "Start Date", "End Date", "Start Time", "End Time"]
    finally: page.close()
def test_events_page_upload_csv_automatically_imports_rows(tmp_path, monkeypatch):
    db = _db(tmp_path); path = tmp_path / "events.csv"; path.write_text("title,description,location,start_date,end_date,start_time,end_time\nOpen Day,Welcome,Campus,2026-07-01,2026-07-01,10:00,14:00\n", encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(path), "CSV")); monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None); app = _app(); page = EventsPage(db)
    try: assert app; page.upload_csv(); assert len(get_all_events(db)) == 1
    finally: page.close()
def test_events_page_export_csv_writes_file(tmp_path, monkeypatch):
    db = _db(tmp_path); _event(db); path = tmp_path / "events_export"; monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(path), "CSV")); monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None); app = _app(); page = EventsPage(db)
    try:
        assert app; page.export_csv()
        with (tmp_path / "events_export.csv").open("r", encoding="utf-8-sig", newline="") as file: assert list(csv.reader(file))[1][1] == "Open Day"
    finally: page.close()
def test_events_page_save_edits_updates_database(tmp_path):
    db = _db(tmp_path); event_id = _event(db); app = _app(); page = EventsPage(db)
    try: assert app; page.events_table.item(0, 1).setText("Updated Day"); page.save_table_changes(); assert get_event_by_id(event_id, db)["title"] == "Updated Day"
    finally: page.close()
def test_events_page_delete_selected_row_removes_database_row(tmp_path, monkeypatch):
    db = _db(tmp_path); event_id = _event(db); monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes); app = _app(); page = EventsPage(db)
    try: assert app; page.events_table.selectRow(0); page.delete_selected_event(); assert get_event_by_id(event_id, db) is None
    finally: page.close()
def test_events_page_uses_row_numbers_and_internal_ids(tmp_path):
    db = _db(tmp_path); old = _event(db); delete_event(old, db); event_id = _event(db); app = _app(); page = EventsPage(db)
    try: assert app; item = page.events_table.item(0, 0); assert item.text() == "1"; assert item.data(Qt.ItemDataRole.UserRole) == event_id
    finally: page.close()
