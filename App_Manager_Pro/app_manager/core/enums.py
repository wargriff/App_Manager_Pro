"""Énumérations métier."""

from enum import Enum


class AppCategory(str, Enum):
    APP = "app"
    GAME = "game"


class AppSource(str, Enum):
    WINGET = "winget"
    INSTALLED = "installed"
    PORTABLE = "portable"
    REGISTRY = "registry"


class FilterMode(str, Enum):
    ALL = "all"
    APPS = "apps"
    GAMES = "games"
    UPDATES = "updates"


class ScanPhase(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETE = "complete"
