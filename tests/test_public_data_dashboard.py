"""Headless tests for the unified public Data Management screen."""

import os
import sqlite3

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
)

from database.init_db import initialize_database
from controllers.rag.knowledge_store import is_knowledge_dirty, mark_knowledge_dirty
from ui.public.main_window import PublicMainWindow
from ui.public.screens.data_dashboard_screen import DataDashboardScreen


def _get_application() -> QApplication:
    """Return the shared Qt application required to construct widgets."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _create_temp_db(tmp_path):
    """Initialize and return an isolated database path for one test."""
    db_path = tmp_path / "test_ecu_robot.db"
    initialize_database(db_path)
    return db_path


def _insert_faq(db_path) -> None:
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            INSERT INTO faq (question, answer, keywords, category)
            VALUES (?, ?, ?, ?)
            """,
            ("Where is admissions?", "Admissions is in Building A.", "admissions", "services"),
        )
        connection.commit()
    finally:
        connection.close()


def test_data_dashboard_screen_can_be_created(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        assert screen.objectName() == "data_dashboard_screen"
    finally:
        screen.close()


def test_required_widgets_exist(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        for object_name, widget_type in (
            ("data_dataset_selector", QComboBox),
            ("data_table", QTableWidget),
            ("data_status_label", QLabel),
            ("data_upload_csv_button", QPushButton),
            ("data_delete_row_button", QPushButton),
            ("data_export_csv_button", QPushButton),
            ("data_save_edits_button", QPushButton),
            ("kb_sync_database_button", QPushButton),
            ("kb_sync_external_button", QPushButton),
            ("kb_rebuild_all_button", QPushButton),
            ("kb_status_button", QPushButton),
            ("kb_status_label", QLabel),
            ("chatbot_eval_button", QPushButton),
            ("chatbot_debug_status_button", QPushButton),
            ("chatbot_eval_status_label", QLabel),
            ("kb_source_name_input", QLineEdit),
            ("kb_source_url_input", QLineEdit),
            ("kb_add_source_button", QPushButton),
            ("kb_remove_source_button", QPushButton),
            ("kb_toggle_source_button", QPushButton),
            ("kb_sources_table", QTableWidget),
            ("kb_upload_document_button", QPushButton),
            ("kb_open_documents_folder_button", QPushButton),
        ):
            assert screen.findChild(widget_type, object_name) is not None
    finally:
        screen.close()


def test_dataset_selector_contains_required_datasets(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        selector = screen.data_dataset_selector
        assert [selector.itemText(index) for index in range(selector.count())] == [
            "Faculties",
            "Rooms",
            "Professors",
            "Courses",
            "Events",
            "FAQ",
        ]
    finally:
        screen.close()


def test_selecting_each_dataset_loads_table_without_crashing(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        for dataset in ("Faculties", "Rooms", "Professors", "Courses", "Events", "FAQ"):
            screen.data_dataset_selector.setCurrentText(dataset)
            screen.load_selected_dataset()
            assert screen.data_table.columnCount() >= 1
    finally:
        screen.close()


def test_action_buttons_exist_in_required_order(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        buttons = (
            screen.data_upload_csv_button,
            screen.data_delete_row_button,
            screen.data_export_csv_button,
            screen.data_save_edits_button,
        )
        assert [button.text() for button in buttons] == [
            "Upload CSV",
            "Delete Selected Row",
            "Export CSV",
            "Save Edits",
        ]
    finally:
        screen.close()


def test_knowledge_base_buttons_exist(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        assert screen.kb_sync_database_button.text() == "Sync Database Knowledge"
        assert screen.kb_sync_external_button.text() == "Sync Website/Documents"
        assert screen.kb_rebuild_all_button.text() == "Rebuild All Knowledge"
        assert screen.kb_status_button.text() == "Knowledge Status"
    finally:
        screen.close()


def test_sync_database_button_calls_sync_function(tmp_path, monkeypatch) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    calls = []

    def fake_sync(path):
        calls.append(path)
        return {"chunks_created": 7}

    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.sync_database_to_knowledge_base",
        fake_sync,
    )
    screen = DataDashboardScreen(db_path=db_path)
    try:
        assert application is not None
        screen.kb_sync_database_button.click()
        assert calls == [db_path]
        assert "Synced 7 database" in screen.kb_status_label.text()
    finally:
        screen.close()


def test_sync_external_button_calls_sync_function(tmp_path, monkeypatch) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    calls = []

    def fake_sync(path, sources_root):
        calls.append((path, sources_root))
        return {"website_chunks": 2, "document_chunks": 3, "errors": []}

    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.sync_external_sources_to_knowledge_base",
        fake_sync,
    )
    screen = DataDashboardScreen(db_path=db_path)
    try:
        assert application is not None
        screen.kb_sync_external_button.click()
        assert calls == [(db_path, screen.sources_root)]
        assert "Website chunks: 2" in screen.kb_status_label.text()
        assert "Document chunks: 3" in screen.kb_status_label.text()
    finally:
        screen.close()


def test_knowledge_status_label_updates(tmp_path, monkeypatch) -> None:
    application = _get_application()

    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.get_knowledge_status_summary",
        lambda db_path: {
            "dirty": False,
            "dirty_reason": "",
            "last_database_sync": "",
            "last_external_sync": "",
            "chunk_count": 3,
            "sources": {"faq": 2, "website": 1},
        },
    )
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        screen.kb_status_button.click()
        assert "3 chunks" in screen.kb_status_label.text()
        assert "faq: 2" in screen.kb_status_label.text()
        assert "website: 1" in screen.kb_status_label.text()
    finally:
        screen.close()


def test_knowledge_sync_failure_does_not_crash(tmp_path, monkeypatch) -> None:
    application = _get_application()

    def failing_sync(_path):
        raise RuntimeError("sync failed")

    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.sync_database_to_knowledge_base",
        failing_sync,
    )
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        screen.kb_sync_database_button.click()
        assert "Could not sync database knowledge" in screen.kb_status_label.text()
    finally:
        screen.close()


def test_source_manager_widgets_exist(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        assert screen.kb_add_source_button.text() == "Add Website Source"
        assert screen.kb_remove_source_button.text() == "Remove Selected Source"
        assert screen.kb_toggle_source_button.text() == "Enable/Disable Selected Source"
        assert screen.kb_upload_document_button.text() == "Upload Document"
        assert screen.kb_open_documents_folder_button.text() == "Open Documents Folder"
    finally:
        screen.close()


def test_add_source_updates_table_and_status(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        screen.kb_source_name_input.setText("ECU")
        screen.kb_source_url_input.setText("https://example.edu")
        screen.kb_add_source_button.click()
        assert screen.kb_sources_table.rowCount() == 1
        assert screen.kb_sources_table.item(0, 0).text() == "ECU"
        assert "Added website source" in screen.kb_status_label.text()
    finally:
        screen.close()


def test_remove_selected_source_updates_table_and_status(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        screen.kb_source_name_input.setText("ECU")
        screen.kb_source_url_input.setText("https://example.edu")
        screen.kb_add_source_button.click()
        screen.kb_sources_table.selectRow(0)
        screen.kb_remove_source_button.click()
        assert screen.kb_sources_table.rowCount() == 0
        assert "Removed selected source" in screen.kb_status_label.text()
    finally:
        screen.close()


def test_toggle_selected_source_updates_enabled_state(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        screen.kb_source_name_input.setText("ECU")
        screen.kb_source_url_input.setText("https://example.edu")
        screen.kb_add_source_button.click()
        screen.kb_sources_table.selectRow(0)
        screen.kb_toggle_source_button.click()
        assert screen.kb_sources_table.item(0, 2).text() == "No"
        screen.kb_sources_table.selectRow(0)
        screen.kb_toggle_source_button.click()
        assert screen.kb_sources_table.item(0, 2).text() == "Yes"
    finally:
        screen.close()


def test_upload_document_copies_file(tmp_path, monkeypatch) -> None:
    application = _get_application()
    source_file = tmp_path / "source.txt"
    source_file.write_text("Document text", encoding="utf-8")
    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: (str(source_file), ""),
    )
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        screen.kb_upload_document_button.click()
        assert (screen.documents_folder / "source.txt").exists()
        assert "Uploaded document" in screen.kb_status_label.text()
    finally:
        screen.close()


def test_csv_upload_marks_knowledge_dirty(tmp_path, monkeypatch) -> None:
    application = _get_application()
    csv_file = tmp_path / "faq.csv"
    csv_file.write_text("question,answer\nQ,A\n", encoding="utf-8")
    db_path = _create_temp_db(tmp_path)

    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: (str(csv_file), ""),
    )

    def fake_importer(path, database_path):
        assert path == str(csv_file)
        assert database_path == db_path
        return {"imported": 1, "skipped": 0}

    monkeypatch.setitem(
        __import__("ui.public.screens.data_dashboard_screen", fromlist=["DATASETS"]).DATASETS["FAQ"],
        "importer",
        fake_importer,
    )
    screen = DataDashboardScreen(db_path=db_path)
    try:
        assert application is not None
        screen.data_dataset_selector.setCurrentText("FAQ")
        screen.data_upload_csv_button.click()
        assert is_knowledge_dirty(db_path) is True
    finally:
        screen.close()


def test_save_edits_marks_knowledge_dirty(tmp_path) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    _insert_faq(db_path)
    screen = DataDashboardScreen(db_path=db_path)
    try:
        assert application is not None
        screen.data_dataset_selector.setCurrentText("FAQ")
        screen.load_selected_dataset()
        screen.data_table.item(0, 2).setText("Admissions is near the main gate.")
        screen.data_save_edits_button.click()
        assert is_knowledge_dirty(db_path) is True
    finally:
        screen.close()


def test_delete_row_marks_knowledge_dirty(tmp_path, monkeypatch) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    _insert_faq(db_path)
    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    screen = DataDashboardScreen(db_path=db_path)
    try:
        assert application is not None
        screen.data_dataset_selector.setCurrentText("FAQ")
        screen.load_selected_dataset()
        screen.data_table.selectRow(0)
        screen.data_delete_row_button.click()
        assert is_knowledge_dirty(db_path) is True
    finally:
        screen.close()


def test_source_changes_mark_knowledge_dirty(tmp_path) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    screen = DataDashboardScreen(db_path=db_path)
    try:
        assert application is not None
        screen.kb_source_name_input.setText("ECU")
        screen.kb_source_url_input.setText("https://example.edu")
        screen.kb_add_source_button.click()
        assert is_knowledge_dirty(db_path) is True
    finally:
        screen.close()


def test_upload_document_marks_knowledge_dirty(tmp_path, monkeypatch) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    source_file = tmp_path / "source.txt"
    source_file.write_text("Document text", encoding="utf-8")
    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: (str(source_file), ""),
    )
    screen = DataDashboardScreen(db_path=db_path)
    try:
        assert application is not None
        screen.kb_upload_document_button.click()
        assert is_knowledge_dirty(db_path) is True
    finally:
        screen.close()


def test_rebuild_all_clears_dirty_after_success(tmp_path, monkeypatch) -> None:
    application = _get_application()
    db_path = _create_temp_db(tmp_path)
    mark_knowledge_dirty(db_path, "Courses data changed")

    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.sync_database_to_knowledge_base",
        lambda path: {"chunks_created": 3},
    )
    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.sync_external_sources_to_knowledge_base",
        lambda path, sources_root: {"website_chunks": 1, "document_chunks": 2, "errors": []},
    )
    screen = DataDashboardScreen(db_path=db_path)
    try:
        assert application is not None
        screen.kb_rebuild_all_button.click()
        assert is_knowledge_dirty(db_path) is False
        assert "Rebuilt knowledge base" in screen.kb_status_label.text()
    finally:
        screen.close()


def test_knowledge_status_shows_dirty_and_sync_metadata(tmp_path, monkeypatch) -> None:
    application = _get_application()
    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.get_knowledge_status_summary",
        lambda db_path: {
            "dirty": True,
            "dirty_reason": "Courses data changed",
            "last_database_sync": "2026-06-29T10:00:00+00:00",
            "last_external_sync": "",
            "chunk_count": 12,
            "sources": {"courses": 4, "website": 8},
        },
    )
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        screen.kb_status_button.click()
        text = screen.kb_status_label.text()
        assert "Knowledge Base: 12 chunks" in text
        assert "Status: Outdated" in text
        assert "Reason: Courses data changed" in text
        assert "courses: 4" in text
        assert "Last database sync: 2026-06-29" in text
    finally:
        screen.close()


