"""Catalogue central des applications détectées."""

from __future__ import annotations

import queue
from queue import Empty

from app_manager.core.enums import FilterMode
from app_manager.domain.filters.app_filter import AppFilter
from app_manager.domain.models.app_item import AppItem


class AppCatalog:

    def __init__(self):

        self.all_items: list[AppItem] = []
        self.filtered_items: list[AppItem] = []
        self.pending: queue.Queue[AppItem] = queue.Queue()
        self.seen: set[tuple[str, str]] = set()
        self.filter_mode = FilterMode.ALL
        self.search_query = ""

    def reset(self):

        self.all_items.clear()
        self.filtered_items.clear()
        self.seen.clear()
        self.pending = queue.Queue()
        self.filter_mode = FilterMode.ALL
        self.search_query = ""

    def enqueue(self, item: AppItem) -> bool:

        key = AppItem.item_key(item)

        if key in self.seen:
            return False

        self.seen.add(key)
        self.pending.put(item)
        return True

    def drain_pending(self, limit: int) -> int:

        added = 0

        while added < limit:
            try:
                item = self.pending.get_nowait()
            except Empty:
                break

            self.all_items.append(item)
            added += 1

        if added:
            self.refresh_filter()

        return added

    def set_filter_mode(self, mode: FilterMode):

        self.filter_mode = mode
        self.refresh_filter()

    def set_search(self, query: str):

        self.search_query = query
        self.refresh_filter()

    def refresh_filter(self):

        self.filtered_items = AppFilter.apply(
            self.all_items,
            self.filter_mode,
            self.search_query,
        )

    def remove_item(self, item: AppItem):

        key = AppItem.item_key(item)
        self.all_items = [
            i for i in self.all_items if AppItem.item_key(i) != key
        ]
        self.seen.discard(key)
        self.refresh_filter()

    @property
    def update_count(self) -> int:
        return sum(1 for i in self.all_items if i.update_available)
