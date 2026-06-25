"""Shared visual system for the ECU public touchscreen dashboard."""

ECU_RED = "#D71920"
ECU_RED_DARK = "#B9151B"
CHARCOAL = "#202124"
BLACK = "#111827"
WHITE = "#FFFFFF"
OFF_WHITE = "#F7F7F5"
LIGHT_GRAY = "#F1F3F5"
BORDER = "#E5E7EB"
TEXT_DARK = "#1F2937"
TEXT_MUTED = "#6B7280"
SUCCESS = "#16A34A"
WARNING = "#F59E0B"
DANGER = ECU_RED
INFO = "#2563EB"

# Backward-compatible public UI aliases used by existing screens.
NAVY = CHARCOAL
NAVY_DARK = BLACK
NAVY_LIGHT = "#34373C"
GOLD = ECU_RED
GOLD_LIGHT = "#FDE8EA"

FONT_FAMILY = "Segoe UI"
HEADER_FONT_SIZE = 32
TITLE_FONT_SIZE = 26
BODY_FONT_SIZE = 18
SMALL_FONT_SIZE = 14
BUTTON_FONT_SIZE = 17

TOUCH_BUTTON_HEIGHT = 60
BUTTON_HEIGHT = 52
HEADER_HEIGHT = 72
CARD_RADIUS = 18
BUTTON_RADIUS = 16
PAGE_PADDING = 32
CARD_PADDING = 20
SIDEBAR_WIDTH = 220


def px(value: int) -> str:
    """Return an integer measurement formatted for a Qt stylesheet."""
    return f"{value}px"


def font(size: int, weight: int | None = None) -> str:
    """Return shared font-family, size, and optional weight declarations."""
    declarations = f'font-family: "{FONT_FAMILY}"; font-size: {px(size)};'
    if weight is not None:
        declarations += f" font-weight: {weight};"
    return declarations


def min_touch_height() -> str:
    """Return the minimum control height used by touch interactions."""
    return f"min-height: {px(TOUCH_BUTTON_HEIGHT)};"


def compact_height() -> str:
    """Return compact button/input height for dense kiosk toolbars."""
    return f"min-height: {px(BUTTON_HEIGHT)}; max-height: {px(BUTTON_HEIGHT)};"


APP_BACKGROUND_STYLE = f"""
QWidget {{
    background-color: {OFF_WHITE};
    color: {TEXT_DARK};
    {font(BODY_FONT_SIZE)}
}}
""".strip()

HEADER_STYLE = f"""
QLabel {{
    color: {TEXT_DARK};
    {font(HEADER_FONT_SIZE, 850)}
}}
""".strip()

SUBTITLE_STYLE = f"""
QLabel {{
    color: {TEXT_MUTED};
    {font(BODY_FONT_SIZE, 600)}
}}
""".strip()

SIDEBAR_STYLE = f"""
QFrame {{
    background-color: {CHARCOAL};
    border: none;
}}
""".strip()

SIDEBAR_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: #D1D5DB;
    border: none;
    border-left: 4px solid transparent;
    border-radius: {px(10)};
    padding: 0 {px(14)};
    text-align: left;
    {font(14, 700)}
    {compact_height()}
}}
QPushButton:hover {{
    background-color: rgba(255, 255, 255, 18);
    color: {WHITE};
}}
QPushButton:checked {{
    background-color: rgba(215, 25, 32, 34);
    color: {WHITE};
    border-left: 4px solid {ECU_RED};
}}
""".strip()

APP_HEADER_STYLE = f"""
QFrame {{
    background-color: {WHITE};
    border-bottom: 1px solid {BORDER};
}}
""".strip()

PAGE_TITLE_STYLE = f"""
QLabel {{
    color: {TEXT_DARK};
    {font(30, 850)}
}}
""".strip()

COMPACT_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {WHITE};
    color: {TEXT_DARK};
    border: 1px solid {BORDER};
    border-radius: {px(14)};
    padding: 0 {px(16)};
    {font(14, 800)}
    {compact_height()}
}}
QPushButton:hover {{
    border-color: {ECU_RED};
    background-color: #FFF9F9;
}}
QPushButton:pressed {{
    background-color: {GOLD_LIGHT};
}}
""".strip()

PRIMARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {ECU_RED};
    color: {WHITE};
    border: none;
    border-radius: {px(BUTTON_RADIUS)};
    padding: 0 {px(18)};
    {font(15, 800)}
    {compact_height()}
}}
QPushButton:hover {{
    background-color: {ECU_RED_DARK};
}}
QPushButton:pressed {{
    background-color: {ECU_RED_DARK};
    padding-top: {px(2)};
}}
""".strip()

SECONDARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {WHITE};
    color: {TEXT_DARK};
    border: 1px solid {BORDER};
    border-radius: {px(BUTTON_RADIUS)};
    padding: 0 {px(18)};
    {font(15, 750)}
    {compact_height()}
}}
QPushButton:hover {{
    border-color: {ECU_RED};
    background-color: #FFF7F7;
}}
QPushButton:pressed {{
    background-color: {GOLD_LIGHT};
}}
""".strip()

CARD_STYLE = f"""
QFrame {{
    background-color: {WHITE};
    color: {TEXT_DARK};
    border: 1px solid {BORDER};
    border-radius: {px(CARD_RADIUS)};
    padding: {px(CARD_PADDING)};
    {font(BODY_FONT_SIZE)}
}}
""".strip()

FEATURE_CARD_STYLE = f"""
QPushButton {{
    background-color: {WHITE};
    color: {TEXT_DARK};
    border: 1px solid {BORDER};
    border-radius: {px(CARD_RADIUS)};
    padding: {px(18)} {px(CARD_PADDING)};
    text-align: left;
    {font(17, 800)}
}}
QPushButton:hover {{
    border-color: {ECU_RED};
    background-color: #FFF9F9;
}}
QPushButton:pressed {{
    background-color: {GOLD_LIGHT};
}}
""".strip()

GLASS_CARD_STYLE = CARD_STYLE

SEARCH_INPUT_STYLE = f"""
QLineEdit,
QComboBox {{
    background-color: {WHITE};
    color: {TEXT_DARK};
    border: 1px solid {BORDER};
    border-radius: {px(16)};
    padding: 0 {px(CARD_PADDING)};
    {font(15, 700)}
    {compact_height()}
}}
QLineEdit:focus,
QComboBox:focus {{
    border: 2px solid {ECU_RED};
}}
""".strip()

CHIP_STYLE = f"""
QPushButton {{
    background-color: {WHITE};
    color: {TEXT_DARK};
    border: 1px solid {BORDER};
    border-radius: {px(TOUCH_BUTTON_HEIGHT // 2)};
    padding: 0 {px(18)};
    {font(14, 750)}
    {min_touch_height()}
}}
QPushButton:hover {{
    border-color: {ECU_RED};
    background-color: #FFF9F9;
}}
""".strip()

TABLE_STYLE = f"""
QTableWidget {{
    background-color: {WHITE};
    alternate-background-color: {LIGHT_GRAY};
    color: {TEXT_DARK};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    border-radius: {px(CARD_RADIUS)};
    selection-background-color: {GOLD_LIGHT};
    selection-color: {TEXT_DARK};
    {font(14, 550)}
}}
QHeaderView::section {{
    background-color: {CHARCOAL};
    color: {WHITE};
    border: none;
    padding: 10px;
    {font(13, 800)}
}}
""".strip()

FLOATING_CHAT_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {CHARCOAL};
    color: {WHITE};
    border: 2px solid {WHITE};
    border-radius: {px(TOUCH_BUTTON_HEIGHT // 2)};
    {font(BUTTON_FONT_SIZE, 850)}
    {min_touch_height()}
}}
QPushButton:hover {{
    background-color: {BLACK};
    border-color: {ECU_RED};
}}
""".strip()

EMERGENCY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {ECU_RED};
    color: {WHITE};
    border: none;
    border-radius: {px(BUTTON_RADIUS)};
    padding: 0 {px(CARD_PADDING)};
    {font(BUTTON_FONT_SIZE, 850)}
    {min_touch_height()}
}}
QPushButton:hover {{
    background-color: {ECU_RED_DARK};
}}
QPushButton:pressed {{
    background-color: {ECU_RED_DARK};
}}
""".strip()
