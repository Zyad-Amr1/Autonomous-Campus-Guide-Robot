"""Desktop entry point for the ECU Robot Admin Panel."""

import sys

from PySide6.QtWidgets import QApplication

from ui.admin.login_window import LoginWindow
from ui.admin.main_window import AdminMainWindow


def main() -> None:
    """Start login and transition to the dashboard shell after authentication."""
    application = QApplication(sys.argv)
    login_window = LoginWindow()
    main_window: AdminMainWindow | None = None

    def show_main_window(current_admin: dict) -> None:
        """Open the authenticated shell while retaining its Python reference."""
        nonlocal main_window
        main_window = AdminMainWindow(current_admin)
        main_window.show()
        login_window.close()

    login_window.login_successful.connect(show_main_window)
    login_window.show()
    application.exec()


if __name__ == "__main__":
    main()
