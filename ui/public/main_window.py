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

        self.home_screen = HomeScreen(self)
        self.public_page_stack.addWidget(self.home_screen)

        placeholder_pages = (
            (
                "Campus Map",
                "Room finder and campus navigation will be connected here.",
                "MAP",
            ),
            (
                "Ask Chatbot",
                "The ECU question-answer assistant will be connected here.",
                "AI",
            ),
            (
                "University Information",
                "Explore university data and services from one place.",
                "ECU",
            ),
            (
                "Faculties",
                "Faculty information will be displayed here.",
                "FAC",
            ),
            (
                "Professors",
                "Professor search and office information will be displayed here.",
                "PROF",
            ),
            (
                "Courses",
                "Course schedules and room details will be displayed here.",
                "COURSE",
            ),
            (
                "Events",
                "Campus events and important dates will be displayed here.",
                "EVENT",
            ),
            (
                "FAQ",
                "Common questions and answers will be displayed here.",
                "FAQ",
            ),
        )
        self.placeholder_screens: list[PlaceholderScreen] = []
        for title, subtitle, icon in placeholder_pages:
            screen = PlaceholderScreen(title, subtitle, icon, self)
            self.placeholder_screens.append(screen)
            self.public_page_stack.addWidget(screen)

        # Apply styles only after every page belongs to the stack. Styling a
        # top-level widget before addWidget() makes Qt recursively re-polish it
        # during reparenting and can stall startup on some font configurations.
        self.setStyleSheet(
            """
            QMainWindow#public_main_window,
            QStackedWidget#public_page_stack {
                background-color: #07182D;
                border: none;
            }
            """
        )
        self.home_screen.apply_styles()
        for screen in self.placeholder_screens:
            screen.apply_styles()

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
