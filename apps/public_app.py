"""Desktop entry point for the ECU Smart Assistant public dashboard."""

import sys

from PySide6.QtWidgets import QApplication

from ui.public.main_window import PublicMainWindow


def main() -> None:
    """Start the standalone public robot dashboard shell."""
    application = QApplication(sys.argv)
    application.setApplicationName("ECU Smart Assistant")
    window = PublicMainWindow()
    window.show()
    application.exec()


if __name__ == "__main__":
    main()
