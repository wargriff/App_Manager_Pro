"""Barre latérale de navigation."""

from __future__ import annotations

import customtkinter as ctk

from app_manager.config.theme import THEME


class Sidebar(ctk.CTkFrame):

    ACTIONS = [
        ("💻 Programmes", "apps"),
        ("🎮 Jeux", "games"),
        ("⬆ Mises à jour", "updates"),
        ("🔄 Scanner", "scan"),
        ("⬆ Tout mettre à jour", "upgrade_all"),
        ("⛔ Stop", "stop"),
    ]

    def __init__(self, master, on_action):

        super().__init__(
            master,
            width=230,
            fg_color=THEME.bg_dark,
            corner_radius=0,
        )
        self.pack(side="left", fill="y")
        self.pack_propagate(False)

        ctk.CTkLabel(
            self,
            text="APP MANAGER",
            font=THEME.font_title,
            text_color=THEME.accent,
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            self,
            text="Pro Edition",
            font=THEME.font_subtitle,
            text_color=THEME.accent_muted,
        ).pack(pady=(0, 12))

        for label, action in self.ACTIONS:
            ctk.CTkButton(
                self,
                text=label,
                height=38,
                anchor="w",
                font=THEME.font_body,
                fg_color="transparent",
                hover_color="#1a1a1a",
                command=lambda a=action: on_action(a),
            ).pack(fill="x", padx=10, pady=3)

        self.badge = ctk.CTkLabel(
            self,
            text="",
            font=THEME.font_subtitle,
            text_color=THEME.warning,
        )
        self.badge.pack(pady=(8, 16))

    def set_badge(self, text: str):
        self.badge.configure(text=text)
