"""Top-level window and navigation for the public robot dashboard."""

from PySide6.QtWidgets import QMainWindow, QStackedWidget

from ui.public.screens.home_screen import HomeScreen
from ui.public.screens.placeholder_screen import PlaceholderScreen


class PublicMainWindow(QMainWindow):
    """Host the touch-friendly public experience as a simple page stack."""

    def __init__(self) -> None:
        """Create the home page and the eight public feature placeholders."""
        super().__init__()
        self.setWindowTitle("ECU Robot Assistant")
        self.setObjectName("public_main_window")
        self.setMinimumSize(1280, 800)

        self.public_page_stack = QStackedWidget()
        self.public_page_stack.setObjectName("public_page_stack")
        self.setCentralWidget(self.public_page_stack)
        self.setStyleSheet(
            """
            QMainWindow#public_main_window,
            QStackedWidget#public_page_stack {
                background-color: #07182D;
                border: none;
            }
            """
        )

        self.home_screen = HomeScreen(self)
        self.public_page_stack.addWidget(self.home_screen)

        placeholder_pages = (
            (
                "Campus Map",
                "Room finder and campus navigation will be connected here.",
                "🗺️",
            ),
            (
                "Ask Chatbot",
                "The ECU question-answer assistant will be connected here.",
                "🤖",
            ),
            (
                "University Information",
                "Explore university data and services from one place.",
                "🏛️",
            ),
            (
                "Faculties",
                "Faculty information will be displayed here.",
                "🎓",
            ),
            (
                "Professors",
                "Professor search and office information will be displayed here.",
                "👨‍🏫",
            ),
            (
                "Courses",
                "Course schedules and room details will be displayed here.",
                "📚",
            ),
            (
                "Events",
                "Campus events and important dates will be displayed here.",
                "📅",
            ),
            (
                "FAQ",
                "Common questions and answers will be displayed here.",
                "❓",
            ),
        )
        for title, subtitle, icon in placeholder_pages:
            self.public_page_stack.addWidget(
                PlaceholderScreen(title, subtitle, icon, self)
            )

    def show_home(self) -> None:
        """Return to the public dashboard home screen."""
        self.public_page_stack.setCurrentIndex(0)

    def show_map(self) -> None:
        """Open the Campus Map placeholder."""
        self.public_page_stack.setCurrentIndex(1)

    def show_chatbot(self) -> None:
        """Open the Ask Chatbot placeholder."""
        self.public_page_stack.setCurrentIndex(2)

    def show_university_info(self) -> None:
        """Open the University Information placeholder."""
        self.public_page_stack.setCurrentIndex(3)

    def show_faculties(self) -> None:
        """Open the Faculties placeholder."""
        self.public_page_stack.setCurrentIndex(4)

    def show_professors(self) -> None:
        """Open the Professors placeholder."""
        self.public_page_stack.setCurrentIndex(5)

    def show_courses(self) -> None:
        """Open the Courses placeholder."""
        self.public_page_stack.setCurrentIndex(6)

    def show_events(self) -> None:
        """Open the Events placeholder."""
        self.public_page_stack.setCurrentIndex(7)

    def show_faq(self) -> None:
        """Open the FAQ placeholder."""
        self.public_page_stack.setCurrentIndex(8)
