"""Thème visuel — couleurs et polices."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Theme:
    bg_dark: str = "#0d0d0d"
    bg_main: str = "#121212"
    bg_row: str = "#1e1e1e"
    bg_row_alt: str = "#222222"
    accent: str = "#00ff88"
    accent_muted: str = "#666666"
    text_primary: str = "#ffffff"
    text_secondary: str = "#aaaaaa"
    text_muted: str = "#888888"
    warning: str = "#ffaa00"
    success: str = "#0d5c0d"
    danger: str = "#7a0c0c"
    update_btn: str = "#1a4a7a"
    update_btn_hover: str = "#2563a8"
    font_title: tuple = ("Segoe UI", 22, "bold")
    font_subtitle: tuple = ("Segoe UI", 11)
    font_body: tuple = ("Segoe UI", 13)
    font_row_title: tuple = ("Segoe UI", 12, "bold")
    font_row_info: tuple = ("Segoe UI", 10)
    font_status: tuple = ("Segoe UI", 12)


THEME = Theme()
