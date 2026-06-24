"""Tests for the shared public dashboard theme contract."""

import re

from ui.public import theme


COLOR_NAMES = (
    "NAVY",
    "NAVY_DARK",
    "NAVY_LIGHT",
    "GOLD",
    "GOLD_LIGHT",
    "WHITE",
    "OFF_WHITE",
    "LIGHT_GRAY",
    "TEXT_DARK",
    "TEXT_MUTED",
    "SUCCESS",
    "WARNING",
    "DANGER",
    "INFO",
)

STYLE_NAMES = (
    "APP_BACKGROUND_STYLE",
    "HEADER_STYLE",
    "PRIMARY_BUTTON_STYLE",
    "SECONDARY_BUTTON_STYLE",
    "CARD_STYLE",
    "GLASS_CARD_STYLE",
    "SIDEBAR_BUTTON_STYLE",
    "FLOATING_CHAT_BUTTON_STYLE",
    "EMERGENCY_BUTTON_STYLE",
)


def test_public_theme_imports_successfully() -> None:
    assert theme is not None


def test_public_theme_colors_are_valid_hex_strings() -> None:
    for name in COLOR_NAMES:
        value = getattr(theme, name)
        assert isinstance(value, str)
        assert re.fullmatch(r"#[0-9A-Fa-f]{6}", value)


def test_public_theme_font_family_is_defined() -> None:
    assert isinstance(theme.FONT_FAMILY, str)
    assert theme.FONT_FAMILY.strip()


def test_public_theme_touch_height_is_kiosk_friendly() -> None:
    assert theme.TOUCH_BUTTON_HEIGHT >= 60


def test_public_theme_radii_are_positive_integers() -> None:
    assert isinstance(theme.CARD_RADIUS, int)
    assert isinstance(theme.BUTTON_RADIUS, int)
    assert theme.CARD_RADIUS > 0
    assert theme.BUTTON_RADIUS > 0


def test_public_theme_required_styles_are_non_empty() -> None:
    for name in STYLE_NAMES:
        value = getattr(theme, name)
        assert isinstance(value, str)
        assert value.strip()


def test_px_formats_integer_measurements() -> None:
    assert theme.px(12) == "12px"


def test_font_includes_requested_size() -> None:
    assert "font-size: 18px" in theme.font(18)


def test_min_touch_height_uses_theme_constant() -> None:
    assert str(theme.TOUCH_BUTTON_HEIGHT) in theme.min_touch_height()
