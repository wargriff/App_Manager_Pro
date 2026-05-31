"""Compatibilité — voir app_manager.infrastructure."""

from app_manager.infrastructure import (
    IconManager,
    Uninstaller,
    Utils,
    WingetManager,
    scan_all,
    stop_scan,
)
from app_manager.infrastructure.winget import WingetApp, WingetUpgrade

__all__ = [
    "scan_all",
    "stop_scan",
    "WingetManager",
    "WingetApp",
    "WingetUpgrade",
    "Uninstaller",
    "IconManager",
    "Utils",
]
