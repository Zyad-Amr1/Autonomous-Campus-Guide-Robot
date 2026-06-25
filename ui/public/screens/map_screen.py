"""Public campus map screen with a professional placeholder canvas."""

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
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
from database.connection import DB_NAME
from database.repositories.room_repository import get_all_rooms


CATEGORY_COLORS = {
    "labs": "#2F80ED",
    "laboratory": "#2F80ED",
    "laboratories": "#2F80ED",
    "offices": "#8E5CF7",
    "office": "#8E5CF7",
    "clinics": "#D94D45",
    "clinic": "#D94D45",
    "medical": "#D94D45",
    "library": "#3BAA6B",
    "cafeteria": "#E67E22",
    "other": GOLD,
}


class MapCanvas(QWidget):
    """Draw a static, polished 2D placeholder campus map."""

    def __init__(self) -> None:
        """Create the custom map canvas."""
        super().__init__()
        self.setObjectName("map_canvas")
        self.setMinimumSize(620, 440)
        self.background_image_path: str | None = None
        self._background_pixmap = QPixmap()
        self.markers: list[dict] = []
        self.selected_marker: dict | None = None
        self.marker_clicked = None
        self._marker_hit_radius = 16
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def set_background_image(self, path: str) -> None:
        """Set a future real campus image path and repaint the canvas."""
        self.background_image_path = path
        image_path = Path(path)
        self._background_pixmap = (
            QPixmap(str(image_path)) if image_path.exists() else QPixmap()
        )
        self.update()

    def set_markers(self, rooms: list[dict]) -> None:
        """Replace visible room markers with mappable room dictionaries."""
        self.markers = [room for room in rooms if self._has_valid_coordinates(room)]
        self.selected_marker = None
        self.update()

    def marker_color(self, category: str | None) -> str:
        """Return the display color for one marker category."""
        normalized = (category or "other").strip().lower()
        return CATEGORY_COLORS.get(normalized, CATEGORY_COLORS["other"])

    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint an illustrative campus map without loading real markers."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(16, 16, -16, -16)
        painter.setPen(QPen(QColor("#D8D2C5"), 1))
        painter.setBrush(QColor("#ECE8DC"))
        painter.drawRoundedRect(rect, 24, 24)
        if not self._background_pixmap.isNull():
            self._draw_background_image(painter, rect)
            self._draw_room_markers(painter, QRectF(rect))
            return

        self._draw_landscape(painter, QRectF(rect))
        self._draw_roads(painter, QRectF(rect))
        self._draw_walkways(painter, QRectF(rect))
        self._draw_buildings(painter, QRectF(rect))
        if self.markers:
            self._draw_room_markers(painter, QRectF(rect))
        else:
            self._draw_placeholder_markers(painter, QRectF(rect))

    def _draw_background_image(self, painter: QPainter, rect) -> None:
        """Draw a real campus image scaled neatly inside the canvas."""
        scaled = self._background_pixmap.scaled(
            rect.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        target_x = rect.x() + (rect.width() - scaled.width()) // 2
        target_y = rect.y() + (rect.height() - scaled.height()) // 2
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(rect), 24, 24)
        painter.save()
        painter.setClipPath(clip_path)
        painter.drawPixmap(target_x, target_y, scaled)
        painter.restore()

    def _draw_landscape(self, painter: QPainter, rect: QRectF) -> None:
        """Draw soft green zones and a central plaza."""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#DCE7D6"))
        painter.drawEllipse(QRectF(rect.left() + 26, rect.top() + 34, 210, 135))
        painter.drawEllipse(QRectF(rect.right() - 236, rect.bottom() - 164, 210, 126))
        painter.setBrush(QColor("#C8DDC2"))
        for x, y in (
            (0.18, 0.16),
            (0.28, 0.78),
            (0.64, 0.18),
            (0.76, 0.55),
            (0.88, 0.82),
        ):
            center = QPointF(
                rect.left() + rect.width() * x,
                rect.top() + rect.height() * y,
            )
            painter.drawEllipse(center, 14, 14)

        plaza = QRectF(
            rect.center().x() - 86,
            rect.center().y() - 58,
            172,
            116,
        )
        painter.setBrush(QColor("#E8D9B8"))
        painter.drawRoundedRect(plaza, 28, 28)
        painter.setPen(QPen(QColor(GOLD), 2))
        painter.drawEllipse(plaza.adjusted(38, 18, -38, -18))

    def _draw_roads(self, painter: QPainter, rect: QRectF) -> None:
        """Draw soft road bands around the simulated campus blocks."""
        painter.setPen(
            QPen(
                QColor("#C8C1B2"),
                22,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        painter.drawLine(
            QPointF(rect.left() + 34, rect.top() + 58),
            QPointF(rect.right() - 34, rect.top() + 58),
        )
        painter.drawLine(
            QPointF(rect.left() + 42, rect.bottom() - 58),
            QPointF(rect.right() - 42, rect.bottom() - 58),
        )
        painter.setPen(
            QPen(
                QColor("#F6F2E8"),
                4,
                Qt.PenStyle.DashLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        painter.drawLine(
            QPointF(rect.left() + 42, rect.top() + 58),
            QPointF(rect.right() - 42, rect.top() + 58),
        )
        painter.drawLine(
            QPointF(rect.left() + 50, rect.bottom() - 58),
            QPointF(rect.right() - 50, rect.bottom() - 58),
        )

    def _draw_walkways(self, painter: QPainter, rect: QRectF) -> None:
        """Draw light curved pedestrian paths through the campus."""
        painter.setPen(QPen(QColor("#F9F7F0"), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        path = QPainterPath(QPointF(rect.left() + 48, rect.center().y()))
        path.cubicTo(
            QPointF(rect.left() + 220, rect.top() + 120),
            QPointF(rect.right() - 220, rect.bottom() - 120),
            QPointF(rect.right() - 48, rect.center().y()),
        )
        painter.drawPath(path)

        painter.setPen(QPen(QColor("#CDBE95"), 2, Qt.PenStyle.DashLine))
        painter.drawPath(path)

        painter.setPen(QPen(QColor("#F9F7F0"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        vertical_path = QPainterPath(QPointF(rect.center().x(), rect.top() + 42))
        vertical_path.cubicTo(
            QPointF(rect.center().x() - 82, rect.top() + 150),
            QPointF(rect.center().x() + 82, rect.bottom() - 150),
            QPointF(rect.center().x(), rect.bottom() - 42),
        )
        painter.drawPath(vertical_path)

    def _draw_buildings(self, painter: QPainter, rect: QRectF) -> None:
        """Draw navy campus building blocks and labels."""
        buildings = (
            ("Engineering\nBuilding", 0.08, 0.20, 0.24, 0.18),
            ("Science\nComplex", 0.38, 0.12, 0.24, 0.17),
            ("Library", 0.68, 0.20, 0.21, 0.18),
            ("Administration", 0.10, 0.62, 0.24, 0.17),
            ("Health\nCenter", 0.42, 0.66, 0.20, 0.16),
            ("Student\nCenter", 0.69, 0.60, 0.22, 0.19),
        )
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        for label, x, y, width, height in buildings:
            building_rect = QRectF(
                rect.left() + rect.width() * x,
                rect.top() + rect.height() * y,
                rect.width() * width,
                rect.height() * height,
            )
            painter.setPen(QPen(QColor("#071B35"), 1))
            painter.setBrush(QColor(NAVY))
            painter.drawRoundedRect(building_rect, 14, 14)
            painter.setPen(QColor(WHITE))
            painter.drawText(
                building_rect.adjusted(10, 8, -10, -8),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )

    def _draw_placeholder_markers(self, painter: QPainter, rect: QRectF) -> None:
        """Draw simple placeholder colored markers."""
        markers = (
            ("i", 0.20, 0.43, GOLD),
            ("L", 0.78, 0.42, "#3BAA6B"),
            ("+", 0.53, 0.58, "#D94D45"),
            ("C", 0.82, 0.74, "#2F80ED"),
        )
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        for label, x, y, color in markers:
            center = QPointF(
                rect.left() + rect.width() * x,
                rect.top() + rect.height() * y,
            )
            painter.setPen(QPen(QColor(WHITE), 3))
            painter.setBrush(QColor(color))
            painter.drawEllipse(center, 13, 13)
            painter.setPen(QColor(WHITE))
            painter.drawText(
                QRectF(center.x() - 12, center.y() - 12, 24, 24),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )

    def _draw_room_markers(self, painter: QPainter, rect: QRectF) -> None:
        """Draw database-backed room markers on the active map surface."""
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        for marker in self.markers:
            center = self._marker_center(marker, rect)
            is_selected = marker is self.selected_marker
            radius = 18 if is_selected else 14
            painter.setPen(QPen(QColor(WHITE), 4 if is_selected else 3))
            painter.setBrush(QColor(self.marker_color(marker.get("category"))))
            painter.drawEllipse(center, radius, radius)
            painter.setPen(QColor(WHITE))
            painter.drawText(
                QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2),
                Qt.AlignmentFlag.AlignCenter,
                self._marker_initial(marker),
            )

    def mousePressEvent(self, event) -> None:  # noqa: N802
        """Select a room marker when a user taps near it."""
        canvas_rect = QRectF(self.rect().adjusted(16, 16, -16, -16))
        for marker in reversed(self.markers):
            center = self._marker_center(marker, canvas_rect)
            delta = center - event.position()
            if (
                delta.x() * delta.x() + delta.y() * delta.y()
                <= self._marker_hit_radius * self._marker_hit_radius
            ):
                self.select_marker(marker)
                return
        super().mousePressEvent(event)

    def select_marker(self, marker: dict) -> None:
        """Set the active marker and notify the optional owner callback."""
        self.selected_marker = marker
        self.update()
        if self.marker_clicked is not None:
            self.marker_clicked(marker)

    def _marker_center(self, marker: dict, rect: QRectF) -> QPointF:
        """Translate normalized room coordinates into canvas coordinates."""
        x_value = float(marker["x_coord"])
        y_value = float(marker["y_coord"])
        if x_value > 1 or y_value > 1:
            x_value /= 100.0
            y_value /= 100.0
        x_value = min(max(x_value, 0.0), 1.0)
        y_value = min(max(y_value, 0.0), 1.0)
        return QPointF(
            rect.left() + rect.width() * x_value,
            rect.top() + rect.height() * y_value,
        )

    def _marker_initial(self, marker: dict) -> str:
        """Return a compact marker label."""
        room_name = str(marker.get("room_name") or marker.get("room_number") or "?")
        return room_name[:1].upper()

    def _has_valid_coordinates(self, room: dict) -> bool:
        """Return whether a room has usable x/y marker coordinates."""
        try:
            if room.get("x_coord") is None or room.get("y_coord") is None:
                return False
            float(room["x_coord"])
            float(room["y_coord"])
            return True
        except AttributeError:
            return False
        except (TypeError, ValueError):
            return False


class MapScreen(QWidget):
    """Display the public campus map search, filters, canvas, and info panel."""

    FILTERS = (
        ("All", "filter_all_button"),
        ("Labs", "filter_labs_button"),
        ("Offices", "filter_offices_button"),
        ("Clinics", "filter_clinics_button"),
        ("Library", "filter_library_button"),
        ("Cafeteria", "filter_cafeteria_button"),
        ("Other", "filter_other_button"),
    )

    def __init__(self, db_path=DB_NAME) -> None:
        """Create the map screen without touching real map data."""
        super().__init__()
        self.db_path = db_path
        self.setObjectName("map_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._apply_styles()
        self.load_room_markers()

    def _build_ui(self) -> None:
        """Arrange the map header, controls, canvas, and info panel."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(PAGE_PADDING + 8, PAGE_PADDING, PAGE_PADDING + 8, PAGE_PADDING)
        page_layout.setSpacing(16)

        self.map_title = QLabel("Campus Map")
        self.map_title.setObjectName("map_title")
        self.map_subtitle = QLabel("Find rooms, buildings, offices, and important places.")
        self.map_subtitle.setObjectName("map_subtitle")
        self.map_subtitle.setWordWrap(True)
        self.placeholder_title_label = QLabel("Campus Map", self)
        self.placeholder_title_label.setObjectName("placeholder_title_label")
        self.placeholder_title_label.hide()
        page_layout.addWidget(self.map_title)
        page_layout.addWidget(self.map_subtitle)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        self.map_search_input = QLineEdit()
        self.map_search_input.setObjectName("map_search_input")
        self.map_search_input.setPlaceholderText("Search for a room, lab, office...")
        self.map_search_input.setMinimumHeight(TOUCH_BUTTON_HEIGHT)
        controls_layout.addWidget(self.map_search_input, stretch=1)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        self.filter_buttons: dict[str, QPushButton] = {}
        for label, object_name in self.FILTERS:
            button = QPushButton(label)
            button.setObjectName(object_name)
            button.setCheckable(True)
            button.setMinimumHeight(46)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            if label == "All":
                button.setChecked(True)
            self.filter_buttons[object_name] = button
            setattr(self, object_name, button)
            filter_layout.addWidget(button)
        page_layout.addLayout(controls_layout)
        page_layout.addLayout(filter_layout)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(18)
        self.map_canvas = MapCanvas()
        self.map_canvas.marker_clicked = self.update_selected_room
        body_layout.addWidget(self.map_canvas, stretch=3)
        body_layout.addWidget(self._create_info_panel(), stretch=1)
        page_layout.addLayout(body_layout, stretch=1)

    def _create_info_panel(self) -> QFrame:
        """Create the right-side selected-location placeholder panel."""
        self.map_info_panel = QFrame()
        self.map_info_panel.setObjectName("map_info_panel")
        self.map_info_panel.setMinimumWidth(280)
        panel_layout = QVBoxLayout(self.map_info_panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(12)

        eyebrow = QLabel("Selected Location")
        eyebrow.setObjectName("map_info_eyebrow")
        self.map_info_title = QLabel("Select a place")
        self.map_info_title.setObjectName("map_info_title")
        self.map_info_details = QLabel("Tap a marker on the map to view details.")
        self.map_info_details.setObjectName("map_info_details")
        self.map_info_details.setWordWrap(True)

        panel_layout.addWidget(eyebrow)
        panel_layout.addWidget(self.map_info_title)
        panel_layout.addWidget(self.map_info_details)
        panel_layout.addStretch()
        return self.map_info_panel

    def load_room_markers(self) -> None:
        """Load mappable room records from the configured database."""
        try:
            rooms = get_all_rooms(self.db_path)
        except Exception:
            self.map_canvas.set_markers([])
            return
        markers = [self._room_to_marker(room) for room in rooms]
        self.map_canvas.set_markers(
            [marker for marker in markers if marker is not None]
        )

    def update_selected_room(self, marker: dict) -> None:
        """Update the right info panel with the selected room details."""
        self.map_info_title.setText(str(marker.get("room_name") or "Selected room"))
        details = (
            f"Room number: {marker.get('room_number') or 'N/A'}\n"
            f"Building: {marker.get('building') or 'N/A'}\n"
            f"Floor: {marker.get('floor') if marker.get('floor') is not None else 'N/A'}\n"
            f"Category: {marker.get('category') or 'Other'}\n\n"
            f"{marker.get('description') or 'No description available yet.'}"
        )
        self.map_info_details.setText(details)

    def _room_to_marker(self, room) -> dict | None:
        """Convert a repository room row into a marker dictionary."""
        marker = dict(room)
        if marker.get("x_coord") is None or marker.get("y_coord") is None:
            return None
        try:
            marker["x_coord"] = float(marker["x_coord"])
            marker["y_coord"] = float(marker["y_coord"])
        except (TypeError, ValueError):
            return None
        return marker

    def _apply_styles(self) -> None:
        """Apply ECU public dashboard styling to the map screen."""
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

            QLineEdit#map_search_input {{
                background-color: {WHITE};
                color: {TEXT_DARK};
                border: 1px solid rgba(92, 107, 128, 80);
                border-radius: {px(18)};
                padding: 0 {px(CARD_PADDING)};
                {font(16, 650)}
            }}

            QLineEdit#map_search_input:focus {{
                border: 2px solid {GOLD};
            }}

            QPushButton {{
                background-color: {WHITE};
                color: {TEXT_DARK};
                border: 1px solid rgba(92, 107, 128, 70);
                border-radius: {px(16)};
                padding: 0 {px(16)};
                {font(14, 750)}
            }}

            QPushButton:hover {{
                border-color: {GOLD};
                background-color: {OFF_WHITE};
            }}

            QPushButton:checked {{
                background-color: {NAVY};
                border-color: {NAVY};
                color: {WHITE};
            }}

            QWidget#map_canvas {{
                background-color: #ECE8DC;
                border: 1px solid rgba(92, 107, 128, 70);
                border-radius: {px(CARD_RADIUS + 4)};
            }}

            QFrame#map_info_panel {{
                background-color: {WHITE};
                border: 1px solid rgba(92, 107, 128, 70);
                border-radius: {px(CARD_RADIUS)};
            }}

            QLabel#map_info_eyebrow {{
                color: {GOLD};
                {font(12, 850)}
            }}

            QLabel#map_info_title {{
                color: {NAVY_DARK};
                {font(24, 850)}
            }}

            QLabel#map_info_message,
            QLabel#map_info_details {{
                color: {TEXT_MUTED};
                {font(15, 600)}
            }}
            """
        )

    def update_language(self, translations: dict[str, str]) -> None:
        """Keep compatibility labels synchronized with language switching."""
        self.placeholder_title_label.setText(translations["placeholder_map_title"])
