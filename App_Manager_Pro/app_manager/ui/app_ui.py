# app_ui.py — interface principale

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from app_manager.models.app_item import AppItem
from app_manager.services.icon_manager import IconManager
from app_manager.services.scanner import stop_scan
from app_manager.services.uninstaller import Uninstaller
from app_manager.services.winget import WingetManager
from app_manager.ui.row_factory import RowFactory
from app_manager.ui.scan_manager import ScanManager
from app_manager.ui.update_manager import UpdateManager
from app_manager.ui.virtual_list import VirtualList


class AppUI:

    def __init__(self, root: ctk.CTk):

        self.root = root
        self.search_var: tk.StringVar | None = None
        self.search = None
        self.virtual_list: VirtualList | None = None
        self.status = None
        self.progress = None
        self.update_badge = None

        self.queue: queue.Queue[AppItem] = queue.Queue()
        self.ui_queue: queue.Queue = queue.Queue()

        self.all_data: list[AppItem] = []
        self.filtered_data: list[AppItem] = []
        self.seen: set[tuple[str, str]] = set()
        self._winget_by_id: dict[str, AppItem] = {}
        self._winget_by_name: dict[str, AppItem] = {}

        self.icon_manager = IconManager()
        self.icon_cache: dict[str, Any] = {}
        self.after_ids: set[str] = set()
        self._icon_requested: set[str] = set()

        self.is_scanning = False
        self._closing = False
        self._scan_done = 0
        self._checking_updates = False
        self._filter_mode = "all"

        self.row_factory = RowFactory(self)
        self.scan_manager = ScanManager(self)
        self.update_manager = UpdateManager(self)

        self.build_ui()

        self.safe_after(50, self.scan_manager.process_queue)
        self.safe_after(50, self.process_ui_queue)
        self.safe_after(200, self.scan_manager.start_scan)

    # =====================================================
    # THREAD-SAFE UI
    # =====================================================

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

    def safe_widget_call(self, func):

        if not self._closing:
            try:
                func()
            except Exception as error:
                print("[UI ERROR]", error)

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        sidebar = ctk.CTkFrame(
            self.root, width=230, fg_color="#0d0d0d", corner_radius=0,
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar, text="APP MANAGER",
            font=("Segoe UI", 22, "bold"), text_color="#00ff88",
        ).pack(pady=(18, 8))

        ctk.CTkLabel(
            sidebar, text="Pro",
            font=("Segoe UI", 11), text_color="#666666",
        ).pack(pady=(0, 12))

        buttons = [
            ("💻 Programmes", "apps"),
            ("🎮 Jeux", "games"),
            ("⬆ Mises à jour", "updates"),
            ("🔄 Scanner", "scan"),
            ("⬆ Tout mettre à jour", "upgrade_all"),
            ("⛔ Stop", "stop"),
        ]

        for text, action in buttons:
            ctk.CTkButton(
                sidebar, text=text, height=38, anchor="w",
                font=("Segoe UI", 13),
                fg_color="transparent", hover_color="#1a1a1a",
                command=lambda a=action: self.handle_action(a),
            ).pack(fill="x", padx=10, pady=3)

        self.update_badge = ctk.CTkLabel(
            sidebar, text="",
            font=("Segoe UI", 11), text_color="#ffaa00",
        )
        self.update_badge.pack(pady=(8, 16))

        main = ctk.CTkFrame(self.root, fg_color="#121212", corner_radius=0)
        main.pack(side="right", fill="both", expand=True)

        top = ctk.CTkFrame(main, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 8))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_list)

        self.search = ctk.CTkEntry(
            top,
            textvariable=self.search_var,
            placeholder_text="🔍 Rechercher une application...",
            height=40,
            font=("Segoe UI", 13),
        )
        self.search.pack(fill="x")

        list_frame = ctk.CTkFrame(main, fg_color="#121212")
        list_frame.pack(fill="both", expand=True, padx=16, pady=4)

        self.virtual_list = VirtualList(
            list_frame,
            self.row_factory.build_row,
        )

        bottom = ctk.CTkFrame(main, fg_color="transparent")
        bottom.pack(fill="x", padx=16, pady=(4, 12))

        self.status = ctk.CTkLabel(
            bottom, text="Prêt",
            font=("Segoe UI", 12), text_color="#aaaaaa",
        )
        self.status.pack(side="left")

        self.progress = ctk.CTkProgressBar(bottom, height=4)
        self.progress.pack(fill="x", pady=(6, 0))
        self.progress.pack_forget()

    def sync_list(self):

        if self.virtual_list:
            self.virtual_list.set_items(self.filtered_data)

    def update_badge(self):

        count = sum(1 for i in self.all_data if i.update_available)

        if count:
            self.update_badge.configure(
                text=f"⬆ {count} mise(s) à jour",
            )
        else:
            self.update_badge.configure(text="✓ À jour")

    # =====================================================
    # ICONS
    # =====================================================

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

                    def apply_icon():
                        if self._closing:
                            return
                        item.icon = icon
                        if self.virtual_list:
                            self.virtual_list._render_start = -1
                            self.virtual_list.render(force=True)

                    self.run_on_ui(apply_icon)

            finally:
                item._loading_icon = False

        threading.Thread(target=worker, daemon=True).start()

    def add_item(
        self,
        name,
        path,
        source,
        size=0,
        winget_id: str = "",
    ):

        self.queue.put(
            AppItem(
                name=name,
                path=path,
                source=source,
                size=str(size),
                winget_id=winget_id,
                category=AppItem.detect_category(name, path),
            )
        )

    def apply_filter(self):

        query = (
            self.search_var.get().lower().strip()
            if self.search_var else ""
        )

        base = self.all_data

        if self._filter_mode == "games":
            base = [i for i in base if i.category == "game"]
        elif self._filter_mode == "apps":
            base = [i for i in base if i.category == "app"]
        elif self._filter_mode == "updates":
            base = [i for i in base if i.update_available]

        if query:
            self.filtered_data = [
                i for i in base
                if query in i.name.lower()
                or (i.path and query in i.path.lower())
            ]
        else:
            self.filtered_data = base.copy()

        self.sync_list()

    def filter_list(self, *_):
        self.apply_filter()

    def handle_action(self, action):

        if action == "scan":
            self.scan_manager.start_scan()
            return

        if action == "stop":
            self.scan_manager.stop_scan()
            return

        if action == "upgrade_all":
            self.update_manager.upgrade_all()
            return

        if action == "updates":
            self._filter_mode = "updates"
            self.apply_filter()
            self.status.configure(
                text=f"⬆ {len(self.filtered_data)} mise(s) à jour",
            )
            return

        if action == "games":
            self._filter_mode = "games"
            self.apply_filter()
            self.status.configure(
                text=f"🎮 {len(self.filtered_data)} jeux",
            )
            return

        if action == "apps":
            self._filter_mode = "apps"
            self.apply_filter()
            self.status.configure(
                text=f"💻 {len(self.filtered_data)} applications",
            )

    def uninstall(self, item: AppItem):

        if not messagebox.askyesno(
            "Confirmation",
            f"Supprimer {item.name} ?",
        ):
            return

        threading.Thread(
            target=self._uninstall_worker,
            args=(item,),
            daemon=True,
        ).start()

    def _uninstall_worker(self, item: AppItem):

        try:
            if item.source == "winget" and item.winget_id:
                ok, msg = WingetManager().uninstall(item.winget_id)
                success = ok
            elif item.source == "winget" and not item.path:
                ok, msg = WingetManager().uninstall(item.name)
                success = ok
            else:
                success, msg = Uninstaller.uninstall(item.name, item.path)

        except Exception as error:
            success = False
            msg = str(error)

        def done():
            self.status.configure(text=msg)
            if success:
                key = AppItem.item_key(item)
                self.all_data = [
                    i for i in self.all_data if AppItem.item_key(i) != key
                ]
                self.seen.discard(key)
                self.apply_filter()
                self.update_badge()
                messagebox.showinfo("OK", msg)
            else:
                messagebox.showerror("Erreur", msg)

        self.run_on_ui(done)

    def reset_data(self):

        self.seen.clear()
        self.all_data.clear()
        self.filtered_data.clear()
        self._winget_by_id.clear()
        self._winget_by_name.clear()
        self._icon_requested.clear()
        self._filter_mode = "all"
        self.queue = queue.Queue()

        if self.virtual_list:
            self.virtual_list.clear_cache()
            self.virtual_list.scroll_to_top()

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

    def process_ui_queue(self):

        if self._closing:
            return

        try:
            while True:
                try:
                    func = self.ui_queue.get_nowait()
                except queue.Empty:
                    break
                self.safe_widget_call(func)
        except Exception as error:
            print("[UI QUEUE ERROR]", error)
        finally:
            if not self._closing:
                self.safe_after(50, self.process_ui_queue)
