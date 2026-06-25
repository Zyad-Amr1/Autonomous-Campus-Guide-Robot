"""Public campus map route simulation screen."""

from heapq import heappop, heappush
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QCompleter,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.public.theme import (
    CARD_PADDING,
    CARD_RADIUS,
    GOLD,
    GOLD_LIGHT,
    NAVY,
    NAVY_DARK,
    NAVY_LIGHT,
    OFF_WHITE,
    PAGE_PADDING,
    TEXT_DARK,
    TEXT_MUTED,
    TOUCH_BUTTON_HEIGHT,
    WHITE,
    font,
    px,
)


LANDMARKS = {
    "Building A": (555, 515),
    "Building B": (455, 765),
    "Building C": (280, 705),
    "Building D": (305, 555),
    "Building E": (480, 205),
    "Cafeteria": (310, 395),
    "Parking": (505, 60),
    "Stadium": (840, 230),
    "Workshop 1": (95, 675),
    "Workshop 2": (285, 280),
    "Boys’ Musallah": (760, 585),
    "Girls’ Musallah": (790, 420),
    "Sports Activity": (775, 510),
}

LANDMARK_DETAILS = {
    "Building A": (
        "Academic Building",
        "Main academic block near the central campus path.",
    ),
    "Building B": (
        "Academic Building",
        "Teaching building connected to the southern walkway.",
    ),
    "Building C": (
        "Academic Building",
        "Classroom building beside the west campus route.",
    ),
    "Building D": (
        "Academic Building",
        "Academic block close to the cafeteria connector path.",
    ),
    "Building E": (
        "Academic Building",
        "Northern academic building near the main parking approach.",
    ),
    "Cafeteria": (
        "Student Services",
        "Food and student break area in the middle of campus.",
    ),
    "Parking": (
        "Campus Access",
        "Main parking area and common starting point for visitors.",
    ),
    "Stadium": (
        "Sports",
        "Outdoor sports venue on the east side of campus.",
    ),
    "Workshop 1": (
        "Workshop",
        "Hands-on workshop area near the west side buildings.",
    ),
    "Workshop 2": (
        "Workshop",
        "Workshop space connected to the cafeteria route.",
    ),
    "Boys’ Musallah": (
        "Prayer Area",
        "Prayer space for boys near the eastern campus path.",
    ),
    "Girls’ Musallah": (
        "Prayer Area",
        "Prayer space for girls near the sports activity area.",
    ),
    "Boysâ€™ Musallah": (
        "Prayer Area",
        "Prayer space for boys near the eastern campus path.",
    ),
    "Girlsâ€™ Musallah": (
        "Prayer Area",
        "Prayer space for girls near the sports activity area.",
    ),
    "Sports Activity": (
        "Sports",
        "Student sports activity area beside the east walkway.",
    ),
}

WALKING_GRAPH = {
    "Parking": ("Building E", "Stadium"),
    "Building E": ("Parking", "Workshop 2", "Building A"),
    "Workshop 2": ("Building E", "Cafeteria", "Building D"),
    "Cafeteria": ("Workshop 2", "Building D", "Building A"),
    "Building D": ("Workshop 2", "Cafeteria", "Building C", "Building A"),
    "Building C": ("Workshop 1", "Building D", "Building B"),
    "Workshop 1": ("Building C",),
    "Building B": ("Building C", "Building A"),
    "Building A": (
        "Building E",
        "Cafeteria",
        "Building D",
        "Building B",
        "Girls’ Musallah",
        "Sports Activity",
    ),
    "Girls’ Musallah": ("Building A", "Stadium", "Sports Activity"),
    "Sports Activity": ("Building A", "Girls’ Musallah", "Boys’ Musallah"),
    "Boys’ Musallah": ("Sports Activity", "Stadium"),
    "Stadium": ("Parking", "Girls’ Musallah", "Boys’ Musallah"),
}


