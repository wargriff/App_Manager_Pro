"""Contrôleur du scan d'applications."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app_manager.application.use_cases.scan_apps import ScanAppsUseCase
from app_manager.config.settings import QUEUE_BATCH_SIZE
from app_manager.core.enums import FilterMode
from app_manager.domain.models.app_item import AppItem

if TYPE_CHECKING:
    from app_manager.presentation.main_window import MainWindow


class ScanController:

    def __init__(self, view: "MainWindow"):
        self.view = view
        self.use_case = ScanAppsUseCase(view.catalog)

    def start_scan(self):

        if self.use_case.is_running:
            return

        self.view.reset_view()
        self.view.status_bar.show_progress()
        self.view.status_bar.set_text("🔄 Scan en cours...")

        self.use_case.start(
            on_item=lambda _: None,
            on_complete=lambda: self.view.run_on_ui(self._on_scan_complete),
            on_stopped=lambda: self.view.run_on_ui(self._on_scan_stopped),
        )

    def stop_scan(self):
        self.use_case.stop()

    def _on_scan_stopped(self):
        self.view.status_bar.hide_progress()
        self.view.status_bar.set_text("⛔ Scan stoppé")

    def _on_scan_complete(self):
        self.view.status_bar.hide_progress()

        removed = self.view.catalog.deduplicate_all()
        count = len(self.view.catalog.all_items)

        if removed:
            self.view.status_bar.set_text(
                f"✅ {count} apps ({removed} doublons retirés)",
            )
        else:
            self.view.status_bar.set_text(f"✅ {count} apps")

        self.view.sync_list()
        self.view.update_controller.check_updates()

    def process_queue(self):

        if self.view._closing:
            return

        added = self.view.catalog.drain_pending(QUEUE_BATCH_SIZE)

        if added:
            self.view.sync_list()
            self.view.status_bar.set_text(
                f"{len(self.view.catalog.all_items)} apps",
            )

        if not self.view._closing:
            self.view.safe_after(50, self.process_queue)
