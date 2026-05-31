"""Construction des lignes de la liste d'applications."""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Callable

import customtkinter as ctk

from app_manager.models.app_item import AppItem
from app_manager.services.utils import Utils

if TYPE_CHECKING:
    from app_manager.ui.app_ui import AppUI


class RowFactory:

    def __init__(self, ui: "AppUI"):
        self.ui = ui

    def build_row(self, frame: tk.Frame) -> dict:

        icon = tk.Label(
            frame,
            text="📦",
            bg="#1e1e1e",
            fg="#cccccc",
            font=("Segoe UI", 16),
        )
        icon.pack(side="left", padx=(10, 6), pady=6)

        text_frame = tk.Frame(frame, bg="#1e1e1e")
        text_frame.pack(side="left", fill="both", expand=True, pady=6)

        name = tk.Label(
            text_frame,
            text="",
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        name.pack(anchor="w", fill="x")

        info = tk.Label(
            text_frame,
            text="",
            bg="#1e1e1e",
            fg="#888888",
            font=("Segoe UI", 10),
            anchor="w",
        )
        info.pack(anchor="w", fill="x")

        actions = tk.Frame(frame, bg="#1e1e1e")
        actions.pack(side="right", padx=8, pady=6)

        update_btn = ctk.CTkButton(
            actions, text="⬆", width=30, height=28,
            font=("Segoe UI", 14),
            fg_color="#1a4a7a", hover_color="#2563a8",
        )
        update_btn.pack(side="left", padx=2)

        play_btn = ctk.CTkButton(
            actions, text="▶", width=30, height=28,
            fg_color="#0d5c0d", hover_color="#148214",
        )
        play_btn.pack(side="left", padx=2)

        open_btn = ctk.CTkButton(
            actions, text="📂", width=30, height=28,
            fg_color="#2a2a2a", hover_color="#3a3a3a",
        )
        open_btn.pack(side="left", padx=2)

        delete_btn = ctk.CTkButton(
            actions, text="🗑", width=30, height=28,
            fg_color="#7a0c0c", hover_color="#9a1010",
        )
        delete_btn.pack(side="left", padx=2)

        row = {
            "icon": icon,
            "name": name,
            "info": info,
            "update": update_btn,
            "play": play_btn,
            "open": open_btn,
            "delete": delete_btn,
        }
        row["bind"] = self._make_binder(row)
        return row

    def _make_binder(self, row: dict) -> Callable[[AppItem, bool], None]:

        def bind_item(item: AppItem, is_scrolling: bool):

            row["name"].configure(text=item.name[:80])

            if item.update_available and item.latest_version:
                row["info"].configure(
                    text=f"{item.source} • v{item.size} → v{item.latest_version}",
                )
            else:
                row["info"].configure(text=f"{item.source} • {item.size}")

            path = item.path or ""
            vlist = self.ui.virtual_list
            exists = vlist.path_exists(path) if vlist else False
            can_launch = exists and path.lower().endswith(".exe")

            row["play"].configure(
                state="normal" if can_launch else "disabled",
                command=lambda p=path: Utils.run_app(p),
            )
            row["open"].configure(
                state="normal" if exists else "disabled",
                command=lambda p=path: Utils.open_folder(p),
            )

            can_update = bool(item.winget_id and item.update_available)
            row["update"].configure(
                state="normal" if can_update else "disabled",
                command=lambda i=item: self.ui.update_manager.upgrade_item(i),
            )
            row["delete"].configure(
                command=lambda i=item: self.ui.uninstall(i),
            )

            if item.icon:
                row["icon"].configure(image=item.icon, text="")
                row["icon"].image = item.icon
            else:
                row["icon"].configure(
                    image="",
                    text="🎮" if item.category == "game" else "📦",
                )
                if not is_scrolling:
                    self.ui.load_icon_async(item)

        return bind_item
