"""Centralize the visual identity of the ECU public dashboard.

The public dashboard is a touch-friendly kiosk interface designed for quick,
comfortable use on the ECU guidance robot. Its palette uses ECU-style navy
and gold branding, with shared typography, spacing, and reusable
PySide6-compatible stylesheet strings defined in one place.
"""

NAVY = "#0B2A52"
NAVY_DARK = "#081F3D"
NAVY_LIGHT = "#163B6D"
GOLD = "#D4A43B"
GOLD_LIGHT = "#E6BC5A"
WHITE = "#FFFFFF"
OFF_WHITE = "#F7F5F0"
LIGHT_GRAY = "#E8E4DA"
TEXT_DARK = "#10233E"
TEXT_MUTED = "#5C6B80"
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
DANGER = "#EF4444"
INFO = "#38BDF8"

FONT_FAMILY = "Segoe UI"
HEADER_FONT_SIZE = 32
TITLE_FONT_SIZE = 26
BODY_FONT_SIZE = 18
SMALL_FONT_SIZE = 14
BUTTON_FONT_SIZE = 18

TOUCH_BUTTON_HEIGHT = 64
CARD_RADIUS = 22
BUTTON_RADIUS = 16
PAGE_PADDING = 32
CARD_PADDING = 24
SIDEBAR_WIDTH = 252


def px(value: int) -> str:
    """Return an integer measurement formatted for a Qt stylesheet."""
    return f"{value}px"


def font(size: int, weight: int | None = None) -> str:
    """Return shared font-family, size, and optional weight declarations."""
    declarations = (
        f'font-family: "{FONT_FAMILY}"; '
        f"font-size: {px(size)};"
    )
    if weight is not None:
        declarations += f" font-weight: {weight};"
    return declarations


def min_touch_height() -> str:
    """Return the minimum control height used by touch interactions."""
    return f"min-height: {px(TOUCH_BUTTON_HEIGHT)};"


APP_BACKGROUND_STYLE = f"""
QWidget {{
    background-color: {OFF_WHITE};
    color: {WHITE};
    {font(BODY_FONT_SIZE)}
}}
""".strip()

HEADER_STYLE = f"""
QLabel {{
    color: {WHITE};
    {font(HEADER_FONT_SIZE, 700)}
}}
""".strip()

SUBTITLE_STYLE = f"""
QLabel {{
    color: {LIGHT_GRAY};
    {font(BODY_FONT_SIZE)}
}}
""".strip()

PRIMARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {GOLD};
    color: {NAVY_DARK};
    border: none;
    border-radius: {px(BUTTON_RADIUS)};
    padding: 0 {px(CARD_PADDING)};
    {font(BUTTON_FONT_SIZE, 700)}
    {min_touch_height()}
}}
QPushButton:hover {{
    background-color: {GOLD_LIGHT};
}}
QPushButton:pressed {{
    background-color: {GOLD};
    padding-top: {px(2)};
}}
""".strip()

SECONDARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {NAVY_LIGHT};
    color: {WHITE};
    border: 1px solid {INFO};
    border-radius: {px(BUTTON_RADIUS)};
    padding: 0 {px(CARD_PADDING)};
    {font(BUTTON_FONT_SIZE, 600)}
    {min_touch_height()}
}}
QPushButton:hover {{
    background-color: {NAVY};
    border-color: {GOLD_LIGHT};
}}
QPushButton:pressed {{
    background-color: {NAVY_DARK};
}}
""".strip()

CARD_STYLE = f"""
QFrame {{
    background-color: {OFF_WHITE};
    color: {TEXT_DARK};
    border: 1px solid {LIGHT_GRAY};
    border-radius: {px(CARD_RADIUS)};
    padding: {px(CARD_PADDING)};
    {font(BODY_FONT_SIZE)}
}}
""".strip()

GLASS_CARD_STYLE = f"""
QFrame {{
    background-color: {NAVY_LIGHT};
    color: {WHITE};
    border: 1px solid rgba(255, 255, 255, 42);
    border-radius: {px(CARD_RADIUS)};
    padding: {px(CARD_PADDING)};
    {font(BODY_FONT_SIZE)}
}}
""".strip()

SIDEBAR_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {OFF_WHITE};
    border: none;
    border-radius: {px(14)};
    padding: 0 {px(CARD_PADDING)};
    text-align: left;
    {font(BUTTON_FONT_SIZE, 600)}
    {min_touch_height()}
}}
QPushButton:hover {{
    background-color: {NAVY_LIGHT};
}}
QPushButton:checked {{
    background-color: {GOLD};
    color: {TEXT_DARK};
}}
""".strip()

FLOATING_CHAT_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {GOLD};
    color: {NAVY_DARK};
    border: 2px solid {GOLD_LIGHT};
    border-radius: {px(TOUCH_BUTTON_HEIGHT // 2)};
    min-width: {px(TOUCH_BUTTON_HEIGHT)};
    max-width: {px(TOUCH_BUTTON_HEIGHT)};
    {font(BUTTON_FONT_SIZE, 800)}
    {min_touch_height()}
}}
QPushButton:hover {{
    background-color: {GOLD_LIGHT};
}}
QPushButton:pressed {{
    background-color: {GOLD};
}}
""".strip()

EMERGENCY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {DANGER};
    color: {WHITE};
    border: none;
    border-radius: {px(BUTTON_RADIUS)};
    padding: 0 {px(CARD_PADDING)};
    {font(BUTTON_FONT_SIZE, 800)}
    {min_touch_height()}
}}
QPushButton:hover {{
    background-color: #DC2626;
}}
QPushButton:pressed {{
    background-color: #B91C1C;
}}
""".strip()
