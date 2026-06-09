"""Catalogue central des applications détectées."""

from __future__ import annotations

import queue
from queue import Empty

from app_manager.core.enums import FilterMode
from app_manager.domain.dedup.app_deduplicator import (
    are_duplicates,
    dedupe_items,
    is_noise_item,
    merge_items,
    normalize_name,
    normalize_path,
    pick_better,
)
from app_manager.domain.filters.app_filter import AppFilter
from app_manager.domain.models.app_item import AppItem


class AppCatalog:

    def __init__(self):

        self.all_items: list[AppItem] = []
        self.filtered_items: list[AppItem] = []
        self.pending: queue.Queue[AppItem] = queue.Queue()
        self.seen: set[tuple[str, str]] = set()
        self._paths_seen: set[str] = set()
        self._names_index: dict[str, AppItem] = {}
        self._winget_ids_seen: set[str] = set()
        self.filter_mode = FilterMode.ALL
        self.search_query = ""

    def reset(self):

        self.all_items.clear()
        self.filtered_items.clear()
        self.seen.clear()
        self._paths_seen.clear()
        self._names_index.clear()
        self._winget_ids_seen.clear()
        self.pending = queue.Queue()
        self.filter_mode = FilterMode.ALL
        self.search_query = ""

    def enqueue(self, item: AppItem) -> bool:

        if is_noise_item(item):
            return False

        path_key = normalize_path(item.path)

        if path_key and path_key in self._paths_seen:
            return False

        winget_key = item.winget_id.lower().strip()

        if winget_key and winget_key in self._winget_ids_seen:
            return False

        name_key = normalize_name(item.name)

        if name_key and name_key in self._names_index:

            existing = self._names_index[name_key]

            if are_duplicates(item, existing):

                better = pick_better(existing, item)
                worse = item if better is existing else existing
                merge_items(better, worse)

                if better is not existing:
                    self._replace_in_catalog(existing, better)

                return False

        # Doublon par chemin / nom proche dans le catalogue actuel
        for existing in self.all_items:

            if are_duplicates(item, existing):

                better = pick_better(existing, item)
                worse = item if better is existing else existing
                merge_items(better, worse)

                if better is not existing:
                    self._replace_in_catalog(existing, better)

                return False

        key = AppItem.item_key(item)

        if key in self.seen:
            return False

        self.seen.add(key)

        if path_key:
            self._paths_seen.add(path_key)

        if winget_key:
            self._winget_ids_seen.add(winget_key)

        if name_key:
            self._names_index[name_key] = item

        self.pending.put(item)
        return True

    def _replace_in_catalog(self, old: AppItem, new: AppItem) -> None:

        try:
            index = self.all_items.index(old)
            self.all_items[index] = new
        except ValueError:
            pass

        old_key = normalize_name(old.name)
        new_key = normalize_name(new.name)

        if old_key in self._names_index:
            del self._names_index[old_key]

        if new_key:
            self._names_index[new_key] = new

        self.seen.discard(AppItem.item_key(old))
        self.seen.add(AppItem.item_key(new))

        old_path = normalize_path(old.path)
        new_path = normalize_path(new.path)

        if old_path:
            self._paths_seen.discard(old_path)

        if new_path:
            self._paths_seen.add(new_path)

    def drain_pending(self, limit: int) -> int:

        added = 0

        while added < limit:
            try:
                item = self.pending.get_nowait()
            except Empty:
                break

            if not self._accept_into_list(item):
                continue

            self.all_items.append(item)
            added += 1

        if added:
            self.refresh_filter()

        return added

    def _accept_into_list(self, item: AppItem) -> bool:

        for existing in self.all_items:

            if are_duplicates(item, existing):

                better = pick_better(existing, item)
                merge_items(better, item if better is existing else existing)
                return False

        return True

    def deduplicate_all(self) -> int:

        before = len(self.all_items)
        self.all_items = dedupe_items(self.all_items)

        self._rebuild_indexes()
        self.refresh_filter()

        return before - len(self.all_items)

    def _rebuild_indexes(self):

        self.seen.clear()
        self._paths_seen.clear()
        self._names_index.clear()
        self._winget_ids_seen.clear()

        for item in self.all_items:

            self.seen.add(AppItem.item_key(item))

            path_key = normalize_path(item.path)

            if path_key:
                self._paths_seen.add(path_key)

            name_key = normalize_name(item.name)

            if name_key:
                self._names_index[name_key] = item

            if item.winget_id:
                self._winget_ids_seen.add(item.winget_id.lower())

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
        self._rebuild_indexes()
        self.refresh_filter()

    @property
    def update_count(self) -> int:
        return sum(1 for i in self.all_items if i.update_available)