class MapCanvas(QWidget):
    """Display the ECU campus map image plus simulated route overlays."""

    IMPORTANT_LABELS = {
        "Building A",
        "Building B",
        "Building C",
        "Building D",
        "Building E",
        "Cafeteria",
        "Stadium",
    }

    def __init__(self, background_image_path: str | None = None) -> None:
        """Create an image-ready map canvas."""
        super().__init__()
        self.setObjectName("map_canvas")
        self.setMinimumSize(620, 440)
        self.background_image_path: str | None = None
        self._background_pixmap = QPixmap()
        self.landmarks = LANDMARKS.copy()
        self.current_route: list[str] = []
        self.route_start: str | None = None
        self.route_destination: str | None = None
        self.walking_progress: float | None = None
        self.selected_landmark: str | None = None
        self.landmark_clicked = None
        self._image_target_rect = QRectF()
        self._marker_hit_radius = 18
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        if background_image_path is not None:
            self.set_background_image(background_image_path)

    def set_background_image(self, path: str) -> None:
        """Set a campus map image path and repaint the canvas."""
        self.background_image_path = path
        image_path = Path(path)
        self._background_pixmap = (
            QPixmap(str(image_path)) if image_path.exists() else QPixmap()
        )
        self.update()

    def set_route(self, route: list[str], start: str, destination: str) -> None:
        """Store and draw a selected walking route."""
        self.current_route = route
        self.route_start = start
        self.route_destination = destination
        self.walking_progress = None
        self.update()

    def clear_route(self) -> None:
        """Clear route overlays and selected endpoints."""
        self.current_route = []
        self.route_start = None
        self.route_destination = None
        self.walking_progress = None
        self.update()

    def set_walking_progress(self, progress: float | None) -> None:
        """Set the animated walking dot position along the route."""
        if progress is None:
            self.walking_progress = None
        else:
            self.walking_progress = min(1.0, max(0.0, progress))
        self.update()

    def select_landmark(self, landmark: str) -> None:
        """Highlight a landmark marker on the canvas."""
        if landmark not in self.landmarks:
            return
        self.selected_landmark = landmark
        self.update()

    def clear_selection(self) -> None:
        """Clear the selected landmark marker highlight."""
        self.selected_landmark = None
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint the map image, route, and hardcoded landmarks."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        canvas_rect = QRectF(self.rect().adjusted(16, 16, -16, -16))
        painter.setPen(QPen(QColor("#D8D2C5"), 1))
        painter.setBrush(QColor("#ECE8DC"))
        painter.drawRoundedRect(canvas_rect, 24, 24)

        if self._background_pixmap.isNull():
            self._image_target_rect = canvas_rect
            self._draw_missing_image_message(painter, canvas_rect)
        else:
            self._draw_background_image(painter, canvas_rect)

        self._draw_route(painter)
        self._draw_landmarks(painter)
        self._draw_walker(painter)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        """Select a landmark when a user taps near its marker."""
        for name in reversed(list(self.landmarks)):
            center = self._point_for_landmark(name)
            delta = center - event.position()
            if (
                delta.x() * delta.x() + delta.y() * delta.y()
                <= self._marker_hit_radius * self._marker_hit_radius
            ):
                self.select_landmark(name)
                if self.landmark_clicked is not None:
                    self.landmark_clicked(name)
                return
        super().mousePressEvent(event)

    def _draw_background_image(self, painter: QPainter, rect: QRectF) -> None:
        """Draw the real campus map image scaled with aspect ratio preserved."""
        scaled = self._background_pixmap.scaled(
            rect.size().toSize(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        target_x = rect.x() + (rect.width() - scaled.width()) / 2
        target_y = rect.y() + (rect.height() - scaled.height()) / 2
        self._image_target_rect = QRectF(target_x, target_y, scaled.width(), scaled.height())
        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, 24, 24)
        painter.save()
        painter.setClipPath(clip_path)
        painter.drawPixmap(int(target_x), int(target_y), scaled)
        painter.restore()

    def _draw_missing_image_message(self, painter: QPainter, rect: QRectF) -> None:
        """Draw a friendly placeholder when the map image is unavailable."""
        painter.setPen(QPen(QColor("#D8D2C5"), 2, Qt.PenStyle.DashLine))
        painter.setBrush(QColor("#F1EEE7"))
        painter.drawRoundedRect(rect.adjusted(18, 18, -18, -18), 22, 22)
        painter.setPen(QColor(TEXT_MUTED))
        painter.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        painter.drawText(
            rect,
            Qt.AlignmentFlag.AlignCenter,
            "Campus map image not found.",
        )

    def _draw_route(self, painter: QPainter) -> None:
        """Draw the current route as a gold walking polyline."""
        if len(self.current_route) < 2:
            return
        path = QPainterPath(self._point_for_landmark(self.current_route[0]))
        for landmark in self.current_route[1:]:
            path.lineTo(self._point_for_landmark(landmark))
        painter.setPen(
            QPen(
                QColor(GOLD),
                7,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.drawPath(path)
        painter.setPen(
            QPen(
                QColor(WHITE),
                2,
                Qt.PenStyle.DashLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        painter.drawPath(path)

    def _draw_landmarks(self, painter: QPainter) -> None:
        """Draw all campus landmark markers and key labels."""
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        for name in self.landmarks:
            center = self._point_for_landmark(name)
            color = QColor(NAVY_LIGHT)
            radius = 10
            if name == self.route_start:
                color = QColor("#22A06B")
                radius = 15
            elif name == self.route_destination:
                color = QColor("#D94D45")
                radius = 15
            elif name == self.selected_landmark:
                color = QColor(GOLD)
                radius = 13

            painter.setPen(QPen(QColor(WHITE), 3))
            painter.setBrush(color)
            painter.drawEllipse(center, radius, radius)

            if name in self.IMPORTANT_LABELS or name in (self.route_start, self.route_destination):
                label_rect = QRectF(center.x() + 12, center.y() - 13, 122, 26)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 255, 255, 218))
                painter.drawRoundedRect(label_rect, 8, 8)
                painter.setPen(QColor(TEXT_DARK))
                painter.drawText(
                    label_rect.adjusted(7, 0, -7, 0),
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                    name,
                )

    def _draw_walker(self, painter: QPainter) -> None:
        """Draw the animated walking position on top of the route."""
        if self.walking_progress is None or len(self.current_route) < 2:
            return

        position = self._point_for_route_progress(self.walking_progress)
        painter.setPen(QPen(QColor(WHITE), 5))
        painter.setBrush(QColor(NAVY_DARK))
        painter.drawEllipse(position, 13, 13)
        painter.setPen(QPen(QColor(GOLD), 3))
        painter.setBrush(QColor(WHITE))
        painter.drawEllipse(position, 7, 7)

    def _point_for_landmark(self, name: str) -> QPointF:
        """Convert 0-1000 normalized coordinates into canvas points."""
        x_value, y_value = self.landmarks[name]
        rect = self._image_target_rect if self._image_target_rect.isValid() else QRectF(self.rect().adjusted(16, 16, -16, -16))
        return QPointF(
            rect.left() + rect.width() * (x_value / 1000),
            rect.top() + rect.height() * (y_value / 1000),
        )

    def _point_for_route_progress(self, progress: float) -> QPointF:
        """Return the canvas point at a normalized progress along the route."""
        route_points = [self._point_for_landmark(name) for name in self.current_route]
        segment_lengths: list[float] = []
        total_length = 0.0
        for index in range(len(route_points) - 1):
            first = route_points[index]
            second = route_points[index + 1]
            length = ((second.x() - first.x()) ** 2 + (second.y() - first.y()) ** 2) ** 0.5
            segment_lengths.append(length)
            total_length += length

        if total_length <= 0:
            return route_points[0]

        target_length = total_length * min(1.0, max(0.0, progress))
        traveled = 0.0
        for index, segment_length in enumerate(segment_lengths):
            if traveled + segment_length >= target_length:
                segment_progress = (target_length - traveled) / segment_length
                first = route_points[index]
                second = route_points[index + 1]
                return QPointF(
                    first.x() + (second.x() - first.x()) * segment_progress,
                    first.y() + (second.y() - first.y()) * segment_progress,
                )
            traveled += segment_length
        return route_points[-1]


class MapScreen(QWidget):
    """Display hardcoded campus walking navigation over the ECU map."""

    MAP_IMAGE_PATH = "assets/maps/ecu_campus_map.png"

    def __init__(self, map_image_path: str | None = None) -> None:
        """Create the route simulation map screen."""
        super().__init__()
        self.map_image_path = map_image_path or self.MAP_IMAGE_PATH
        self.landmarks = LANDMARKS.copy()
        self.walking_graph = {key: tuple(value) for key, value in WALKING_GRAPH.items()}
        self.current_route: list[str] = []
        self.selected_landmark: str | None = None
        self.walking_progress = 0.0
        self.is_walking = False
        self.walk_timer = QTimer(self)
        self.walk_timer.setInterval(120)
        self.walk_timer.timeout.connect(self._advance_walk)
        self.setObjectName("map_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        """Arrange route controls, map canvas, and info panel."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(PAGE_PADDING + 8, PAGE_PADDING, PAGE_PADDING + 8, PAGE_PADDING)
        page_layout.setSpacing(16)

        self.map_title = QLabel("Campus Map")
        self.map_title.setObjectName("map_title")
        self.map_subtitle = QLabel("Choose where you are and where you want to go.")
        self.map_subtitle.setObjectName("map_subtitle")
        self.map_subtitle.setWordWrap(True)
        self.placeholder_title_label = QLabel("Campus Map", self)
        self.placeholder_title_label.setObjectName("placeholder_title_label")
        self.placeholder_title_label.hide()
        page_layout.addWidget(self.map_title)
        page_layout.addWidget(self.map_subtitle)

        search_panel = QFrame()
        search_panel.setObjectName("map_search_panel")
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(16, 14, 16, 14)
        search_layout.setSpacing(12)

        self.map_search_input = QLineEdit()
        self.map_search_input.setObjectName("map_search_input")
        self.map_search_input.setPlaceholderText("Search landmarks")
        self.map_search_input.setMinimumHeight(TOUCH_BUTTON_HEIGHT)
        completer = QCompleter(list(self.landmarks.keys()), self.map_search_input)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.map_search_input.setCompleter(completer)

        self.map_search_button = QPushButton("Search")
        self.map_search_button.setObjectName("map_search_button")
        self.map_search_button.setMinimumHeight(TOUCH_BUTTON_HEIGHT)
        self.map_search_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.map_search_input.returnPressed.connect(self.search_landmark)
        self.map_search_button.clicked.connect(self.search_landmark)

        search_layout.addWidget(self.map_search_input, stretch=1)
        search_layout.addWidget(self.map_search_button)
        page_layout.addWidget(search_panel)

        controls = QFrame()
        controls.setObjectName("map_controls_panel")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(16, 14, 16, 14)
        controls_layout.setSpacing(12)

        self.map_from_combo = QComboBox()
        self.map_from_combo.setObjectName("map_from_combo")
        self.map_to_combo = QComboBox()
        self.map_to_combo.setObjectName("map_to_combo")
        for combo in (self.map_from_combo, self.map_to_combo):
            combo.addItems(self.landmarks.keys())
            combo.setMinimumHeight(TOUCH_BUTTON_HEIGHT)
        self.map_to_combo.setCurrentText("Cafeteria")

        self.map_find_route_button = QPushButton("Find Route")
        self.map_find_route_button.setObjectName("map_find_route_button")
        self.map_reset_route_button = QPushButton("Reset Route")
        self.map_reset_route_button.setObjectName("map_reset_route_button")
        for button in (self.map_find_route_button, self.map_reset_route_button):
            button.setMinimumHeight(TOUCH_BUTTON_HEIGHT)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.map_find_route_button.clicked.connect(self.find_route)
        self.map_reset_route_button.clicked.connect(self.reset_route)

        controls_layout.addWidget(QLabel("From"))
        controls_layout.addWidget(self.map_from_combo, stretch=1)
        controls_layout.addWidget(QLabel("To"))
        controls_layout.addWidget(self.map_to_combo, stretch=1)
        controls_layout.addWidget(self.map_find_route_button)
        controls_layout.addWidget(self.map_reset_route_button)
        page_layout.addWidget(controls)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(18)
        self.map_canvas = MapCanvas(self.map_image_path)
        self.map_canvas.landmark_clicked = self._handle_landmark_click
        body_layout.addWidget(self.map_canvas, stretch=3)
        body_layout.addWidget(self._create_info_panel(), stretch=1)
        page_layout.addLayout(body_layout, stretch=1)

    def _create_info_panel(self) -> QFrame:
        """Create the Google Maps-like route info panel."""
        self.map_info_panel = QFrame()
        self.map_info_panel.setObjectName("map_info_panel")
        self.map_info_panel.setMinimumWidth(300)
        panel_layout = QVBoxLayout(self.map_info_panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(12)

        eyebrow = QLabel("Walking Navigation")
        eyebrow.setObjectName("map_info_eyebrow")
        self.map_info_title = QLabel("Select a route")
        self.map_info_title.setObjectName("map_info_title")
        self.map_route_info_label = QLabel("Choose a start and destination, then tap Find Route.")
        self.map_route_info_label.setObjectName("map_route_info_label")
        self.map_route_info_label.setWordWrap(True)
        self.map_info_details = self.map_route_info_label
        self.map_selected_place_label = QLabel("No place selected.")
        self.map_selected_place_label.setObjectName("map_selected_place_label")
        self.map_selected_place_label.setWordWrap(True)
        self.map_set_destination_button = QPushButton("Set as Destination")
        self.map_set_destination_button.setObjectName("map_set_destination_button")
        self.map_set_destination_button.setMinimumHeight(TOUCH_BUTTON_HEIGHT)
        self.map_set_destination_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.map_set_destination_button.setEnabled(False)
        self.map_set_destination_button.clicked.connect(self.set_selected_as_destination)
        self.map_route_steps_label = QLabel("")
        self.map_route_steps_label.setObjectName("map_route_steps_label")
        self.map_route_steps_label.setWordWrap(True)
        self.map_walk_status_label = QLabel("Choose a route to start walking.")
        self.map_walk_status_label.setObjectName("map_walk_status_label")
        self.map_walk_status_label.setWordWrap(True)

        walk_buttons_layout = QHBoxLayout()
        walk_buttons_layout.setContentsMargins(0, 0, 0, 0)
        walk_buttons_layout.setSpacing(8)
        self.map_start_walk_button = QPushButton("Start Walk")
        self.map_start_walk_button.setObjectName("map_start_walk_button")
        self.map_pause_walk_button = QPushButton("Pause Walk")
        self.map_pause_walk_button.setObjectName("map_pause_walk_button")
        self.map_reset_walk_button = QPushButton("Reset Walk")
        self.map_reset_walk_button.setObjectName("map_reset_walk_button")
        for button in (
            self.map_start_walk_button,
            self.map_pause_walk_button,
            self.map_reset_walk_button,
        ):
            button.setMinimumHeight(TOUCH_BUTTON_HEIGHT)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            walk_buttons_layout.addWidget(button)

        self.map_start_walk_button.clicked.connect(self.start_walk)
        self.map_pause_walk_button.clicked.connect(self.pause_walk)
        self.map_reset_walk_button.clicked.connect(self.reset_walk)

        panel_layout.addWidget(eyebrow)
        panel_layout.addWidget(self.map_info_title)
        panel_layout.addWidget(self.map_route_info_label)
        panel_layout.addWidget(self.map_selected_place_label)
        panel_layout.addWidget(self.map_set_destination_button)
        panel_layout.addWidget(self.map_route_steps_label)
        panel_layout.addWidget(self.map_walk_status_label)
        panel_layout.addLayout(walk_buttons_layout)
        panel_layout.addStretch()
        return self.map_info_panel

    def search_landmark(self) -> None:
        """Search for a landmark by name and select the best match."""
        query = self.map_search_input.text().strip()
        if not query:
            self.map_info_title.setText("Search campus")
            self.map_route_info_label.setText("Type a landmark name to highlight it on the map.")
            return

        exact_match = next(
            (name for name in self.landmarks if name.casefold() == query.casefold()),
            None,
        )
        partial_match = next(
            (name for name in self.landmarks if query.casefold() in name.casefold()),
            None,
        )
        match = exact_match or partial_match
        if match is None:
            self.map_info_title.setText("No landmark found")
            self.map_route_info_label.setText("Try searching for a building, cafeteria, parking, or stadium.")
            return

        self.select_landmark(match)
        self.map_search_input.setText(match)

    def select_landmark(self, landmark: str) -> None:
        """Select a landmark and show its details in the info panel."""
        if landmark not in self.landmarks:
            return
        self.selected_landmark = landmark
        self.map_canvas.select_landmark(landmark)
        category, description = LANDMARK_DETAILS.get(
            landmark,
            ("Campus Landmark", "Campus place on the walking map."),
        )
        self.map_info_title.setText(landmark)
        self.map_route_info_label.setText("Selected landmark")
        self.map_selected_place_label.setText(
            f"Type/category: {category}\n"
            f"{description}"
        )
        self.map_set_destination_button.setEnabled(True)

    def set_selected_as_destination(self) -> None:
        """Use the selected landmark as the route destination."""
        if self.selected_landmark is None:
            return
        self.map_to_combo.setCurrentText(self.selected_landmark)

    def shortest_path(self, start: str, destination: str) -> list[str]:
        """Return a Dijkstra shortest path between two landmarks."""
        if start not in self.landmarks or destination not in self.landmarks:
            return []
        queue = [(0.0, start, [start])]
        visited: set[str] = set()
        while queue:
            distance, node, path = heappop(queue)
            if node == destination:
                return path
            if node in visited:
                continue
            visited.add(node)
            for neighbor in self.walking_graph.get(node, ()):
                if neighbor in visited:
                    continue
                heappush(
                    queue,
                    (
                        distance + self._distance(node, neighbor),
                        neighbor,
                        path + [neighbor],
                    ),
                )
        return []

    def find_route(self) -> None:
        """Find and draw a simulated walking route from the selected combos."""
        start = self.map_from_combo.currentText()
        destination = self.map_to_combo.currentText()
        if start == destination:
            self.current_route = []
            self._stop_walk()
            self.map_canvas.clear_route()
            self.map_info_title.setText("Same location selected")
            self.map_route_info_label.setText("Choose two different places to create a route.")
            self.map_route_steps_label.setText("")
            self.map_walk_status_label.setText("Choose a route first.")
            return

        route = self.shortest_path(start, destination)
        if not route:
            self.current_route = []
            self._stop_walk()
            self.map_canvas.clear_route()
            self.map_info_title.setText("No route found")
            self.map_route_info_label.setText("Try another start or destination.")
            self.map_route_steps_label.setText("")
            self.map_walk_status_label.setText("Choose a route first.")
            return

        self.current_route = route
        self._stop_walk()
        self.walking_progress = 0.0
        self.map_canvas.set_route(route, start, destination)
        self.map_canvas.set_walking_progress(0.0)
        minutes = max(1, round(self._route_distance(route) / 75))
        self.map_info_title.setText("Route ready")
        self.map_route_info_label.setText(
            f"Route: {start} → {destination}\n"
            f"Estimated walking time: {minutes} min"
        )
        self.map_route_steps_label.setText("\n".join(self._route_steps(route)))
        self.map_walk_status_label.setText(f"Ready to walk to {destination}.")

    def reset_route(self) -> None:
        """Clear the active walking route."""
        self.current_route = []
        self._stop_walk()
        self.walking_progress = 0.0
        self.map_canvas.clear_route()
        self.map_info_title.setText("Select a route")
        self.map_route_info_label.setText("Choose a start and destination, then tap Find Route.")
        self.map_route_steps_label.setText("")
        self.map_walk_status_label.setText("Choose a route to start walking.")

    def start_walk(self) -> None:
        """Start or resume walking along the selected route."""
        if len(self.current_route) < 2:
            self._stop_walk()
            self.map_canvas.set_walking_progress(None)
            self.map_walk_status_label.setText("Choose a route first.")
            return

        if self.walking_progress >= 1.0:
            self.walking_progress = 0.0
            self.map_canvas.set_walking_progress(self.walking_progress)
        self.is_walking = True
        self.walk_timer.start()
        self.map_walk_status_label.setText(f"Walking to {self.current_route[-1]}...")

    def pause_walk(self) -> None:
        """Pause the walking animation."""
        self._stop_walk()
        if self.current_route:
            self.map_walk_status_label.setText("Walk paused.")

    def reset_walk(self) -> None:
        """Return the walking dot to the route start."""
        self._stop_walk()
        self.walking_progress = 0.0
        if len(self.current_route) < 2:
            self.map_canvas.set_walking_progress(None)
            self.map_walk_status_label.setText("Choose a route first.")
            return
        self.map_canvas.set_walking_progress(0.0)
        self.map_walk_status_label.setText(f"Ready at {self.current_route[0]}.")

    def _stop_walk(self) -> None:
        """Stop the walk timer and clear active walking state."""
        self.walk_timer.stop()
        self.is_walking = False

    def _advance_walk(self) -> None:
        """Advance the walking dot one animation step."""
        if len(self.current_route) < 2:
            self.reset_walk()
            return

        self.walking_progress = min(1.0, self.walking_progress + 0.035)
        self.map_canvas.set_walking_progress(self.walking_progress)
        destination = self.current_route[-1]
        if self.walking_progress >= 1.0:
            self._stop_walk()
            self.map_walk_status_label.setText(f"Arrived at {destination}")
        else:
            self.map_walk_status_label.setText(f"Walking to {destination}...")

    def _handle_landmark_click(self, landmark: str) -> None:
        """Show clicked landmark context in the route info panel."""
        self.select_landmark(landmark)

    def _distance(self, first: str, second: str) -> float:
        """Return Euclidean distance between two normalized landmarks."""
        x1, y1 = self.landmarks[first]
        x2, y2 = self.landmarks[second]
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def _route_distance(self, route: list[str]) -> float:
        """Return the total route distance in normalized map units."""
        return sum(
            self._distance(route[index], route[index + 1])
            for index in range(len(route) - 1)
        )

    def _route_steps(self, route: list[str]) -> list[str]:
        """Create simple walking instructions for the selected route."""
        if not route:
            return []
        if len(route) == 1:
            return [f"Start at {route[0]}"]

        steps = [f"Start at {route[0]}", "Walk through central path"]
        for landmark in route[1:-1]:
            steps.append(f"Continue toward {landmark}")
        steps.append(f"Arrive at {route[-1]}")
        return steps

    def _apply_styles(self) -> None:
        """Apply ECU public dashboard styling to the navigation map screen."""
        self.setStyleSheet(
            f"""
            QWidget#map_screen {{
                background-color: {OFF_WHITE};
                color: {TEXT_DARK};
                {font(17)}
            }}

            QLabel#map_title {{
                color: {NAVY};
                {font(32, 850)}
            }}

            QLabel#map_subtitle {{
                color: {TEXT_MUTED};
                {font(16, 600)}
            }}

            QFrame#map_search_panel,
            QFrame#map_controls_panel,
            QFrame#map_info_panel {{
                background-color: {WHITE};
                border: 1px solid rgba(92, 107, 128, 70);
                border-radius: {px(CARD_RADIUS)};
            }}

            QLineEdit {{
                background-color: {OFF_WHITE};
                color: {TEXT_DARK};
                border: 1px solid rgba(92, 107, 128, 80);
                border-radius: {px(16)};
                padding: 0 {px(CARD_PADDING)};
                {font(15, 750)}
            }}

            QLineEdit:focus {{
                border: 2px solid {GOLD};
            }}

            QComboBox {{
                background-color: {OFF_WHITE};
                color: {TEXT_DARK};
                border: 1px solid rgba(92, 107, 128, 80);
                border-radius: {px(16)};
                padding: 0 {px(CARD_PADDING)};
                {font(15, 750)}
            }}

            QPushButton {{
                background-color: {NAVY};
                color: {WHITE};
                border: none;
                border-radius: {px(16)};
                padding: 0 {px(18)};
                {font(15, 800)}
            }}

            QPushButton:hover {{
                background-color: {NAVY_LIGHT};
            }}

            QPushButton:pressed {{
                background-color: {GOLD_LIGHT};
                color: {TEXT_DARK};
            }}

            QPushButton:disabled {{
                background-color: rgba(92, 107, 128, 55);
                color: rgba(34, 43, 55, 130);
            }}

            QWidget#map_canvas {{
                background-color: #ECE8DC;
                border: 1px solid rgba(92, 107, 128, 70);
                border-radius: {px(CARD_RADIUS + 4)};
            }}

            QLabel#map_info_eyebrow {{
                color: {GOLD};
                {font(12, 850)}
            }}

            QLabel#map_info_title {{
                color: {NAVY_DARK};
                {font(24, 850)}
            }}

            QLabel#map_route_info_label {{
                color: {TEXT_MUTED};
                {font(15, 650)}
            }}

            QLabel#map_selected_place_label {{
                color: {TEXT_DARK};
                background-color: {OFF_WHITE};
                border: 1px solid rgba(92, 107, 128, 45);
                border-radius: {px(14)};
                padding: {px(12)};
                {font(14, 650)}
            }}

            QLabel#map_route_steps_label {{
                color: {NAVY_DARK};
                background-color: rgba(215, 169, 75, 34);
                border-radius: {px(14)};
                padding: {px(12)};
                {font(14, 700)}
            }}

            QLabel#map_walk_status_label {{
                color: {NAVY_DARK};
                background-color: {WHITE};
                border: 1px solid rgba(215, 169, 75, 90);
                border-radius: {px(14)};
                padding: {px(10)};
                {font(14, 800)}
            }}
            """
        )

    def update_language(self, translations: dict[str, str]) -> None:
        """Keep compatibility labels synchronized with language switching."""
        self.placeholder_title_label.setText(translations["placeholder_map_title"])
