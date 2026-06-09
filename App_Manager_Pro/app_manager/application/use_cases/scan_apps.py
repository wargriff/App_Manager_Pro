"""Cas d'usage : scanner les applications installées."""

from __future__ import annotations

import logging
import threading
from typing import Callable

from app_manager.domain.catalog.app_catalog import AppCatalog
from app_manager.domain.models.app_item import AppItem
from app_manager.infrastructure.filesystem import Utils
from app_manager.infrastructure.scanner import scan_all, stop_scan
from app_manager.infrastructure.winget import WingetManager

logger = logging.getLogger("app_manager.scan")


class ScanAppsUseCase:

    def __init__(self, catalog: AppCatalog):
        self.catalog = catalog
        self.is_running = False
        self._done_count = 0
        self._on_stopped = None

    def start(
        self,
        on_item: Callable[[AppItem], None],
        on_complete: Callable[[], None],
        on_stopped: Callable[[], None] | None = None,
    ):

        if self.is_running:
            return

        self.is_running = True
        self._done_count = 0
        self.catalog.reset()

        threading.Thread(
            target=self._winget_scan,
            args=(on_item, on_complete),
            daemon=True,
        ).start()

        threading.Thread(
            target=self._filesystem_scan,
            args=(on_item, on_complete),
            daemon=True,
        ).start()

        self._on_stopped = on_stopped

    def stop(self):

        self.is_running = False
        try:
            stop_scan()
        except Exception as error:
            logger.warning("stop_scan: %s", error)

        if self._on_stopped:
            self._on_stopped()

    def _winget_scan(
        self,
        on_item: Callable[[AppItem], None],
        on_complete: Callable[[], None],
    ):

        try:
            for app in WingetManager().get_apps():
                if not self.is_running:
                    return
                item = AppItem(
                    name=app.name,
                    path=None,
                    source="winget",
                    size=app.version,
                    winget_id=app.id,
                    category=AppItem.detect_category(app.name, None),
                )
                if self.catalog.enqueue(item):
                    on_item(item)
        except Exception as error:
            logger.exception("winget scan: %s", error)
        finally:
            self._signal_complete(on_complete)

    def _filesystem_scan(
        self,
        on_item: Callable[[AppItem], None],
        on_complete: Callable[[], None],
    ):

        def callback(program):

            if not self.is_running:
                return

            size = program.size
            if isinstance(size, int) and size > 0:
                size = Utils.format_size(size)

            item = AppItem(
                name=program.name,
                path=program.path,
                source=program.source,
                size=str(size) if size else "installé",
                category=AppItem.detect_category(
                    program.name,
                    program.path,
                ),
            )

            if self.catalog.enqueue(item):
                on_item(item)

        try:
            scan_all(callback)
        except Exception as error:
            logger.exception("filesystem scan: %s", error)
        finally:
            self._signal_complete(on_complete)

    def _signal_complete(self, on_complete: Callable[[], None]):

        self._done_count += 1
        if self._done_count >= 2:
            self.is_running = False
            on_complete()
