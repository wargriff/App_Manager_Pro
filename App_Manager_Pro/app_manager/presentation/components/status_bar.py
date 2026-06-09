"""Barre de statut et progression."""

from __future__ import annotations

import customtkinter as ctk

from app_manager.config.theme import THEME


class StatusBar(ctk.CTkFrame):

    def __init__(self, master):

        super().__init__(master, fg_color="transparent")
        self.pack(fill="x", padx=16, pady=(4, 12))

        self.label = ctk.CTkLabel(
            self,
            text="Prêt",
            font=THEME.font_status,
            text_color=THEME.text_secondary,
        )
        self.label.pack(side="left")

        self.progress = ctk.CTkProgressBar(self, height=4)
        self.progress.pack(fill="x", pady=(6, 0))
        self.progress.pack_forget()

    def set_text(self, text: str):
        self.label.configure(text=text)

    def show_progress(self):
        self.progress.pack(fill="x", pady=(6, 0))
        self.progress.start()

    def hide_progress(self):
        try:
            self.progress.stop()
            self.progress.pack_forget()
        except Exception:
            pass
