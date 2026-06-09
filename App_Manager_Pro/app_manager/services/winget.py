"""Alias → infrastructure.winget."""

from app_manager.infrastructure.winget.client import *  # noqa: F403
from app_manager.infrastructure.winget import WingetApp, WingetManager, WingetUpgrade

__all__ = ["WingetApp", "WingetManager", "WingetUpgrade"]