def test_sync_external_updates_status_safely(tmp_path, monkeypatch) -> None:
    application = _get_application()

    def fake_sync(path, sources_root="knowledge_sources"):
        return {"website_chunks": 4, "document_chunks": 2, "errors": ["one"]}

    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.sync_external_sources_to_knowledge_base",
        fake_sync,
    )
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        screen.kb_sync_external_button.click()
        assert "Website chunks: 4" in screen.kb_status_label.text()
        assert "Document chunks: 2" in screen.kb_status_label.text()
        assert "Errors: 1" in screen.kb_status_label.text()
    finally:
        screen.close()


def test_sync_external_failure_does_not_crash(tmp_path, monkeypatch) -> None:
    application = _get_application()

    def failing_sync(path, sources_root="knowledge_sources"):
        raise RuntimeError("network unavailable")

    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.sync_external_sources_to_knowledge_base",
        failing_sync,
    )
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        screen.kb_sync_external_button.click()
        assert "Could not sync website/documents" in screen.kb_status_label.text()
    finally:
        screen.close()


def test_chatbot_evaluation_buttons_exist(tmp_path) -> None:
    application = _get_application()
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        assert screen.chatbot_eval_button.text() == "Run Chatbot Evaluation"
        assert screen.chatbot_debug_status_button.text() == "Show RAG Debug Status"
    finally:
        screen.close()


