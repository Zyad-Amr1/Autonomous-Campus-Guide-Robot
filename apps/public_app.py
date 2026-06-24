"""Desktop entry point for the ECU Robot Public Assistant."""

import sys

from PySide6.QtWidgets import QApplication

from ui.public.main_window import PublicMainWindow


def main() -> None:
    """Start the standalone public robot dashboard."""
    application = QApplication(sys.argv)
    application.setApplicationName("ECU Robot Assistant")
    window = PublicMainWindow()
    window.show()
    application.exec()


if __name__ == "__main__":
    main()
