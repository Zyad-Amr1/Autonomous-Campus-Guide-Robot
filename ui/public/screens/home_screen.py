"""Modern touch-first home screen for the ECU robot assistant."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class HomeScreen(QWidget):
    """Present the three primary robot tasks and smaller quick actions."""

    def __init__(self, parent_window=None) -> None:
        """Build the kiosk home screen and connect available navigation."""
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("public_home_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        if parent_window is None:
            self.apply_styles()

    def _build_ui(self) -> None:
        """Arrange the branded header, hero, feature cards, and footer."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(54, 34, 54, 28)
        page_layout.setSpacing(24)

        header_layout = QHBoxLayout()
        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(2)
        brand_label = QLabel("ECU ROBOT ASSISTANT")
        brand_label.setObjectName("public_brand_label")
        university_label = QLabel("Egyptian Chinese University")
        university_label.setObjectName("public_university_label")
        brand_layout.addWidget(brand_label)
        brand_layout.addWidget(university_label)
        touchscreen_badge = QLabel("TOUCHSCREEN GUIDE")
        touchscreen_badge.setObjectName("touchscreen_badge")
        touchscreen_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addLayout(brand_layout)
        header_layout.addStretch()
        header_layout.addWidget(touchscreen_badge)
        page_layout.addLayout(header_layout)

        hero_layout = QVBoxLayout()
        hero_layout.setSpacing(7)
        self.public_home_title = QLabel("How can I help you today?")
        self.public_home_title.setObjectName("public_home_title")
        self.public_home_subtitle = QLabel(
            "Use the campus map, ask the robot chatbot, or explore university "
            "information."
        )
        self.public_home_subtitle.setObjectName("public_home_subtitle")
        guide_label = QLabel("Your smart guide inside ECU.")
        guide_label.setObjectName("public_guide_label")
        hero_layout.addWidget(self.public_home_title)
        hero_layout.addWidget(self.public_home_subtitle)
        hero_layout.addWidget(guide_label)
        page_layout.addLayout(hero_layout)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(22)
        map_card, self.map_button = self._create_main_card(
            "MAP",
            "Campus Map",
            "Find rooms, buildings, offices, and important places.",
            "Open Map",
            "map_button",
            "show_map",
        )
        chatbot_card, self.chatbot_button = self._create_main_card(
            "AI",
            "Ask Chatbot",
            "Ask about ECU, admissions, schedules, services, and more.",
            "Ask Now",
            "chatbot_button",
            "show_chatbot",
        )
        info_card, self.university_info_button = self._create_main_card(
            "ECU",
            "University Info",
            "Browse faculties, professors, courses, events, and FAQs.",
            "Explore Info",
            "university_info_button",
            "show_university_info",
        )
        cards_layout.addWidget(map_card)
        cards_layout.addWidget(chatbot_card)
        cards_layout.addWidget(info_card)
        page_layout.addLayout(cards_layout, stretch=1)

        quick_section = QVBoxLayout()
        quick_section.setSpacing(12)
        quick_title = QLabel("QUICK ACCESS")
        quick_title.setObjectName("quick_access_title")
        quick_section.addWidget(quick_title)
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(12)
        quick_actions = (
            ("Faculties", "faculties_quick_button", "show_faculties"),
            ("Professors", "professors_quick_button", "show_professors"),
            ("Courses", "courses_quick_button", "show_courses"),
            ("Events", "events_quick_button", "show_events"),
            ("FAQ", "faq_quick_button", "show_faq"),
        )
        for text, object_name, method_name in quick_actions:
            button = QPushButton(text)
            button.setObjectName(object_name)
            button.setProperty("buttonRole", "quick")
            button.setMinimumHeight(50)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            self._connect_navigation(button, method_name)
            setattr(self, object_name, button)
            quick_layout.addWidget(button)
        quick_section.addLayout(quick_layout)
        page_layout.addLayout(quick_section)

        footer = QLabel("Powered by ECU Guidance Robot")
        footer.setObjectName("public_footer_label")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(footer)

    def _create_main_card(
        self,
        icon: str,
        title: str,
        description: str,
        button_text: str,
        button_name: str,
        method_name: str,
    ) -> tuple[QFrame, QPushButton]:
        """Create one visually dominant primary action card."""
        card = QFrame()
        card.setObjectName("primary_topic_card")
        card.setMinimumHeight(300)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 25, 30, 26)
        card_layout.setSpacing(12)

        icon_label = QLabel(icon)
        icon_label.setObjectName("topic_icon_label")
        icon_label.setFixedSize(72, 52)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label = QLabel(title)
        title_label.setObjectName("topic_title_label")
        description_label = QLabel(description)
        description_label.setObjectName("topic_description_label")
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        button = QPushButton(button_text)
        button.setObjectName(button_name)
        button.setProperty("buttonRole", "primary")
        button.setMinimumHeight(58)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._connect_navigation(button, method_name)

        card_layout.addWidget(icon_label)
        card_layout.addWidget(title_label)
        card_layout.addWidget(description_label, stretch=1)
        card_layout.addWidget(button)
        return card, button

    def _connect_navigation(self, button: QPushButton, method_name: str) -> None:
        """Connect a button only when its optional host supports navigation."""
        callback: Callable | None = getattr(
            self.parent_window,
            method_name,
            None,
        )
        if callback is not None:
            button.clicked.connect(callback)

    def apply_styles(self) -> None:
        """Apply the distinct navy, gold, and glass-inspired kiosk theme."""
        self.setStyleSheet(
            """
            QWidget#public_home_screen {
                background-color: #07182D;
                color: #FFFFFF;
                font-family: "Segoe UI", Arial, sans-serif;
            }

            QLabel#public_brand_label {
                color: #F6C85F;
                font-size: 21px;
                font-weight: 800;
                letter-spacing: 2px;
            }

            QLabel#public_university_label {
                color: #A9BCD2;
                font-size: 13px;
            }

            QLabel#touchscreen_badge {
                background-color: rgba(246, 200, 95, 0.14);
                color: #F6C85F;
                border: 1px solid rgba(246, 200, 95, 0.55);
                border-radius: 17px;
                padding: 8px 17px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            QLabel#public_home_title {
                color: #FFFFFF;
                font-size: 36px;
                font-weight: 800;
            }

            QLabel#public_home_subtitle {
                color: #C7D7E8;
                font-size: 16px;
            }

            QLabel#public_guide_label {
                color: #F6C85F;
                font-size: 13px;
                font-weight: 600;
            }

            QFrame#primary_topic_card {
                background-color: #102A46;
                border: 1px solid #294967;
                border-radius: 24px;
            }

            QLabel#topic_icon_label {
                background-color: #F6C85F;
                color: #10233A;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 800;
            }

            QLabel#topic_title_label {
                color: #FFFFFF;
                font-size: 24px;
                font-weight: 750;
            }

            QLabel#topic_description_label {
                color: #BFD0E0;
                font-size: 15px;
            }

            QPushButton[buttonRole="primary"] {
                background-color: #F6C85F;
                color: #10233A;
                border: none;
                border-radius: 14px;
                padding: 0 22px;
                font-size: 16px;
                font-weight: 800;
            }

            QPushButton[buttonRole="primary"]:hover {
                background-color: #FFE092;
            }

            QPushButton[buttonRole="primary"]:pressed {
                background-color: #E5B84E;
            }

            QLabel#quick_access_title {
                color: #829AB4;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 2px;
            }

            QPushButton[buttonRole="quick"] {
                background-color: #153554;
                color: #E9F1F8;
                border: 1px solid #315371;
                border-radius: 14px;
                padding: 0 18px;
                font-size: 14px;
                font-weight: 650;
            }

            QPushButton[buttonRole="quick"]:hover {
                background-color: #1C466D;
                border-color: #F6C85F;
                color: #FFFFFF;
            }

            QLabel#public_footer_label {
                color: #6F88A3;
                font-size: 11px;
                padding-top: 2px;
            }
            """
        )
