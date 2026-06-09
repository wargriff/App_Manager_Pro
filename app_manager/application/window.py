"""Fenêtre principale de l'application."""

from __future__ import annotations

import logging
import traceback
from tkinter import messagebox

import customtkinter as ctk

from app_manager.config.settings import (
    APP_NAME,
    MIN_WINDOW_SIZE,
    SHORTCUT_QUIT,
    SHORTCUT_RESCAN,
    WINDOW_SIZE,
)
from app_manager.presentation.main_window import MainWindow

logger = logging.getLogger("app_manager.app")


class ApplicationWindow:

    def __init__(self):

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.root = ctk.CTk()
        self._closing = False

        self._setup_window()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.main_window = MainWindow(self.root)
        self._bind_shortcuts()

    def _setup_window(self):

        self.root.title(APP_NAME)
        self.root.minsize(*MIN_WINDOW_SIZE)
        self._center_window(*WINDOW_SIZE)
        self.root.report_callback_exception = self._on_exception

    def _center_window(self, width: int, height: int):

        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _bind_shortcuts(self):

        self.root.bind(SHORTCUT_QUIT, lambda e: self.on_close())
        self.root.bind(
            SHORTCUT_RESCAN,
            lambda e: self.main_window.scan_controller.start_scan(),
        )

    def _on_exception(self, exc_type, exc_value, exc_traceback):

        error = "".join(
            traceback.format_exception(
                exc_type,
                exc_value,
                exc_traceback,
            )
        )
        logger.error("UI exception:\n%s", error)
        messagebox.showerror("Erreur", str(exc_value))

    def on_close(self):

        if self._closing:
            return

        self._closing = True
        logger.info("Fermeture de l'application")

        if hasattr(self, "main_window"):
            self.main_window.on_close()
        elif self.root.winfo_exists():
            self.root.quit()
            self.root.destroy()

    def run(self):
        logger.info("Démarrage de %s", APP_NAME)
        self.root.mainloop()
