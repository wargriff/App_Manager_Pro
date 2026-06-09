"""Barre de recherche."""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from app_manager.config.theme import THEME


class SearchBar(ctk.CTkFrame):

    def __init__(self, master, on_change):

        super().__init__(master, fg_color="transparent")
        self.pack(fill="x", padx=16, pady=(16, 8))

        self.var = tk.StringVar()
        self.var.trace_add("write", lambda *_: on_change())

        self.entry = ctk.CTkEntry(
            self,
            textvariable=self.var,
            placeholder_text="🔍 Rechercher une application...",
            height=40,
            font=THEME.font_body,
        )
        self.entry.pack(fill="x")

    @property
    def query(self) -> str:
        return self.var.get()
