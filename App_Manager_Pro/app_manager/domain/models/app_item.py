from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app_manager.core.enums import AppCategory


@dataclass(slots=True)
class AppItem:
    name: str
    path: Optional[str]
    source: str
    size: str
    category: str = AppCategory.APP.value
    icon: Optional[Any] = None
    winget_id: str = ""
    update_available: bool = False
    latest_version: str = ""
    _loading_icon: bool = field(default=False, repr=False)

    @staticmethod
    def item_key(item: "AppItem") -> tuple[str, str]:
        return (
            item.name.lower(),
            (item.path or "").lower(),
        )

    @staticmethod
    def detect_category(name: str, path: Optional[str]) -> str:
        text = f"{name} {path or ''}".lower()
        keywords = {
            "steam", "steamapps", "epic", "riot", "valorant",
            "league of legends", "ubisoft", "uplay",
            "battle.net", "blizzard", "game",
        }
        if any(k in text for k in keywords):
            return AppCategory.GAME.value
        return AppCategory.APP.value

    def display_info(self) -> str:
        if self.update_available and self.latest_version:
            return f"{self.source} • v{self.size} → v{self.latest_version}"
        return f"{self.source} • {self.size}"
