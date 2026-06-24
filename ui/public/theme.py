"""Centralize the visual identity of the ECU public dashboard.

The public dashboard is a touch-friendly kiosk interface designed for quick,
comfortable use on the ECU guidance robot. Its palette uses ECU-style navy
and gold branding, with shared typography, spacing, and reusable
PySide6-compatible stylesheet strings defined in one place.
"""

NAVY = "#0B2545"
NAVY_DARK = "#061A33"
NAVY_LIGHT = "#153B66"
GOLD = "#D9A441"
GOLD_LIGHT = "#F4C95D"
WHITE = "#FFFFFF"
OFF_WHITE = "#F8FAFC"
LIGHT_GRAY = "#E5E7EB"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#64748B"
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
CARD_RADIUS = 24
BUTTON_RADIUS = 18
PAGE_PADDING = 32
CARD_PADDING = 24
SIDEBAR_WIDTH = 240


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
    background-color: {NAVY_DARK};
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
    background-color: rgba(21, 59, 102, 210);
    color: {WHITE};
    border: 1px solid rgba(255, 255, 255, 55);
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
    border-radius: {px(BUTTON_RADIUS)};
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
    color: {NAVY_DARK};
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
