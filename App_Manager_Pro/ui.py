# ui.py

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox
from typing import Optional, Any

import customtkinter as ctk

from icon_manager import IconManager
from scanner import scan_all, stop_scan
from uninstaller import Uninstaller
from utils import Utils
from winget_manager import WingetManager

VISIBLE_ITEM_COUNT = 28
BUFFER_ITEMS = 12
ITEM_HEIGHT = 74

QUEUE_BATCH_SIZE = 250
REFRESH_INTERVAL = 16


@dataclass(slots=True)
class AppItem:
    name: str
    path: Optional[str]
    source: str
    size: str
    category: str = "app"
    icon: Optional[Any] = None
    _loading_icon: bool = False


class AppUI:

    def __init__(self, root: ctk.CTk):

        self.search_var = None
        self.search = None
        self.canvas = None
        self.scrollbar = None
        self.list_container = None
        self.canvas_window = None
        self.status = None
        self.progress = None
        self.root = root

        self.root.title("App Manager Pro")
        self.root.geometry("1400x850")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.queue: queue.Queue[AppItem] = queue.Queue()
        self.ui_queue: queue.Queue = queue.Queue()

        self.all_data: list[AppItem] = []
        self.filtered_data: list[AppItem] = []

        self.seen: set[tuple[str, str]] = set()

        self.item_widgets: list[dict] = []

        self.icon_manager = IconManager()
        self.icon_cache: dict[str, Any] = {}

        self.after_ids: set[str] = set()

        self.is_scanning = False
        self._closing = False
        self._scan_done = 0
        self._refresh_scheduled = False

        self.build_ui()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close,
        )

        self.safe_after(
            50,
            self.process_queue,
        )

        self.safe_after(
            50,
            self.process_ui_queue,
        )

        self.start_scan()

    # =====================================================
    # SAFE TK
    # =====================================================

    def safe_after(
        self,
        delay: int,
        callback,
    ):

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

            after_id = self.root.after(
                delay,
                wrapped,
            )

            self.after_ids.add(after_id)

            return after_id

        except Exception as error:

            print("[SAFE AFTER ERROR]", error)

            return None

    def safe_widget_call(self, func):

        if self._closing:
            return

        try:
            func()

        except Exception as error:
            print("[UI ERROR]", error)

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        sidebar = ctk.CTkFrame(
            self.root,
            width=220,
            fg_color="#101010",
        )

        sidebar.pack(
            side="left",
            fill="y",
        )

        ctk.CTkLabel(
            sidebar,
            text="APP MANAGER",
            font=("Segoe UI", 24, "bold"),
            text_color="#00ff88",
        ).pack(
            pady=20,
        )

        buttons = [
            ("💻 Programmes", "apps"),
            ("🎮 Jeux", "games"),
            ("🔄 Scanner", "scan"),
            ("⛔ Stop", "stop"),
        ]

        for text, action in buttons:

            ctk.CTkButton(
                sidebar,
                text=text,
                height=42,
                anchor="w",
                fg_color="transparent",
                hover_color="#1f1f1f",
                command=lambda a=action: self.handle_action(a),
            ).pack(
                fill="x",
                padx=12,
                pady=4,
            )

        main = ctk.CTkFrame(
            self.root,
            fg_color="#121212",
        )

        main.pack(
            side="right",
            fill="both",
            expand=True,
        )

        self.search_var = tk.StringVar()

        self.search_var.trace_add(
            "write",
            self.filter_list,
        )

        self.search = ctk.CTkEntry(
            main,
            textvariable=self.search_var,
            placeholder_text="Rechercher...",
            height=42,
        )

        self.search.pack(
            fill="x",
            padx=20,
            pady=20,
        )

        content = ctk.CTkFrame(
            main,
            fg_color="transparent",
        )

        content.pack(
            fill="both",
            expand=True,
        )

        self.canvas = tk.Canvas(
            content,
            bg="#121212",
            highlightthickness=0,
        )

        self.scrollbar = ctk.CTkScrollbar(
            content,
            command=self.canvas.yview,
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set,
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.scrollbar.pack(
            side="right",
            fill="y",
        )

        self.list_container = tk.Frame(
            self.canvas,
            bg="#121212",
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.list_container,
            anchor="nw",
        )

        self.canvas.bind(
            "<Configure>",
            self.on_canvas_resize,
        )

        self.canvas.bind_all(
            "<MouseWheel>",
            self.on_mousewheel,
        )

        self.status = ctk.CTkLabel(
            main,
            text="Prêt",
        )

        self.status.pack(
            pady=5,
        )

        self.progress = ctk.CTkProgressBar(
            main,
            height=6,
        )

        self.progress.pack(
            fill="x",
            padx=20,
            pady=(0, 10),
        )

        self.progress.pack_forget()

        self.create_widget_pool()

    # =====================================================
    # WIDGET POOL
    # =====================================================

    def create_widget_pool(self):

        total = VISIBLE_ITEM_COUNT + BUFFER_ITEMS

        for _ in range(total):

            widget = self.create_item_widget()

            self.item_widgets.append(widget)

    def create_item_widget(self):

        frame = ctk.CTkFrame(
            self.list_container,
            width=1100,
            height=64,
            fg_color="#222222",
            corner_radius=12,
        )

        frame.place(x=0, y=0)

        frame.pack_propagate(False)

        icon = tk.Label(
            frame,
            text="📦",
            bg="#222222",
            fg="white",
        )

        icon.pack(
            side="left",
            padx=12,
        )

        text_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent",
        )

        text_frame.pack(
            side="left",
            fill="both",
            expand=True,
        )

        name = ctk.CTkLabel(
            text_frame,
            text="",
            anchor="w",
            font=("Segoe UI", 14, "bold"),
        )

        name.pack(anchor="w")

        info = ctk.CTkLabel(
            text_frame,
            text="",
            anchor="w",
            text_color="#999999",
        )

        info.pack(anchor="w")

        actions = ctk.CTkFrame(
            frame,
            fg_color="transparent",
        )

        actions.pack(
            side="right",
            padx=10,
        )

        play_btn = ctk.CTkButton(
            actions,
            text="▶",
            width=32,
            height=32,
            fg_color="#0d5c0d",
        )

        play_btn.pack(
            side="left",
            padx=2,
        )

        open_btn = ctk.CTkButton(
            actions,
            text="📂",
            width=32,
            height=32,
        )

        open_btn.pack(
            side="left",
            padx=2,
        )

        delete_btn = ctk.CTkButton(
            actions,
            text="🗑",
            width=32,
            height=32,
            fg_color="#7a0c0c",
        )

        delete_btn.pack(
            side="left",
            padx=2,
        )

        return {
            "frame": frame,
            "icon": icon,
            "name": name,
            "info": info,
            "play": play_btn,
            "open": open_btn,
            "delete": delete_btn,
        }

    # =====================================================
    # FAST REFRESH
    # =====================================================

    def schedule_refresh(self):

        if self._refresh_scheduled:
            return

        self._refresh_scheduled = True

        def run():

            self._refresh_scheduled = False

            if not self._closing:
                self.refresh_visible_items()

        self.safe_after(
            REFRESH_INTERVAL,
            run,
        )

    def refresh_visible_items(self):

        if self._closing:
            return

        width = max(
            self.canvas.winfo_width(),
            300,
        )

        scroll_y = self.canvas.canvasy(0)

        start = max(
            0,
            int(scroll_y // ITEM_HEIGHT),
        )

        visible = self.filtered_data[
            start:start + len(self.item_widgets)
        ]

        for index, widget in enumerate(self.item_widgets):

            if index >= len(visible):

                widget["frame"].place_forget()

                continue

            item = visible[index]

            y = (start + index) * ITEM_HEIGHT

            widget["frame"].place(
                x=10,
                y=y,
                width=width - 30,
                height=64,
            )

            widget["name"].configure(
                text=item.name,
            )

            widget["info"].configure(
                text=f"{item.source} • {item.size}",
            )

            if item.icon:

                widget["icon"].configure(
                    image=item.icon,
                    text="",
                )

                widget["icon"].image = item.icon

            else:

                widget["icon"].configure(
                    image="",
                    text="🎮" if item.category == "game" else "📦",
                )

                self.load_icon_async(item)

            path = item.path or ""

            exists = (
                path
                and os.path.exists(path)
            )

            can_launch = (
                exists
                and path.lower().endswith(".exe")
            )

            widget["play"].configure(
                state="normal" if can_launch else "disabled",
                command=lambda p=path: Utils.run_app(p),
            )

            widget["open"].configure(
                state="normal" if exists else "disabled",
                command=lambda p=path: Utils.open_folder(p),
            )

            widget["delete"].configure(
                command=lambda i=item: self.uninstall(i),
            )

        total_height = max(
            len(self.filtered_data) * ITEM_HEIGHT,
            1,
        )

        self.canvas.configure(
            scrollregion=(
                0,
                0,
                width,
                total_height,
            ),
        )

        self.list_container.configure(
            width=width,
            height=total_height,
        )

    # =====================================================
    # EVENTS
    # =====================================================

    def on_canvas_resize(self, event):

        self.canvas.itemconfigure(
            self.canvas_window,
            width=event.width,
        )

        self.schedule_refresh()

    def on_mousewheel(self, event):

        self.canvas.yview_scroll(
            int(-event.delta / 120),
            "units",
        )

        self.schedule_refresh()

    # =====================================================
    # ICONS
    # =====================================================

    def load_icon_async(self, item):

        if item.icon:
            return

        if item._loading_icon:
            return

        item._loading_icon = True

        def worker():

            try:

                key = item.path or item.name

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

                        self.schedule_refresh()

                    self.safe_after(
                        0,
                        apply_icon,
                    )

            finally:

                item._loading_icon = False

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    # =====================================================
    # SCAN
    # =====================================================

    def start_scan(self):

        if self.is_scanning:
            return

        self.stop_scan()
        self.reset()

        self.is_scanning = True
        self._scan_done = 0

        self.progress.pack(
            fill="x",
            padx=20,
            pady=(0, 10),
        )

        self.progress.start()

        threading.Thread(
            target=self.winget_scan,
            daemon=True,
        ).start()

        threading.Thread(
            target=self.filesystem_scan,
            daemon=True,
        ).start()

    def winget_scan(self):

        try:

            manager = WingetManager()

            for app in manager.get_apps():

                if not self.is_scanning:
                    return

                self.add_item(
                    app.name,
                    None,
                    "winget",
                    app.version,
                )

        finally:

            self.safe_after(
                0,
                self.check_scan_complete,
            )

    def filesystem_scan(self):

        def callback(program):

            if not self.is_scanning:
                return

            self.add_item(
                name=program.name,
                path=program.path,
                source=program.source,
                size=program.size,
            )

        try:

            scan_all(callback)

        finally:

            self.safe_after(
                0,
                self.check_scan_complete,
            )

    # =====================================================
    # DATA
    # =====================================================

    def add_item(
        self,
        name,
        path,
        source,
        size=0,
    ):

        self.queue.put(
            AppItem(
                name=name,
                path=path,
                source=source,
                size=str(size),
                category=self.detect_category(
                    name,
                    path,
                ),
            )
        )

    def process_queue(self):

        if self._closing:
            return

        processed = 0

        while processed < QUEUE_BATCH_SIZE:

            try:
                item = self.queue.get_nowait()

            except queue.Empty:
                break

            key = (
                item.name.lower(),
                (item.path or "").lower(),
            )

            if key in self.seen:
                continue

            self.seen.add(key)

            self.all_data.append(item)

            processed += 1

        if processed:

            self.filtered_data = self.all_data.copy()

            self.status.configure(
                text=f"{len(self.all_data)} apps",
            )

            self.schedule_refresh()

        self.safe_after(
            50,
            self.process_queue,
        )

    # =====================================================
    # FILTER
    # =====================================================

    def filter_list(self, *_):

        query = self.search_var.get().lower().strip()

        if not query:

            self.filtered_data = self.all_data.copy()

        else:

            self.filtered_data = [
                item
                for item in self.all_data
                if (
                    query in item.name.lower()
                    or (
                        item.path
                        and query in item.path.lower()
                    )
                )
            ]

        self.schedule_refresh()

    # =====================================================
    # ACTIONS
    # =====================================================

    def handle_action(self, action):

        if action == "scan":
            self.start_scan()
            return

        if action == "stop":
            self.stop_scan()
            return

        if action == "games":

            self.filtered_data = [
                item
                for item in self.all_data
                if item.category == "game"
            ]

            self.status.configure(
                text=f"🎮 {len(self.filtered_data)} jeux",
            )

            self.schedule_refresh()

            return

        if action == "apps":

            self.filtered_data = [
                item
                for item in self.all_data
                if item.category == "app"
            ]

            self.status.configure(
                text=f"💻 {len(self.filtered_data)} applications",
            )

            self.schedule_refresh()

    # =====================================================
    # SCAN COMPLETE
    # =====================================================

    def check_scan_complete(self):

        self._scan_done += 1

        if self._scan_done < 2:
            return

        self.ui_queue.put(
            self.finish_scan,
        )

    def finish_scan(self):

        if self._closing:
            return

        self.is_scanning = False

        try:
            self.progress.stop()
            self.progress.pack_forget()

        except Exception:
            pass

        self.status.configure(
            text=f"✅ {len(self.all_data)} apps",
        )

        self.refresh_visible_items()

    def stop_scan(self):

        self.is_scanning = False

        try:
            stop_scan()
        except Exception:
            pass

        try:
            self.progress.stop()
            self.progress.pack_forget()
        except Exception:
            pass

        self.status.configure(
            text="⛔ Scan stoppé",
        )

    # =====================================================
    # UI QUEUE
    # =====================================================

    def process_ui_queue(self):

        if self._closing:
            return

        while True:

            try:
                func = self.ui_queue.get_nowait()

            except queue.Empty:
                break

            self.safe_widget_call(func)

        self.safe_after(
            50,
            self.process_ui_queue,
        )

    # =====================================================
    # UNINSTALL
    # =====================================================

    def uninstall(self, item):

        if not messagebox.askyesno(
            "Confirmation",
            f"Supprimer {item.name} ?",
        ):
            return

        threading.Thread(
            target=self.uninstall_worker,
            args=(item,),
            daemon=True,
        ).start()

    def uninstall_worker(self, item):

        try:

            if (
                item.source == "winget"
                and not item.path
            ):

                WingetManager().uninstall(
                    item.name,
                )

                success = True
                msg = f"✅ {item.name}"

            else:

                success, msg = Uninstaller.uninstall(
                    item.name,
                    item.path,
                )

        except Exception as error:

            success = False
            msg = str(error)

        def done():

            if self._closing:
                return

            self.status.configure(
                text=msg,
            )

            if success:

                messagebox.showinfo(
                    "OK",
                    msg,
                )

            else:

                messagebox.showerror(
                    "Erreur",
                    msg,
                )

        self.safe_after(
            0,
            done,
        )

    # =====================================================
    # HELPERS
    # =====================================================

    @staticmethod
    def detect_category(name, path):

        text = f"{name} {path or ''}".lower()

        keywords = {
            "steam",
            "steamapps",
            "epic",
            "riot",
            "valorant",
            "league of legends",
            "ubisoft",
            "uplay",
            "battle.net",
            "blizzard",
            "game",
        }

        if any(k in text for k in keywords):
            return "game"

        return "app"

    def reset(self):

        self.seen.clear()

        self.all_data.clear()

        self.filtered_data.clear()

        self.queue = queue.Queue()

        self.canvas.yview_moveto(0)

        self.schedule_refresh()

    # =====================================================
    # CLOSE
    # =====================================================

    def on_close(self):

        if self._closing:
            return

        self._closing = True

        try:
            self.canvas.unbind_all("<MouseWheel>")
        except Exception:
            pass

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
                self.root.destroy()

        except Exception as error:

            print("[CLOSE ERROR]", error)