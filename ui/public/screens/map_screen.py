"""Public campus map navigation screen."""

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

from database.connection import DB_NAME
from database.repositories.room_repository import get_mappable_rooms
from ui.public.theme import (
    BORDER,
    BUTTON_HEIGHT,
    CARD_PADDING,
    CARD_RADIUS,
    CHARCOAL,
    ECU_RED,
    ECU_RED_DARK,
    GOLD,
    GOLD_LIGHT,
    LIGHT_GRAY,
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
    "Building A": (565, 500),
    "Building B": (450, 770),
    "Building C": (275, 700),
    "Building D": (305, 540),
    "Building E": (500, 205),
    "Cafeteria": (320, 385),
    "Parking": (525, 55),
    "Stadium": (860, 235),
    "Workshop 1": (95, 675),
    "Workshop 2": (290, 270),
    "Boys\u2019 Musallah": (765, 585),
    "Girls\u2019 Musallah": (800, 420),
    "Student Activity": (785, 510),
}

LANDMARK_DETAILS = {
    "Building A": ("Academic Building", "Main academic block beside the central path."),
    "Building B": ("Academic Building", "Teaching building on the southern walkway."),
    "Building C": ("Academic Building", "Classroom building near the west campus path."),
    "Building D": ("Academic Building", "Academic block connected to the central walkway."),
    "Building E": ("Academic Building", "Northern academic building near parking."),
    "Cafeteria": ("Student Services", "Food and student break area in the middle of campus."),
    "Parking": ("Campus Access", "Main parking area and common visitor entry point."),
    "Stadium": ("Sports", "Outdoor sports venue on the east side of campus."),
    "Workshop 1": ("Workshop", "Hands-on workshop area near the west side buildings."),
    "Workshop 2": ("Workshop", "Workshop space connected to the cafeteria route."),
    "Boys\u2019 Musallah": ("Prayer Area", "Prayer space near the east campus path."),
    "Girls\u2019 Musallah": ("Prayer Area", "Prayer space near the activity area."),
    "Student Activity": ("Student Life", "Student activity area beside the east walkway."),
}

PATH_NODES = {
    "@parking_link": (525, 55),
    "@north_gate": (520, 105),
    "@north_spine": (500, 205),
    "@west_spine": (300, 300),
    "@cafeteria_path": (320, 385),
    "@central_path": (430, 500),
    "@east_path": (720, 500),
    "@stadium_path": (835, 300),
    "@south_spine": (430, 690),
    "@west_south_path": (230, 675),
}

WALKING_GRAPH = {
    "Parking": ("@parking_link",),
    "@parking_link": ("Parking", "@north_gate"),
    "@north_gate": ("@parking_link", "@north_spine", "@stadium_path"),
    "@north_spine": ("@north_gate", "Building E", "@west_spine", "@central_path"),
    "Building E": ("@north_spine",),
    "@west_spine": ("@north_spine", "Workshop 2", "@cafeteria_path"),
    "Workshop 2": ("@west_spine",),
    "@cafeteria_path": ("@west_spine", "Cafeteria", "@central_path"),
    "Cafeteria": ("@cafeteria_path",),
    "@central_path": (
        "@north_spine",
        "@cafeteria_path",
        "Building A",
        "Building D",
        "@south_spine",
        "@east_path",
    ),
    "Building A": ("@central_path",),
    "Building D": ("@central_path",),
    "@south_spine": ("@central_path", "Building B", "Building C", "@west_south_path"),
    "Building B": ("@south_spine",),
    "Building C": ("@south_spine",),
    "@west_south_path": ("@south_spine", "Workshop 1"),
    "Workshop 1": ("@west_south_path",),
    "@east_path": (
        "@central_path",
        "Student Activity",
        "Girls\u2019 Musallah",
        "Boys\u2019 Musallah",
        "@stadium_path",
    ),
    "Student Activity": ("@east_path",),
    "Girls\u2019 Musallah": ("@east_path",),
    "Boys\u2019 Musallah": ("@east_path",),
    "@stadium_path": ("@north_gate", "@east_path", "Stadium"),
    "Stadium": ("@stadium_path",),
}


def _project_root() -> Path:
    """Return the repository root that contains the app's top-level folders."""
    current_file = Path(__file__).resolve()
    for folder in (current_file.parent, *current_file.parents):
        if all((folder / name).exists() for name in ("apps", "ui", "database", "tests")):
            return folder
    return current_file.parents[3]


