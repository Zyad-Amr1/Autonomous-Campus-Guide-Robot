"""Public campus map route simulation screen."""

from heapq import heappop, heappush
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
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
    "Boys' Musallah": (760, 585),
    "Girls' Musallah": (790, 420),
    "Sports Activity": (775, 510),
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
        "Girls' Musallah",
        "Sports Activity",
    ),
    "Girls' Musallah": ("Building A", "Stadium", "Sports Activity"),
    "Sports Activity": ("Building A", "Girls' Musallah", "Boys' Musallah"),
    "Boys' Musallah": ("Sports Activity", "Stadium"),
    "Stadium": ("Parking", "Girls' Musallah", "Boys' Musallah"),
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
        self.update()

    def clear_route(self) -> None:
        """Clear route overlays and selected endpoints."""
        self.current_route = []
        self.route_start = None
        self.route_destination = None
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

    def mousePressEvent(self, event) -> None:  # noqa: N802
        """Select a landmark when a user taps near its marker."""
        for name in reversed(list(self.landmarks)):
            center = self._point_for_landmark(name)
            delta = center - event.position()
            if (
                delta.x() * delta.x() + delta.y() * delta.y()
                <= self._marker_hit_radius * self._marker_hit_radius
            ):
                self.selected_landmark = name
                if self.landmark_clicked is not None:
                    self.landmark_clicked(name)
                self.update()
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

    def _point_for_landmark(self, name: str) -> QPointF:
        """Convert 0-1000 normalized coordinates into canvas points."""
        x_value, y_value = self.landmarks[name]
        rect = self._image_target_rect if self._image_target_rect.isValid() else QRectF(self.rect().adjusted(16, 16, -16, -16))
        return QPointF(
            rect.left() + rect.width() * (x_value / 1000),
            rect.top() + rect.height() * (y_value / 1000),
        )


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

        panel_layout.addWidget(eyebrow)
        panel_layout.addWidget(self.map_info_title)
        panel_layout.addWidget(self.map_route_info_label)
        panel_layout.addStretch()
        return self.map_info_panel

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
            self.map_canvas.clear_route()
            self.map_info_title.setText("Same location selected")
            self.map_route_info_label.setText("Choose two different places to create a route.")
            return

        route = self.shortest_path(start, destination)
        if not route:
            self.current_route = []
            self.map_canvas.clear_route()
            self.map_info_title.setText("No route found")
            self.map_route_info_label.setText("Try another start or destination.")
            return

        self.current_route = route
        self.map_canvas.set_route(route, start, destination)
        minutes = max(1, round(self._route_distance(route) / 75))
        self.map_info_title.setText("Route ready")
        self.map_route_info_label.setText(
            f"Route: {start} → {destination}\n"
            f"Estimated walking time: {minutes} min"
        )

    def reset_route(self) -> None:
        """Clear the active walking route."""
        self.current_route = []
        self.map_canvas.clear_route()
        self.map_info_title.setText("Select a route")
        self.map_route_info_label.setText("Choose a start and destination, then tap Find Route.")

    def _handle_landmark_click(self, landmark: str) -> None:
        """Show clicked landmark context in the route info panel."""
        self.map_info_title.setText(landmark)
        self.map_route_info_label.setText("Use this place as your start or destination from the route controls.")

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

            QFrame#map_controls_panel,
            QFrame#map_info_panel {{
                background-color: {WHITE};
                border: 1px solid rgba(92, 107, 128, 70);
                border-radius: {px(CARD_RADIUS)};
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
            """
        )

    def update_language(self, translations: dict[str, str]) -> None:
        """Keep compatibility labels synchronized with language switching."""
        self.placeholder_title_label.setText(translations["placeholder_map_title"])
