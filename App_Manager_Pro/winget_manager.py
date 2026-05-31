"""Compatibilité — utiliser app_manager.services.winget."""

from app_manager.services.winget import WingetManager, WingetApp, WingetUpgrade

__all__ = ["WingetManager", "WingetApp", "WingetUpgrade"]
