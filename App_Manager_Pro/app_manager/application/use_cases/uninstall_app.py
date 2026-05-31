"""Cas d'usage : désinstaller une application."""

from __future__ import annotations

import logging
import threading
from typing import Callable

from app_manager.domain.models.app_item import AppItem
from app_manager.infrastructure.uninstall import Uninstaller
from app_manager.infrastructure.winget import WingetManager

logger = logging.getLogger("app_manager.uninstall")


class UninstallAppUseCase:

    @staticmethod
    def run(
        item: AppItem,
        on_result: Callable[[bool, str], None],
    ):

        def worker():

            try:
                if item.source == "winget" and item.winget_id:
                    ok, msg = WingetManager().uninstall(item.winget_id)
                elif item.source == "winget":
                    ok, msg = WingetManager().uninstall(item.name)
                else:
                    ok, msg = Uninstaller.uninstall(item.name, item.path)
                    ok = bool(ok)

            except Exception as error:
                logger.exception("uninstall: %s", error)
                ok, msg = False, str(error)

            on_result(ok, msg)

        threading.Thread(target=worker, daemon=True).start()