def test_chatbot_evaluation_status_label_updates(tmp_path, monkeypatch) -> None:
    application = _get_application()

    def fake_evaluator(_controller):
        return {"total": 3, "passed": 2, "failed": 1, "results": []}

    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.run_chatbot_evaluation",
        fake_evaluator,
    )
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        screen.chatbot_eval_button.click()
        assert screen.chatbot_eval_status_label.text() == "Evaluation: 2/3 passed"
    finally:
        screen.close()


def test_chatbot_evaluator_failure_does_not_crash(tmp_path, monkeypatch) -> None:
    application = _get_application()

    def failing_evaluator(_controller):
        raise RuntimeError("evaluation failed")

    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.run_chatbot_evaluation",
        failing_evaluator,
    )
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        screen.chatbot_eval_button.click()
        assert "Could not run chatbot evaluation" in screen.chatbot_eval_status_label.text()
    finally:
        screen.close()


def test_rag_debug_status_button_updates_label(tmp_path, monkeypatch) -> None:
    application = _get_application()
    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.load_knowledge_chunks",
        lambda db_path: [
            {"source": "faq", "title": "One"},
            {"source": "website", "title": "Two"},
        ],
    )
    monkeypatch.setattr(
        "ui.public.screens.data_dashboard_screen.load_groq_config",
        lambda: {"api_key": "test", "model": "test"},
    )
    screen = DataDashboardScreen(db_path=_create_temp_db(tmp_path))
    try:
        assert application is not None
        screen.chatbot_debug_status_button.click()
        text = screen.chatbot_eval_status_label.text()
        assert "2 chunk" in text
        assert "Groq key detected: yes" in text
        assert "faq" in text
    finally:
        screen.close()


def test_admin_gate_correct_password_switches_to_data_dashboard() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.show_data()
        window.admin_gate_screen.admin_password_input.setText("admin123")
        window.admin_gate_screen.admin_unlock_button.click()
        assert window.public_page_stack.currentWidget() is window.data_dashboard_screen
    finally:
        window.close()


def test_public_navigation_still_works_after_adding_data_dashboard() -> None:
    application = _get_application()
    window = PublicMainWindow()
    try:
        assert application is not None
        window.show_data_dashboard()
        assert window.public_page_stack.currentWidget() is window.data_dashboard_screen
        window.sidebar_map_button.click()
        assert window.public_page_stack.currentWidget() is window.map_screen
        window.sidebar_home_button.click()
        assert window.public_page_stack.currentWidget() is window.home_screen
        window.floating_ask_button.click()
        assert window.public_page_stack.currentWidget() is window.chat_screen
    finally:
        window.close()
