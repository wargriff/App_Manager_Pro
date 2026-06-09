# main_window.py — fenêtre principale (présentation)

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from app_manager.application.use_cases.uninstall_app import UninstallAppUseCase
from app_manager.config.theme import THEME
from app_manager.core.enums import FilterMode
from app_manager.domain.catalog.app_catalog import AppCatalog
from app_manager.domain.models.app_item import AppItem
from app_manager.infrastructure.icons import IconManager
from app_manager.infrastructure.scanner import stop_scan
from app_manager.presentation.components import SearchBar, Sidebar, StatusBar
from app_manager.presentation.controllers import ScanController, UpdateController
from app_manager.presentation.widgets import RowFactory, VirtualList


class MainWindow:

    def __init__(self, root: ctk.CTk):

        self.root = root
        self.catalog = AppCatalog()
        self.ui_queue: queue.Queue = queue.Queue()
        self.icon_manager = IconManager()
        self.icon_cache: dict[str, Any] = {}
        self.after_ids: set[str] = set()
        self._icon_requested: set[str] = set()
        self._closing = False

        self.virtual_list: VirtualList | None = None
        self.sidebar: Sidebar | None = None
        self.search_bar: SearchBar | None = None
        self.status_bar: StatusBar | None = None

        self.row_factory = RowFactory(self)
        self.scan_controller = ScanController(self)
        self.update_controller = UpdateController(self)

        self._build_layout()

        self.safe_after(50, self.scan_controller.process_queue)
        self.safe_after(50, self._process_ui_queue)
        self.safe_after(200, self.scan_controller.start_scan)

    def _build_layout(self):

        self.sidebar = Sidebar(self.root, self.handle_action)

        main = ctk.CTkFrame(self.root, fg_color=THEME.bg_main, corner_radius=0)
        main.pack(side="right", fill="both", expand=True)

        self.search_bar = SearchBar(main, self._on_search_changed)

        list_frame = ctk.CTkFrame(main, fg_color=THEME.bg_main)
        list_frame.pack(fill="both", expand=True, padx=16, pady=4)

        self.virtual_list = VirtualList(
            list_frame,
            self.row_factory.build_row,
        )

        self.status_bar = StatusBar(main)

    def handle_action(self, action: str):

        if action == "scan":
            self.scan_controller.start_scan()
            return

        if action == "stop":
            self.scan_controller.stop_scan()
            return

        if action == "upgrade_all":
            self.update_controller.upgrade_all()
            return

        if action == "updates":
            self.catalog.set_filter_mode(FilterMode.UPDATES)
            self.sync_list()
            self.status_bar.set_text(
                f"⬆ {len(self.catalog.filtered_items)} MAJ",
            )
            return

        if action == "games":
            self.catalog.set_filter_mode(FilterMode.GAMES)
            self.sync_list()
            self.status_bar.set_text(
                f"🎮 {len(self.catalog.filtered_items)} jeux",
            )
            return

        if action == "apps":
            self.catalog.set_filter_mode(FilterMode.APPS)
            self.sync_list()
            self.status_bar.set_text(
                f"💻 {len(self.catalog.filtered_items)} apps",
            )

    def _on_search_changed(self):
        self.catalog.set_search(self.search_bar.query)
        self.sync_list()

    def sync_list(self):

        if self.virtual_list:
            self.virtual_list.set_items(self.catalog.filtered_items)

    def reset_view(self):

        self.catalog.reset()
        self._icon_requested.clear()

        if self.virtual_list:
            self.virtual_list.clear_cache()
            self.virtual_list.scroll_to_top()

    def run_on_ui(self, callback):

        if not self._closing:
            self.ui_queue.put(callback)

    def safe_after(self, delay: int, callback):

        if self._closing:
            return None

        after_id = None

        def wrapped():
            if self._closing:
                return
            try:
                callback()
            except Exception as error:
                print("[AFTER ERROR]", error)
            finally:
                if after_id:
                    self.after_ids.discard(after_id)

        try:
            after_id = self.root.after(delay, wrapped)
            self.after_ids.add(after_id)
            return after_id
        except Exception as error:
            print("[SAFE AFTER ERROR]", error)
            return None

    def load_icon_async(self, item: AppItem):

        if item.icon or (self.virtual_list and self.virtual_list.is_scrolling):
            return

        key = item.path or item.name

        if key in self._icon_requested or item._loading_icon:
            return

        item._loading_icon = True
        self._icon_requested.add(key)

        def worker():

            try:
                icon = self.icon_cache.get(key)

                if icon is None:
                    icon = self.icon_manager.get_icon(item)
                    if icon:
                        self.icon_cache[key] = icon

                if icon:

                    def apply():
                        if self._closing:
                            return
                        item.icon = icon
                        if self.virtual_list:
                            self.virtual_list._render_start = -1
                            self.virtual_list.render(force=True)

                    self.run_on_ui(apply)

            finally:
                item._loading_icon = False

        threading.Thread(target=worker, daemon=True).start()

    def uninstall(self, item: AppItem):

        if not messagebox.askyesno("Confirmation", f"Supprimer {item.name} ?"):
            return

        def on_result(ok: bool, msg: str):

            def done():
                self.status_bar.set_text(msg)
                if ok:
                    self.catalog.remove_item(item)
                    self.sync_list()
                    self.sidebar.set_badge(
                        f"⬆ {self.catalog.update_count} MAJ"
                        if self.catalog.update_count
                        else "✓ À jour",
                    )
                    messagebox.showinfo("OK", msg)
                else:
                    messagebox.showerror("Erreur", msg)

            self.run_on_ui(done)

        UninstallAppUseCase.run(item, on_result)

    def _process_ui_queue(self):

        if self._closing:
            return

        try:
            while True:
                try:
                    func = self.ui_queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    func()
                except Exception as error:
                    print("[UI ERROR]", error)
        finally:
            if not self._closing:
                self.safe_after(50, self._process_ui_queue)

    def on_close(self):

        if self._closing:
            return

        self._closing = True

        if self.virtual_list:
            self.virtual_list.destroy()

        try:
            stop_scan()
        except Exception:
            pass

        for after_id in list(self.after_ids):
            try:
                self.root.after_cancel(after_id)
            except Exception:
                pass

        self.after_ids.clear()
        self.icon_cache.clear()

        try:
            if self.root.winfo_exists():
                self.root.quit()
                self.root.destroy()
        except Exception as error:
            print("[CLOSE ERROR]", error)
