"""Headless tests for the Courses CSV editing workflow."""

import csv, os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from database.init_db import initialize_database
from database.repositories.course_repository import create_course, delete_course, get_all_courses, get_course_by_id
from database.repositories.faculty_repository import create_faculty
from ui.admin.pages.courses_page import CoursesPage


def _app(): return QApplication.instance() or QApplication([])
def _db(tmp_path): path = tmp_path / "test.db"; initialize_database(path); return path
def _course(db):
    faculty = create_faculty("Engineering", db_path=db)
    return faculty, create_course("CS101", "Programming", faculty, None, None, "Monday", "09:00", "10:30", "Fall", db)


def test_courses_page_has_correct_toolbar_buttons(tmp_path):
    app = _app(); page = CoursesPage(_db(tmp_path))
    try: assert app; assert [page.courses_toolbar_layout.itemAt(i).widget().objectName() for i in range(4)] == ["upload_courses_csv_button", "delete_course_button", "export_courses_csv_button", "save_courses_table_button"]
    finally: page.close()
def test_courses_page_visible_columns_match_expected(tmp_path):
    app = _app(); page = CoursesPage(_db(tmp_path))
    try: assert app; assert [page.courses_table.horizontalHeaderItem(i).text() for i in range(10)] == ["No.", "Course Code", "Course Name", "Faculty", "Professor", "Room", "Day", "Start Time", "End Time", "Semester"]
    finally: page.close()
def test_courses_page_upload_csv_automatically_imports_rows(tmp_path, monkeypatch):
    db = _db(tmp_path); faculty = create_faculty("Engineering", db_path=db); path = tmp_path / "courses.csv"
    path.write_text(f"course_code,course_name,faculty_id,professor_id,room_id,schedule_day,start_time,end_time,semester\nCS101,Programming,{faculty},,,Monday,09:00,10:30,Fall\n", encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(path), "CSV")); monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    app = _app(); page = CoursesPage(db)
    try: assert app; page.upload_csv(); assert page.courses_table.rowCount() == 1; assert len(get_all_courses(db)) == 1
    finally: page.close()
def test_courses_page_export_csv_writes_file(tmp_path, monkeypatch):
    db = _db(tmp_path); _course(db); path = tmp_path / "courses_export"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(path), "CSV")); monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    app = _app(); page = CoursesPage(db)
    try:
        assert app; page.export_csv()
        with (tmp_path / "courses_export.csv").open("r", encoding="utf-8-sig", newline="") as file: assert list(csv.reader(file))[1][1] == "CS101"
    finally: page.close()
def test_courses_page_save_edits_updates_database(tmp_path):
    db = _db(tmp_path); _, course_id = _course(db); app = _app(); page = CoursesPage(db)
    try: assert app; page.courses_table.item(0, 2).setText("Advanced Programming"); page.save_table_changes(); assert get_course_by_id(course_id, db)["course_name"] == "Advanced Programming"
    finally: page.close()
def test_courses_page_delete_selected_row_removes_database_row(tmp_path, monkeypatch):
    db = _db(tmp_path); _, course_id = _course(db); monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes); app = _app(); page = CoursesPage(db)
    try: assert app; page.courses_table.selectRow(0); page.delete_selected_course(); assert get_course_by_id(course_id, db) is None
    finally: page.close()
def test_courses_page_uses_row_numbers_and_internal_ids(tmp_path):
    db = _db(tmp_path); faculty = create_faculty("Engineering", db_path=db); old = create_course("OLD", "Old", faculty, None, None, "Monday", "08:00", "09:00", db_path=db); delete_course(old, db); course_id = create_course("CS101", "Programming", faculty, None, None, "Monday", "09:00", "10:30", db_path=db); app = _app(); page = CoursesPage(db)
    try: assert app; item = page.courses_table.item(0, 0); assert item.text() == "1"; assert item.data(Qt.ItemDataRole.UserRole) == course_id
    finally: page.close()
