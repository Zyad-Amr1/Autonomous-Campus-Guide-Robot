"""Desktop entry point for the ECU Robot Admin Panel."""

import sys

from PySide6.QtWidgets import QApplication

from ui.admin.login_window import LoginWindow


def main() -> None:
    """Start the Admin Panel and display its login window."""
    application = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    application.exec()


if __name__ == "__main__":
    main()
