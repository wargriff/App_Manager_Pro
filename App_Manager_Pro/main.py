import traceback
from tkinter import messagebox

import customtkinter as ctk

from ui import AppUI

APP_NAME = "🔥 App Manager Pro"
WINDOW_SIZE = (1400, 850)


class Application:

    def __init__(self):

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.root = ctk.CTk()

        self._closing = False

        self.setup_window()

        self.app_ui = AppUI(self.root)

        self.bind_shortcuts()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close,
        )

    # =====================================================
    # WINDOW
    # =====================================================

    def setup_window(self):

        self.root.title(APP_NAME)

        self.root.minsize(900, 600)

        self.center_window(*WINDOW_SIZE)

        self.root.report_callback_exception = (
            self.global_exception_handler
        )

    def center_window(
        self,
        width,
        height,
    ):

        self.root.update_idletasks()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    # =====================================================
    # SHORTCUTS
    # =====================================================

    def bind_shortcuts(self):

        self.root.bind(
            "<Escape>",
            lambda e: self.on_close(),
        )

        self.root.bind(
            "<Control-r>",
            lambda e: self.app_ui.start_scan(),
        )

    # =====================================================
    # ERRORS
    # =====================================================

    def global_exception_handler(
        self,
        exc_type,
        exc_value,
        exc_traceback,
    ):

        error = "".join(
            traceback.format_exception(
                exc_type,
                exc_value,
                exc_traceback,
            )
        )

        print(error)

        messagebox.showerror(
            "Erreur",
            str(exc_value),
        )

    # =====================================================
    # CLOSE
    # =====================================================

    def on_close(self):

        if self._closing:
            return

        self._closing = True

        try:
            # noinspection PyUnresolvedReferences
            stop_scan()

        except Exception:
            pass

        # noinspection PyUnresolvedReferences
        for after_id in list(self.after_ids):

            try:
                # noinspection PyUnresolvedReferences
                self.safe_after_cancel(after_id)

            except Exception:
                pass

        # noinspection PyUnresolvedReferences
        self.after_ids.clear()

        # noinspection PyUnresolvedReferences
        self.icon_cache.clear()

        try:

            if self.root.winfo_exists():
                self.root.destroy()

        except Exception as error:

            print("[CLOSE ERROR]", error)

    # =====================================================
    # RUN
    # =====================================================

    def run(self):

        self.root.mainloop()


if __name__ == "__main__":

    app = Application()

    app.run()