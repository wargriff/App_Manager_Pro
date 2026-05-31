"""Scan des applications (Winget + registre + disque)."""

from __future__ import annotations

import queue
import threading
from typing import TYPE_CHECKING

from app_manager.config import QUEUE_BATCH_SIZE
from app_manager.models.app_item import AppItem
from app_manager.services.scanner import scan_all, stop_scan
from app_manager.services.utils import Utils
from app_manager.services.winget import WingetManager

if TYPE_CHECKING:
    from app_manager.ui.app_ui import AppUI


class ScanManager:

    def __init__(self, ui: "AppUI"):
        self.ui = ui

    def start_scan(self):

        if self.ui.is_scanning:
            return

        self.stop_scan()
        self.ui.reset_data()

        self.ui.is_scanning = True
        self.ui._scan_done = 0

        self.ui.progress.pack(fill="x", pady=(6, 0))
        self.ui.progress.start()

        threading.Thread(target=self._winget_scan, daemon=True).start()
        threading.Thread(target=self._filesystem_scan, daemon=True).start()

    def stop_scan(self):

        self.ui.is_scanning = False

        try:
            stop_scan()
        except Exception:
            pass

        try:
            self.ui.progress.stop()
            self.ui.progress.pack_forget()
        except Exception:
            pass

        self.ui.status.configure(text="⛔ Scan stoppé")

    def _winget_scan(self):

        try:
            for app in WingetManager().get_apps():
                if not self.ui.is_scanning:
                    return
                self.ui.add_item(
                    app.name,
                    None,
                    "winget",
                    app.version,
                    winget_id=app.id,
                )
        finally:
            self.ui.run_on_ui(self._check_scan_complete)

    def _filesystem_scan(self):

        def callback(program):
            if not self.ui.is_scanning:
                return
            size = program.size
            if isinstance(size, int) and size > 0:
                size = Utils.format_size(size)
            self.ui.add_item(
                name=program.name,
                path=program.path,
                source=program.source,
                size=str(size) if size else "installé",
            )

        try:
            scan_all(callback)
        finally:
            self.ui.run_on_ui(self._check_scan_complete)

    def _check_scan_complete(self):

        self.ui._scan_done += 1

        if self.ui._scan_done < 2:
            return

        self.ui.ui_queue.put(self._finish_scan)

    def _finish_scan(self):

        if self.ui._closing:
            return

        self.ui.is_scanning = False

        try:
            self.ui.progress.stop()
            self.ui.progress.pack_forget()
        except Exception:
            pass

        self.ui.apply_filter()
        count = len(self.ui.all_data)
        self.ui.status.configure(text=f"✅ {count} apps")
        self.ui.update_manager.check_updates()

    def process_queue(self):

        if self.ui._closing:
            return

        try:
            processed = 0

            while processed < QUEUE_BATCH_SIZE:
                try:
                    item = self.ui.queue.get_nowait()
                except queue.Empty:
                    break

                key = AppItem.item_key(item)

                if key in self.ui.seen:
                    continue

                self.ui.seen.add(key)
                self.ui.all_data.append(item)

                if item.winget_id:
                    self.ui._winget_by_id[item.winget_id.lower()] = item
                self.ui._winget_by_name[item.name.lower()] = item

                processed += 1

            if processed:
                self.ui.apply_filter()
                self.ui.status.configure(
                    text=f"{len(self.ui.all_data)} apps",
                )

        except Exception as error:
            print("[QUEUE ERROR]", error)

        finally:
            if not self.ui._closing:
                self.ui.safe_after(50, self.process_queue)
