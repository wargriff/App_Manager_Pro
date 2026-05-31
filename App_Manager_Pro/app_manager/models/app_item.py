from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class AppItem:
    name: str
    path: Optional[str]
    source: str
    size: str
    category: str = "app"
    icon: Optional[Any] = None
    _loading_icon: bool = False
    winget_id: str = ""
    update_available: bool = False
    latest_version: str = ""

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
            return "game"
        return "app"
