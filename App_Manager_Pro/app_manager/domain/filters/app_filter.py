"""Filtrage et recherche du catalogue."""

from __future__ import annotations

from app_manager.core.enums import FilterMode
from app_manager.domain.models.app_item import AppItem


class AppFilter:

    @staticmethod
    def apply(
        items: list[AppItem],
        mode: FilterMode,
        query: str = "",
    ) -> list[AppItem]:

        base = AppFilter._filter_by_mode(items, mode)

        query = query.lower().strip()
        if not query:
            return base

        return [
            item for item in base
            if query in item.name.lower()
            or (item.path and query in item.path.lower())
        ]

    @staticmethod
    def _filter_by_mode(
        items: list[AppItem],
        mode: FilterMode,
    ) -> list[AppItem]:

        if mode == FilterMode.GAMES:
            return [i for i in items if i.category == "game"]

        if mode == FilterMode.APPS:
            return [i for i in items if i.category == "app"]

        if mode == FilterMode.UPDATES:
            return [i for i in items if i.update_available]

        return items.copy()
