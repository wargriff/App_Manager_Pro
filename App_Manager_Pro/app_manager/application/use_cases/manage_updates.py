"""Cas d'usage : mises à jour Winget."""

from __future__ import annotations

import logging
import threading
from typing import Callable

from app_manager.domain.catalog.app_catalog import AppCatalog
from app_manager.infrastructure.winget import WingetManager

logger = logging.getLogger("app_manager.updates")


class ManageUpdatesUseCase:

    def __init__(self, catalog: AppCatalog):
        self.catalog = catalog
        self.is_checking = False

    def check_updates(self, on_done: Callable[[], None]):

        if self.is_checking:
            return

        self.is_checking = True

        def worker():

            try:
                upgrades = WingetManager().get_upgrades()
                by_id = {u.id.lower(): u for u in upgrades}
                by_name = {u.name.lower(): u for u in upgrades}

                for item in self.catalog.all_items:
                    item.update_available = False
                    item.latest_version = ""

                    up = by_id.get(item.winget_id.lower())
                    if not up:
                        up = by_name.get(item.name.lower())

                    if up:
                        item.update_available = True
                        item.latest_version = up.available
                        if not item.winget_id:
                            item.winget_id = up.id

                self.catalog.refresh_filter()

            except Exception as error:
                logger.exception("check updates: %s", error)

            finally:
                self.is_checking = False
                on_done()

        threading.Thread(target=worker, daemon=True).start()

    def upgrade_one(
        self,
        winget_id: str,
        on_result: Callable[[bool, str], None],
    ):

        def worker():
            ok, msg = WingetManager().upgrade(winget_id)
            on_result(ok, msg)

        threading.Thread(target=worker, daemon=True).start()

    def upgrade_all(self, on_result: Callable[[bool, str], None]):

        def worker():
            ok, msg = WingetManager().upgrade_all()
            on_result(ok, msg)

        threading.Thread(target=worker, daemon=True).start()