class MapCanvas(QWidget):
    """Display the real ECU map image with route and hotspot overlays."""

    MIN_ZOOM_FACTOR = 1.0
    MAX_ZOOM_FACTOR = 2.5
    ZOOM_STEP = 0.15

    def __init__(self, background_image_path: str | None = None) -> None:
        super().__init__()
        self.setObjectName("map_canvas")
        self.setMinimumSize(760, 560)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.background_image_path: str | None = None
        self.resolved_background_image_path: Path | None = None
        self.map_image_path: str | None = None
        self.map_image_exists = False
        self._background_pixmap = QPixmap()
        self.landmarks = LANDMARKS.copy()
        self.path_points = {**PATH_NODES, **self.landmarks}
        self.database_markers: list[dict] = []
        self.markers = self.database_markers
        self.current_route: list[str] = []
        self.route_start: str | None = None
        self.route_destination: str | None = None
        self.walking_progress: float | None = None
        self.selected_landmark: str | None = None
        self.selected_marker: dict | None = None
        self.selected_marker_payload: dict | None = None
        self.landmark_clicked = None
        self.marker_clicked = None
        self._image_target_rect = QRectF()
        self._marker_hit_radius = 18
        self._zoom_factor = self.MIN_ZOOM_FACTOR
        self._pan_offset = QPointF(0, 0)
        self._is_panning = False
        self._last_pan_position = QPointF()
        self._selection_animation_key: str | None = None
        self._selection_animation_progress = 1.0
        self._selection_animation_timer = QTimer(self)
        self._selection_animation_timer.setInterval(16)
        self._selection_animation_timer.timeout.connect(self._advance_selection_animation)
        self._route_start_pulse_phase = 0.0
        self._route_start_pulse_timer = QTimer(self)
        self._route_start_pulse_timer.setInterval(40)
        self._route_start_pulse_timer.timeout.connect(self._advance_route_start_pulse)
        if background_image_path is not None:
            self.set_background_image(background_image_path)

    @property
    def zoom_factor(self) -> float:
        """Return the current map zoom level."""
        return self._zoom_factor

    @property
    def pulse_phase(self) -> float:
        """Return the current route start pulse phase."""
        return self._route_start_pulse_phase

    @property
    def route_start_pulse_active(self) -> bool:
        """Return whether the active-route start pulse is running."""
        return self._route_start_pulse_timer.isActive()

    def set_background_image(self, path: str) -> None:
        """Set a campus map image path and repaint the canvas."""
        self.background_image_path = path
        image_path = Path(path)
        if not image_path.is_absolute():
            image_path = _project_root() / image_path
        self.resolved_background_image_path = image_path
        self.map_image_path = str(image_path)
        self.map_image_exists = image_path.exists()
        self._background_pixmap = QPixmap(str(image_path)) if self.map_image_exists else QPixmap()
        self.update()

    def set_markers(self, markers: list[dict] | None) -> None:
        """Store normalized database markers for rendering on the map."""
        valid_markers: list[dict] = []
        for marker in markers or []:
            if not isinstance(marker, dict):
                continue
            x_coord = self._normalized_marker_coord(marker.get("x_coord"))
            y_coord = self._normalized_marker_coord(marker.get("y_coord"))
            if x_coord is None or y_coord is None:
                continue
            if x_coord == 0 and y_coord == 0:
                continue
            stored_marker = dict(marker)
            stored_marker["x_coord"] = x_coord
            stored_marker["y_coord"] = y_coord
            valid_markers.append(stored_marker)
        self.database_markers = valid_markers
        self.markers = self.database_markers
        self.update()

    def set_route(self, route: list[str], start: str, destination: str) -> None:
        """Store and draw a selected walking route."""
        self.current_route = route
        self.route_start = start
        self.route_destination = destination
        self.walking_progress = None
        if len(route) >= 2 and start in self.path_points:
            self._start_route_start_pulse()
        else:
            self._stop_route_start_pulse()
        self.update()

    def clear_route(self) -> None:
        """Clear route overlays and selected endpoints."""
        self.current_route = []
        self.route_start = None
        self.route_destination = None
        self.walking_progress = None
        self._stop_route_start_pulse()
        self.update()

    def set_walking_progress(self, progress: float | None) -> None:
        """Set the animated walking dot position along the route."""
        self.walking_progress = None if progress is None else min(1.0, max(0.0, progress))
        self.update()

    def select_landmark(self, landmark: str) -> None:
        """Highlight a landmark hotspot."""
        if landmark not in self.landmarks:
            return
        self.selected_landmark = landmark
        self.selected_marker = None
        self.selected_marker_payload = None
        self._is_panning = False
        self._start_selection_animation(f"landmark:{landmark}")
        self.update()

    def select_marker(self, marker: dict) -> dict:
        """Highlight a database marker and return its public selection payload."""
        self.selected_marker = marker
        self.selected_marker_payload = self._marker_selection_payload(marker)
        self.selected_landmark = None
        self._is_panning = False
        self._start_selection_animation(self._marker_animation_key(marker))
        self.update()
        return self.selected_marker_payload

    def clear_selection(self) -> None:
        """Clear selected landmark and database marker highlights."""
        self.selected_landmark = None
        self.selected_marker = None
        self.selected_marker_payload = None
        self._selection_animation_key = None
        self._selection_animation_progress = 1.0
        self._selection_animation_timer.stop()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint the real map image and live navigation overlays."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        canvas_rect = QRectF(self.rect().adjusted(3, 3, -3, -3))
        painter.setPen(QPen(QColor("#D9DEE7"), 1))
        painter.setBrush(QColor("#FDFDFB"))
        painter.drawRoundedRect(canvas_rect, 14, 14)

        if self._background_pixmap.isNull():
            self._image_target_rect = canvas_rect
            self._draw_missing_image_message(painter, canvas_rect)
            return

        self._draw_background_image(painter, canvas_rect)
        self._draw_route(painter)
        self._draw_route_start_pulse(painter)
        self._draw_landmark_hotspots(painter)
        self._draw_database_markers(painter)
        self._draw_walker(painter)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        """Select a landmark or database marker when tapped."""
        if event.button() == Qt.MouseButton.LeftButton:
            for name in reversed(list(self.landmarks)):
                center = self._point_for_name(name)
                delta = center - event.position()
                if (
                    delta.x() * delta.x() + delta.y() * delta.y()
                    <= self._marker_hit_radius * self._marker_hit_radius
                ):
                    self.select_landmark(name)
                    if self.landmark_clicked is not None:
                        self.landmark_clicked(name)
                    return
            marker = self._marker_at_position(event.position())
            if marker is not None:
                payload = self.select_marker(marker)
                if self.marker_clicked is not None:
                    self.marker_clicked(payload)
                return
            self._is_panning = True
            self._last_pan_position = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        """Pan the zoomed map with a simple drag gesture."""
        if self._is_panning and self._zoom_factor > 1.0:
            delta = event.position() - self._last_pan_position
            self._last_pan_position = event.position()
            self._pan_offset += delta
            self._constrain_pan()
            self.update()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        """End drag panning."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event) -> None:  # noqa: N802
        """Support mouse wheel zoom for kiosk operators and desktop users."""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        elif event.angleDelta().y() < 0:
            self.zoom_out()
        event.accept()

    def zoom_in(self) -> None:
        """Increase map zoom without distorting the real image."""
        self._zoom_factor = min(self.MAX_ZOOM_FACTOR, self._zoom_factor + self.ZOOM_STEP)
        self._constrain_pan()
        self.update()

    def zoom_out(self) -> None:
        """Decrease map zoom and keep the image centered at fit size."""
        self._zoom_factor = max(self.MIN_ZOOM_FACTOR, self._zoom_factor - self.ZOOM_STEP)
        if self._zoom_factor == self.MIN_ZOOM_FACTOR:
            self._pan_offset = QPointF(0, 0)
        self._constrain_pan()
        self.update()

    def reset_view(self) -> None:
        """Return the map to its fitted viewport."""
        self._zoom_factor = self.MIN_ZOOM_FACTOR
        self._pan_offset = QPointF(0, 0)
        self.update()

    def _draw_background_image(self, painter: QPainter, rect: QRectF) -> None:
        """Draw the real campus map image smoothly, centered, and aspect-safe."""
        viewport_size = rect.size().toSize()
        zoomed_size = viewport_size * self._zoom_factor
        scaled = self._background_pixmap.scaled(
            zoomed_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        target_x = rect.x() + (rect.width() - scaled.width()) / 2 + self._pan_offset.x()
        target_y = rect.y() + (rect.height() - scaled.height()) / 2 + self._pan_offset.y()
        self._image_target_rect = QRectF(target_x, target_y, scaled.width(), scaled.height())
        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, 14, 14)
        painter.save()
        painter.setClipPath(clip_path)
        painter.drawPixmap(int(target_x), int(target_y), scaled)
        painter.restore()

    def _draw_missing_image_message(self, painter: QPainter, rect: QRectF) -> None:
        """Draw a friendly placeholder when the map image is unavailable."""
        painter.setPen(QPen(QColor("#D8D2C5"), 2, Qt.PenStyle.DashLine))
        painter.setBrush(QColor("#F1EEE7"))
        painter.drawRoundedRect(rect.adjusted(18, 18, -18, -18), 18, 18)
        painter.setPen(QColor(TEXT_MUTED))
        painter.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        painter.drawText(
            rect.adjusted(28, 28, -28, -28),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            "Campus map image not found: assets/maps/campus_outdoor_map.png",
        )

    def _draw_route(self, painter: QPainter) -> None:
        """Draw the current route as a polished ECU accent polyline."""
        if len(self.current_route) < 2:
            return
        path = QPainterPath(self._point_for_name(self.current_route[0]))
        for node in self.current_route[1:]:
            path.lineTo(self._point_for_name(node))
        shadow_path = path.translated(2, 2)
        painter.setPen(QPen(QColor(20, 24, 31, 58), 13, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(shadow_path)
        painter.setPen(QPen(QColor(255, 255, 255, 210), 11, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)
        painter.setPen(QPen(QColor(ECU_RED), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)
        painter.setPen(QPen(QColor(GOLD), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)

    def _draw_route_start_pulse(self, painter: QPainter) -> None:
        """Draw a subtle active-route "you are here" pulse around the start."""
        if len(self.current_route) < 2 or self.route_start not in self.path_points:
            return
        center = self._point_for_name(self.route_start)
        phase = min(1.0, max(0.0, self._route_start_pulse_phase))
        radius = 13 + phase * 15
        opacity = round(72 * (1.0 - phase))

        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(34, 160, 107, opacity))
        painter.drawEllipse(center, radius, radius)
        painter.setPen(QPen(QColor(255, 255, 255, round(95 * (1.0 - phase))), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius, radius)
        painter.restore()

    def _draw_landmark_hotspots(self, painter: QPainter) -> None:
        """Draw subtle clickable pins near real map labels, not fake dot fields."""
        for name in self.landmarks:
            center = self._point_for_name(name)
            is_start = name == self.route_start
            is_destination = name == self.route_destination
            is_selected = name == self.selected_landmark
            fill = QColor(WHITE)
            border = QColor(CHARCOAL)
            radius = 5
            if is_start:
                fill = QColor("#22A06B")
                border = QColor(WHITE)
                radius = 8
            elif is_destination:
                fill = QColor(ECU_RED)
                border = QColor(WHITE)
                radius = 9
            elif is_selected:
                fill = QColor(GOLD_LIGHT)
                border = QColor(ECU_RED)
                radius = 8
            pulse = self._selection_animation_pulse(f"landmark:{name}") if is_selected else 0.0
            radius += pulse * 2.5

            pin_path = QPainterPath()
            pin_path.addEllipse(center, radius, radius)
            pin_tip = QPointF(center.x(), center.y() + radius + 7)
            pin_path.moveTo(center.x() - radius * 0.45, center.y() + radius * 0.55)
            pin_path.lineTo(pin_tip)
            pin_path.lineTo(center.x() + radius * 0.45, center.y() + radius * 0.55)
            pin_path.closeSubpath()
            if pulse > 0:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(215, 25, 32, round(42 * pulse)))
                painter.drawEllipse(center, radius + 5 * pulse, radius + 5 * pulse)
            painter.setPen(QPen(QColor(0, 0, 0, 35), 3))
            painter.setBrush(QColor(0, 0, 0, 28))
            painter.drawPath(pin_path.translated(0, 2))
            painter.setPen(QPen(border, 2))
            painter.setBrush(fill)
            painter.drawPath(pin_path)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(CHARCOAL) if fill != QColor(ECU_RED) else QColor(WHITE))
            painter.drawEllipse(center, max(2, radius - 5), max(2, radius - 5))

    def _draw_database_markers(self, painter: QPainter) -> None:
        """Draw database-driven room markers using normalized image coordinates."""
        if not self.database_markers:
            return

        painter.save()
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        ordered_markers = [
            marker for marker in self.database_markers if not self._is_selected_marker(marker)
        ]
        ordered_markers.extend(
            marker for marker in self.database_markers if self._is_selected_marker(marker)
        )
        for marker in ordered_markers:
            point = self._point_for_marker(marker)
            title = self._marker_title(marker)
            accent = QColor(self.marker_color(marker.get("category")))
            is_selected = self._is_selected_marker(marker)
            pulse = self._selection_animation_pulse(self._marker_animation_key(marker)) if is_selected else 0.0
            border = QColor(ECU_RED if is_selected else "#8A6500")
            pin_radius = (7 if is_selected else 6) + pulse * 2.2
            label_border = QColor(ECU_RED if is_selected else "#D8DEE7")

            label_width = min(178, max(92, len(title) * 7 + 20))
            label_rect = QRectF(point.x() + 11, point.y() - 29, label_width, 24)
            if label_rect.right() > self._image_target_rect.right() - 6:
                label_rect.moveRight(point.x() - 11)
            if label_rect.left() < self._image_target_rect.left() + 6:
                label_rect.moveLeft(point.x() + 11)
            if label_rect.top() < self._image_target_rect.top() + 6:
                label_rect.moveTop(point.y() + 13)

            painter.setPen(QPen(QColor(60, 45, 0, 90), 1))
            painter.drawLine(point, QPointF(label_rect.left(), label_rect.center().y()))

            pin_path = QPainterPath()
            pin_center = QPointF(point.x(), point.y() - 7)
            pin_path.addEllipse(pin_center, pin_radius, pin_radius)
            pin_path.moveTo(point.x() - 4, point.y() - 2)
            pin_path.lineTo(point)
            pin_path.lineTo(point.x() + 4, point.y() - 2)
            pin_path.closeSubpath()
            if pulse > 0:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(215, 25, 32, round(38 * pulse)))
                painter.drawEllipse(pin_center, pin_radius + 5 * pulse, pin_radius + 5 * pulse)
            painter.setPen(QPen(QColor(0, 0, 0, 35), 2))
            painter.setBrush(QColor(0, 0, 0, 28))
            painter.drawPath(pin_path.translated(0, 2))
            painter.setPen(QPen(border, 1.4))
            painter.setBrush(accent)
            painter.drawPath(pin_path)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(WHITE))
            painter.drawEllipse(pin_center, 2.2, 2.2)

            painter.setPen(QPen(label_border, 1.4 if is_selected else 1))
            painter.setBrush(QColor(255, 255, 255, 236))
            painter.drawRoundedRect(label_rect, 8, 8)
            painter.setPen(QColor(TEXT_DARK))
            painter.drawText(
                label_rect.adjusted(9, 1, -8, -1),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                title,
            )
        painter.restore()

    def _draw_walker(self, painter: QPainter) -> None:
        """Draw the animated current-location marker on top of the route."""
        if self.walking_progress is None or len(self.current_route) < 2:
            return
        position = self._point_for_route_progress(self.walking_progress)
        shadow_position = position + QPointF(2, 2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(20, 24, 31, 50))
        painter.drawEllipse(shadow_position, 14, 14)
        painter.setPen(QPen(QColor(WHITE), 5))
        painter.setBrush(QColor(NAVY_DARK))
        painter.drawEllipse(position, 13, 13)
        painter.setPen(QPen(QColor(GOLD), 3))
        painter.setBrush(QColor(WHITE))
        painter.drawEllipse(position, 7, 7)

    def _point_for_name(self, name: str) -> QPointF:
        """Convert normalized coordinates into canvas points."""
        x_value, y_value = self.path_points[name]
        rect = (
            self._image_target_rect
            if self._image_target_rect.isValid()
            else QRectF(self.rect().adjusted(8, 8, -8, -8))
        )
        return QPointF(
            rect.left() + rect.width() * (x_value / 1000),
            rect.top() + rect.height() * (y_value / 1000),
        )

    def _point_for_marker(self, marker: dict) -> QPointF:
        """Convert a stored normalized marker into a canvas point."""
        rect = (
            self._image_target_rect
            if self._image_target_rect.isValid()
            else QRectF(self.rect().adjusted(8, 8, -8, -8))
        )
        return QPointF(
            rect.left() + rect.width() * marker["x_coord"],
            rect.top() + rect.height() * marker["y_coord"],
        )

    def _marker_at_position(self, position: QPointF) -> dict | None:
        """Return the topmost database marker close enough to a click."""
        for marker in reversed(self.database_markers):
            point = self._point_for_marker(marker)
            delta = point - position
            if delta.x() * delta.x() + delta.y() * delta.y() <= self._marker_hit_radius**2:
                return marker
        return None

    def _is_selected_marker(self, marker: dict) -> bool:
        """Return whether a marker is the active database selection."""
        if self.selected_marker is None:
            return False
        if marker is self.selected_marker:
            return True
        return marker.get("id") is not None and marker.get("id") == self.selected_marker.get("id")

    def _marker_animation_key(self, marker: dict) -> str:
        """Return a stable animation key for a database marker selection."""
        marker_id = marker.get("id")
        if marker_id is not None:
            return f"marker:id:{marker_id}"
        return f"marker:title:{self._marker_title(marker)}"

    def _start_selection_animation(self, key: str) -> None:
        """Start one short selected-marker pulse for a new selection."""
        if self._selection_animation_key == key and self._selection_animation_timer.isActive():
            return
        if self._selection_animation_key == key and self._selection_animation_progress < 1.0:
            return
        self._selection_animation_key = key
        self._selection_animation_progress = 0.0
        self._selection_animation_timer.start()

    def _advance_selection_animation(self) -> None:
        """Advance the short QPainter-based selected marker animation."""
        self._selection_animation_progress = min(1.0, self._selection_animation_progress + 0.08)
        if self._selection_animation_progress >= 1.0:
            self._selection_animation_timer.stop()
        self.update()

    def _selection_animation_pulse(self, key: str) -> float:
        """Return a decaying pulse strength for the active selected marker."""
        if self._selection_animation_key != key:
            return 0.0
        progress = min(1.0, max(0.0, self._selection_animation_progress))
        return (1.0 - progress) * (1.0 - progress)

    def _start_route_start_pulse(self) -> None:
        """Start the continuous active-route start pulse."""
        self._route_start_pulse_phase = 0.0
        if not self._route_start_pulse_timer.isActive():
            self._route_start_pulse_timer.start()

    def _stop_route_start_pulse(self) -> None:
        """Stop and reset the active-route start pulse."""
        self._route_start_pulse_timer.stop()
        self._route_start_pulse_phase = 0.0

    def _advance_route_start_pulse(self) -> None:
        """Advance the active-route start pulse safely."""
        if len(self.current_route) < 2 or self.route_start not in self.path_points:
            self._stop_route_start_pulse()
            self.update()
            return
        self._route_start_pulse_phase = (self._route_start_pulse_phase + 0.045) % 1.0
        self.update()

    def marker_color(self, category: str | None) -> str:
        """Return the stable accent color for a database marker category."""
        normalized = str(category or "other").strip().casefold()
        if "library" in normalized:
            return "#3BAA6B"
        if "office" in normalized:
            return "#8E5CF7"
        if "lab" in normalized:
            return "#2F80ED"
        if "class" in normalized:
            return "#22A06B"
        if "service" in normalized or "cafeteria" in normalized:
            return "#E67E22"
        return GOLD

    def _marker_title(self, marker: dict) -> str:
        """Return a compact display title for a database marker."""
        title = (
            marker.get("title")
            or marker.get("room_name")
            or marker.get("name")
            or marker.get("room_number")
            or "Campus marker"
        )
        title = " ".join(str(title).split())
        if len(title) > 28:
            return f"{title[:25]}..."
        return title

    def _marker_selection_payload(self, marker: dict) -> dict:
        """Return a clean public payload for database marker selection."""
        return {
            "type": "database_marker",
            "title": self._marker_title(marker),
            "room_name": marker.get("room_name"),
            "room_number": marker.get("room_number"),
            "category": marker.get("category"),
            "building": marker.get("building"),
            "floor": marker.get("floor"),
            "description": marker.get("description"),
            "raw": marker.get("raw") or {},
        }

    def _normalized_marker_coord(self, value) -> float | None:
        """Validate a normalized marker coordinate."""
        try:
            coordinate = float(value)
        except (TypeError, ValueError):
            return None
        if 0 <= coordinate <= 1:
            return coordinate
        if 10 <= coordinate <= 1000:
            return coordinate / 1000
        return None

    def _point_for_route_progress(self, progress: float) -> QPointF:
        """Return the canvas point at a normalized progress along the route."""
        route_points = [self._point_for_name(name) for name in self.current_route]
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

    def _constrain_pan(self) -> None:
        """Keep zoomed image edges near the viewport."""
        if self._background_pixmap.isNull() or self._zoom_factor <= self.MIN_ZOOM_FACTOR:
            self._pan_offset = QPointF(0, 0)
            return
        rect = QRectF(self.rect().adjusted(3, 3, -3, -3))
        scaled = self._background_pixmap.scaled(
            rect.size().toSize() * self._zoom_factor,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        max_x = max(0.0, (scaled.width() - rect.width()) / 2)
        max_y = max(0.0, (scaled.height() - rect.height()) / 2)
        self._pan_offset = QPointF(
            min(max(self._pan_offset.x(), -max_x), max_x),
            min(max(self._pan_offset.y(), -max_y), max_y),
        )


class MapScreen(QWidget):
    """Display campus walking navigation over the real ECU map."""

    MAP_IMAGE_PATH = "assets/maps/campus_outdoor_map.png"

    def __init__(
        self,
        db_path: str | Path | None = None,
        parent: QWidget | None = None,
        map_image_path: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.db_path = db_path or DB_NAME
        self.map_image_path = map_image_path or self.MAP_IMAGE_PATH
        self.landmarks = LANDMARKS.copy()
        self.path_points = {**PATH_NODES, **self.landmarks}
        self.walking_graph = {key: tuple(value) for key, value in WALKING_GRAPH.items()}
        self.current_route: list[str] = []
        self.selected_landmark: str | None = None
        self.selected_database_marker: dict | None = None
        self.walking_progress = 0.0
        self.is_walking = False
        self.walk_timer = QTimer(self)
        self.walk_timer.setInterval(120)
        self.walk_timer.timeout.connect(self._advance_walk)
        self._translations: dict[str, str] = {}
        self.setObjectName("map_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._load_database_markers()
        self._apply_styles()

    def _load_database_markers(self) -> None:
        """Load room coordinate rows into the canvas without affecting routing."""
        markers: list[dict] = []
        try:
            rows = get_mappable_rooms(self.db_path)
        except Exception:
            rows = []

        for row in rows:
            raw = self._room_row_to_dict(row)
            title = raw.get("room_name") or raw.get("room_number") or "Room"
            markers.append(
                {
                    "id": raw.get("id"),
                    "title": title,
                    "room_name": raw.get("room_name"),
                    "room_number": raw.get("room_number"),
                    "category": raw.get("category"),
                    "description": raw.get("description"),
                    "building": raw.get("building"),
                    "floor": raw.get("floor"),
                    "x_coord": raw.get("x_coord"),
                    "y_coord": raw.get("y_coord"),
                    "raw": raw,
                }
            )
        self.map_canvas.set_markers(markers)

    def _room_row_to_dict(self, row) -> dict:
        """Convert sqlite row-like room records to a plain dict."""
        try:
            return {key: row[key] for key in row.keys()}
        except AttributeError:
            return dict(row)

    def _build_ui(self) -> None:
        """Arrange route controls, map canvas, and info panel."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(PAGE_PADDING, 20, PAGE_PADDING, PAGE_PADDING)
        page_layout.setSpacing(12)

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
        controls_layout.setContentsMargins(14, 12, 14, 12)
        controls_layout.setSpacing(10)
        self.map_search_input = QLineEdit()
        self.map_search_input.setObjectName("map_search_input")
        self.map_search_input.setPlaceholderText("Search landmarks")
        self.map_search_input.setMinimumHeight(40)
        completer = QCompleter(list(self.landmarks.keys()), self.map_search_input)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.map_search_input.setCompleter(completer)
        self.map_search_button = QPushButton("Search")
        self.map_search_button.setObjectName("map_search_button")
        self.map_search_button.setMinimumHeight(40)
        self.map_search_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.map_search_input.returnPressed.connect(self.search_landmark)
        self.map_search_button.clicked.connect(self.search_landmark)
        self.map_from_combo = QComboBox()
        self.map_from_combo.setObjectName("map_from_combo")
        self.map_to_combo = QComboBox()
        self.map_to_combo.setObjectName("map_to_combo")
        for combo in (self.map_from_combo, self.map_to_combo):
            combo.addItems(self.landmarks.keys())
            combo.setMinimumHeight(40)
        self.map_to_combo.setCurrentText("Cafeteria")
        self.map_find_route_button = QPushButton("Find Route")
        self.map_find_route_button.setObjectName("map_find_route_button")
        self.map_reset_route_button = QPushButton("Reset Route")
        self.map_reset_route_button.setObjectName("map_reset_route_button")
        for button in (self.map_find_route_button, self.map_reset_route_button):
            button.setMinimumHeight(40)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.map_find_route_button.clicked.connect(self.find_route)
        self.map_reset_route_button.clicked.connect(self.reset_route)
        self.map_from_label = QLabel("From")
        self.map_from_label.setObjectName("map_control_label")
        self.map_to_label = QLabel("To")
        self.map_to_label.setObjectName("map_control_label")
        self.map_zoom_in_button = QPushButton("+")
        self.map_zoom_in_button.setObjectName("map_zoom_in_button")
        self.map_zoom_out_button = QPushButton("-")
        self.map_zoom_out_button.setObjectName("map_zoom_out_button")
        self.map_reset_view_button = QPushButton("Reset")
        self.map_reset_view_button.setObjectName("map_reset_view_button")
        for button in (self.map_zoom_in_button, self.map_zoom_out_button, self.map_reset_view_button):
            button.setMinimumHeight(40)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

        controls_layout.addWidget(self.map_search_input, stretch=3)
        controls_layout.addWidget(self.map_search_button)
        controls_layout.addWidget(self.map_from_label)
        controls_layout.addWidget(self.map_from_combo, stretch=2)
        controls_layout.addWidget(self.map_to_label)
        controls_layout.addWidget(self.map_to_combo, stretch=2)
        controls_layout.addWidget(self.map_find_route_button)
        controls_layout.addWidget(self.map_reset_route_button)
        controls_layout.addWidget(self.map_zoom_out_button)
        controls_layout.addWidget(self.map_zoom_in_button)
        controls_layout.addWidget(self.map_reset_view_button)
        page_layout.addWidget(controls)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)
        self.map_canvas = MapCanvas(self.map_image_path)
        self.map_canvas.landmark_clicked = self._handle_landmark_click
        self.map_canvas.marker_clicked = self._handle_database_marker_click
        self.map_zoom_in_button.clicked.connect(self.map_canvas.zoom_in)
        self.map_zoom_out_button.clicked.connect(self.map_canvas.zoom_out)
        self.map_reset_view_button.clicked.connect(self.map_canvas.reset_view)
        body_layout.addWidget(self.map_canvas, stretch=3)
        body_layout.addWidget(self._create_info_panel(), stretch=1)
        page_layout.addLayout(body_layout, stretch=1)

    def _create_info_panel(self) -> QFrame:
        """Create the Google Maps-like route info panel."""
        self.map_info_panel = QFrame()
        self.map_info_panel.setObjectName("map_info_panel")
        self.map_info_panel.setMinimumWidth(320)
        self.map_info_panel.setMaximumWidth(360)
        panel_layout = QVBoxLayout(self.map_info_panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(9)
        eyebrow = QLabel("Walking Navigation")
        self.map_info_eyebrow = eyebrow
        self.map_info_eyebrow.setObjectName("map_info_eyebrow")
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
        self.map_set_destination_button.setMinimumHeight(40)
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
        self.map_pause_walk_button = QPushButton("Pause")
        self.map_pause_walk_button.setObjectName("map_pause_walk_button")
        self.map_reset_walk_button = QPushButton("Reset")
        self.map_reset_walk_button.setObjectName("map_reset_walk_button")
        for button in (self.map_start_walk_button, self.map_pause_walk_button, self.map_reset_walk_button):
            button.setMinimumHeight(40)
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
            self.map_info_title.setText(self._t("map_search_title", "Search campus"))
            self.map_route_info_label.setText(
                self._t("map_search_empty", "Type a landmark name to highlight it on the map.")
            )
            return
        exact_match = next((name for name in self.landmarks if name.casefold() == query.casefold()), None)
        partial_match = next((name for name in self.landmarks if query.casefold() in name.casefold()), None)
        match = exact_match or partial_match
        if match is None:
            marker = self._find_database_marker(query)
            if marker is not None:
                self.select_database_marker(marker)
                self.map_search_input.setText(marker.get("title") or marker.get("room_name") or "")
                return
            self.map_info_title.setText(
                self._t("map_search_not_found_title", "No landmark found")
            )
            self.map_route_info_label.setText(
                self._t(
                    "map_search_not_found",
                    "Try searching for a building, cafeteria, parking, or stadium.",
                )
            )
            return
        self.select_landmark(match)
        self.map_search_input.setText(match)

    def select_landmark(self, landmark: str) -> None:
        """Select a landmark and show its details in the info panel."""
        if landmark not in self.landmarks:
            return
        self.selected_landmark = landmark
        self.selected_database_marker = None
        self.map_canvas.select_landmark(landmark)
        category, description = LANDMARK_DETAILS.get(landmark, ("Campus Landmark", "Campus place on the walking map."))
        self.map_info_title.setText(landmark)
        self.map_route_info_label.setText(
            self._t("map_selected_landmark", "Selected landmark")
        )
        self.map_selected_place_label.setText(
            f"{self._t('map_type_category', 'Type/category')}: {category}\n{description}"
        )
        self.map_set_destination_button.setEnabled(True)

    def select_database_marker(self, marker: dict) -> None:
        """Select a database marker and show its room/location details."""
        payload = self.map_canvas.select_marker(marker)
        self._show_database_marker_details(payload)

    def set_selected_as_destination(self) -> None:
        """Use the selected landmark as the route destination."""
        if self.selected_landmark is not None:
            self.map_to_combo.setCurrentText(self.selected_landmark)

    def shortest_path(self, start: str, destination: str) -> list[str]:
        """Return a Dijkstra shortest path over the walkway graph."""
        if start not in self.path_points or destination not in self.path_points:
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
                heappush(queue, (distance + self._distance(node, neighbor), neighbor, path + [neighbor]))
        return []

    def find_route(self) -> None:
        """Find and draw a simulated walking route from the selected combos."""
        start = self.map_from_combo.currentText()
        destination = self.map_to_combo.currentText()
        if start == destination:
            self.current_route = []
            self._stop_walk()
            self.map_canvas.clear_route()
            self.map_info_title.setText(
                self._t("map_same_location_title", "Same location selected")
            )
            self.map_route_info_label.setText(
                self._t("map_same_location_message", "Choose two different places to create a route.")
            )
            self.map_route_steps_label.setText("")
            self.map_walk_status_label.setText(self._t("map_choose_route_first", "Choose a route first."))
            return

        route = self.shortest_path(start, destination)
        if not route:
            self.current_route = []
            self._stop_walk()
            self.map_canvas.clear_route()
            self.map_info_title.setText(self._t("map_no_route_title", "No route found"))
            self.map_route_info_label.setText(self._t("map_no_route_message", "Try another start or destination."))
            self.map_route_steps_label.setText("")
            self.map_walk_status_label.setText(self._t("map_choose_route_first", "Choose a route first."))
            return

        self.current_route = route
        self._stop_walk()
        self.walking_progress = 0.0
        self.map_canvas.set_route(route, start, destination)
        self.map_canvas.set_walking_progress(0.0)
        minutes = max(1, round(self._route_distance(route) / 95))
        self.map_info_title.setText(self._t("map_route_ready", "Route ready"))
        self.map_route_info_label.setText(
            f"{self._t('map_route_label', 'Route')}: {start} \u2192 {destination}\n"
            f"{self._t('map_estimated_time', 'Estimated walking time')}: {minutes} min"
        )
        self.map_route_steps_label.setText("\n".join(self._route_steps(route)))
        self.map_walk_status_label.setText(
            self._t("map_ready_to_walk", "Ready to walk to {destination}.").format(destination=destination)
        )

    def reset_route(self) -> None:
        """Clear the active walking route."""
        self.current_route = []
        self._stop_walk()
        self.walking_progress = 0.0
        self.map_canvas.clear_route()
        self.map_info_title.setText(self._t("map_info_title_default", "Select a route"))
        self.map_route_info_label.setText(
            self._t("map_route_info_default", "Choose a start and destination, then tap Find Route.")
        )
        self.map_route_steps_label.setText("")
        self.map_walk_status_label.setText(
            self._t("map_walk_status_default", "Choose a route to start walking.")
        )

    def start_walk(self) -> None:
        """Start or resume walking along the selected route."""
        if len(self.current_route) < 2:
            self._stop_walk()
            self.map_canvas.set_walking_progress(None)
            self.map_walk_status_label.setText(self._t("map_choose_route_first", "Choose a route first."))
            return
        if self.walking_progress >= 1.0:
            self.walking_progress = 0.0
            self.map_canvas.set_walking_progress(0.0)
        self.is_walking = True
        self.walk_timer.start()
        self.map_walk_status_label.setText(
            self._t("map_walking_to", "Walking to {destination}...").format(destination=self.current_route[-1])
        )

    def pause_walk(self) -> None:
        """Pause the walking animation."""
        self._stop_walk()
        if self.current_route:
            self.map_walk_status_label.setText(self._t("map_walk_paused", "Walk paused."))

    def reset_walk(self) -> None:
        """Return the walking dot to the route start."""
        self._stop_walk()
        self.walking_progress = 0.0
        if len(self.current_route) < 2:
            self.map_canvas.set_walking_progress(None)
            self.map_walk_status_label.setText(self._t("map_choose_route_first", "Choose a route first."))
            return
        self.map_canvas.set_walking_progress(0.0)
        self.map_walk_status_label.setText(
            self._t("map_ready_at", "Ready at {start}.").format(start=self.current_route[0])
        )

    def _stop_walk(self) -> None:
        """Stop the walk timer and clear active walking state."""
        self.walk_timer.stop()
        self.is_walking = False

    def _advance_walk(self) -> None:
        """Advance the walking marker one animation step."""
        if len(self.current_route) < 2:
            self.reset_walk()
            return
        self.walking_progress = min(1.0, self.walking_progress + 0.035)
        self.map_canvas.set_walking_progress(self.walking_progress)
        destination = self.current_route[-1]
        if self.walking_progress >= 1.0:
            self._stop_walk()
            self.map_walk_status_label.setText(
                self._t("map_arrived_at", "Arrived at {destination}").format(destination=destination)
            )
        else:
            self.map_walk_status_label.setText(
                self._t("map_walking_to", "Walking to {destination}...").format(destination=destination)
            )

    def _handle_landmark_click(self, landmark: str) -> None:
        """Show clicked landmark context in the route info panel."""
        self.select_landmark(landmark)

    def _handle_database_marker_click(self, marker: dict) -> None:
        """Show clicked database marker context in the route info panel."""
        self._show_database_marker_details(marker)

    def _show_database_marker_details(self, marker: dict) -> None:
        """Render a selected database marker in the existing info panel."""
        self.selected_landmark = None
        self.selected_database_marker = marker
        title = marker.get("title") or marker.get("room_name") or marker.get("room_number") or "Selected place"
        self.map_info_title.setText(str(title))
        self.map_route_info_label.setText(self._t("map_selected_database_marker", "Selected room/location"))
        self.map_selected_place_label.setText(self._database_marker_detail_text(marker))
        self.map_route_steps_label.setText("")
        self.map_set_destination_button.setEnabled(False)

    def _database_marker_detail_text(self, marker: dict) -> str:
        """Format database marker details while skipping missing fields."""
        lines: list[str] = []
        for label, key in (
            ("Room", "room_number"),
            ("Category", "category"),
            ("Building", "building"),
            ("Floor", "floor"),
            ("Description", "description"),
        ):
            value = marker.get(key)
            if value not in (None, ""):
                lines.append(f"{label}: {value}")
        return "\n".join(lines) if lines else "No additional details available."

    def _find_database_marker(self, query: str) -> dict | None:
        """Find a loaded database marker by room name, number, or category."""
        normalized_query = query.strip().casefold()
        if not normalized_query:
            return None
        for marker in self.map_canvas.markers:
            searchable_values = (
                marker.get("title"),
                marker.get("room_name"),
                marker.get("room_number"),
                marker.get("category"),
            )
            if any(
                normalized_query in str(value).casefold()
                for value in searchable_values
                if value not in (None, "")
            ):
                return marker
        return None

    def _distance(self, first: str, second: str) -> float:
        """Return Euclidean distance between two normalized map points."""
        x1, y1 = self.path_points[first]
        x2, y2 = self.path_points[second]
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def _route_distance(self, route: list[str]) -> float:
        """Return total route distance in normalized map units."""
        return sum(self._distance(route[index], route[index + 1]) for index in range(len(route) - 1))

    def _route_steps(self, route: list[str]) -> list[str]:
        """Create simple Google Maps-like walking instructions."""
        if not route:
            return []
        destination = route[-1]
        steps = [self._t("map_step_start", "1. Start at {start}.").format(start=route[0])]
        if "@central_path" in route or "@cafeteria_path" in route:
            steps.append(self._t("map_step_central", "2. Walk toward the central path."))
        elif "@east_path" in route:
            steps.append(self._t("map_step_east", "2. Follow the east campus walkway."))
        else:
            steps.append(self._t("map_step_nearest", "2. Follow the nearest campus walkway."))
        if destination == "Cafeteria":
            steps.append(self._t("map_step_cafeteria", "3. Continue left toward the Cafeteria."))
        elif destination == "Stadium":
            steps.append(self._t("map_step_stadium", "3. Continue toward the stadium path."))
        else:
            steps.append(self._t("map_step_continue", "3. Continue toward {destination}.").format(destination=destination))
        steps.append(self._t("map_step_arrive", "4. Arrive at {destination}.").format(destination=destination))
        return steps

    def _apply_styles(self) -> None:
        """Apply ECU public dashboard styling to the navigation map screen."""
        self.setStyleSheet(
            f"""
            QWidget#map_screen {{
                background-color: {OFF_WHITE};
                color: {TEXT_DARK};
                {font(16)}
            }}

            QLabel#map_title {{
                color: {CHARCOAL};
                {font(28, 850)}
            }}

            QLabel#map_subtitle {{
                color: {TEXT_MUTED};
                {font(15, 600)}
            }}

            QFrame#map_controls_panel,
            QFrame#map_info_panel {{
                background-color: {WHITE};
                border: 1px solid {BORDER};
                border-radius: {px(8)};
            }}

            QLabel#map_control_label {{
                color: {TEXT_MUTED};
                {font(12, 850)}
            }}

            QLineEdit,
            QComboBox {{
                background-color: {WHITE};
                color: {TEXT_DARK};
                border: 1px solid {BORDER};
                border-radius: {px(8)};
                padding: 0 {px(12)};
                min-height: {px(40)};
                {font(13, 750)}
            }}

            QLineEdit:focus {{
                border: 2px solid {ECU_RED};
            }}

            QPushButton {{
                background-color: {WHITE};
                color: {CHARCOAL};
                border: 1px solid {BORDER};
                border-radius: {px(8)};
                padding: 0 {px(12)};
                min-height: {px(40)};
                {font(13, 800)}
            }}

            QPushButton:hover {{
                background-color: #FFF7F7;
                border-color: rgba(215, 25, 32, 120);
            }}

            QPushButton:pressed {{
                background-color: {GOLD_LIGHT};
                color: {CHARCOAL};
            }}

            QPushButton#map_find_route_button,
            QPushButton#map_start_walk_button {{
                background-color: {ECU_RED};
                color: {WHITE};
                border: none;
            }}

            QPushButton#map_find_route_button:hover,
            QPushButton#map_start_walk_button:hover {{
                background-color: {ECU_RED_DARK};
                color: {WHITE};
            }}

            QPushButton#map_find_route_button:pressed,
            QPushButton#map_start_walk_button:pressed {{
                background-color: {CHARCOAL};
                color: {WHITE};
            }}

            QPushButton#map_zoom_in_button,
            QPushButton#map_zoom_out_button {{
                min-width: {px(38)};
                max-width: {px(38)};
                padding: 0;
                {font(17, 850)}
            }}

            QPushButton#map_reset_view_button {{
                min-width: {px(92)};
            }}

            QPushButton:disabled {{
                background-color: {LIGHT_GRAY};
                color: rgba(34, 43, 55, 130);
                border-color: {BORDER};
            }}

            QWidget#map_canvas {{
                background-color: {WHITE};
                border: 1px solid {BORDER};
                border-radius: {px(8)};
            }}

            QLabel#map_info_eyebrow {{
                color: {ECU_RED};
                {font(12, 850)}
            }}

            QLabel#map_info_title {{
                color: {CHARCOAL};
                {font(21, 850)}
            }}

            QLabel#map_route_info_label {{
                color: {TEXT_MUTED};
                {font(14, 650)}
            }}

            QLabel#map_selected_place_label {{
                color: {TEXT_DARK};
                background-color: {OFF_WHITE};
                border: 1px solid {BORDER};
                border-radius: {px(8)};
                padding: {px(12)};
                {font(14, 650)}
            }}

            QLabel#map_route_steps_label {{
                color: {TEXT_DARK};
                background-color: #FFF7F7;
                border: 1px solid rgba(215, 25, 32, 80);
                border-radius: {px(8)};
                padding: {px(12)};
                {font(13, 700)}
            }}

            QLabel#map_walk_status_label {{
                color: {TEXT_DARK};
                background-color: {WHITE};
                border: 1px solid rgba(215, 25, 32, 90);
                border-radius: {px(8)};
                padding: {px(10)};
                {font(13, 800)}
            }}
            """
        )

    def update_language(self, translations: dict[str, str]) -> None:
        """Keep compatibility labels synchronized with language switching."""
        self._translations = translations
        self.map_title.setText(translations["map_title"])
        self.map_subtitle.setText(translations["map_subtitle"])
        self.placeholder_title_label.setText(translations["placeholder_map_title"])
        self.map_search_input.setPlaceholderText(translations["map_search_placeholder"])
        self.map_search_button.setText(translations["map_search_button"])
        self.map_from_label.setText(translations["map_from"])
        self.map_to_label.setText(translations["map_to"])
        self.map_find_route_button.setText(translations["map_find_route"])
        self.map_reset_route_button.setText(translations["map_reset_route"])
        self.map_info_eyebrow.setText(translations["map_info_eyebrow"])
        self.map_set_destination_button.setText(translations["map_set_destination"])
        self.map_start_walk_button.setText(translations["map_start_walk"])
        self.map_pause_walk_button.setText(translations["map_pause_walk"])
        self.map_reset_walk_button.setText(translations["map_reset_walk"])
        if not self.current_route and self.selected_landmark is None:
            self.map_info_title.setText(translations["map_info_title_default"])
            self.map_route_info_label.setText(translations["map_route_info_default"])
            self.map_selected_place_label.setText(translations["map_selected_place_default"])
            self.map_walk_status_label.setText(translations["map_walk_status_default"])
        elif self.selected_landmark is not None and not self.current_route:
            self.select_landmark(self.selected_landmark)
        elif self.current_route:
            self.find_route()

    def _t(self, key: str, fallback: str) -> str:
        """Return translated map copy with a safe fallback."""
        return self._translations.get(key, fallback)
