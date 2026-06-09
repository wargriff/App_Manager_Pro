# file: Xmacro_main.py

import signal
import sys
import traceback

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from engine_win32 import MacroManager
from ui import UI


# =========================
# CRASH HANDLER
# =========================
def handle_exception(exc_type, exc_value, exc_tb):
    print("[FATAL ERROR]")
    traceback.print_exception(exc_type, exc_value, exc_tb)


sys.excepthook = handle_exception


# =========================
# ENGINE PROXY (CRITICAL FIX)
# =========================
# file: Xmacro_main.py (ONLY EngineProxy updated)

class EngineProxy:
    def __init__(self, manager: MacroManager):
        self.manager = manager

        self.buttons = {
            **manager.mouse.buttons,
            **manager.keyboard.buttons,
        }

    @property
    def enabled(self):
        return self.manager.mouse.enabled

    @property
    def running(self):
        return self.manager.mouse.running and self.manager.keyboard.running

    @running.setter
    def running(self, state: bool):
        self.manager.mouse.running = state
        self.manager.keyboard.running = state

    def toggle(self):
        self.manager.toggle_all()

    def stop(self):
        self.manager.stop()

    # =========================
    # FIX: GAME SAFE SUPPORT
    # =========================
    def set_game_safe(self, state: bool):
        # apply if available
        for eng in (self.manager.mouse, self.manager.keyboard):
            if hasattr(eng, "game_safe"):
                eng.game_safe = state

    # =========================
    # DISPATCH
    # =========================
    def _get_engine(self, key):
        if key in self.manager.mouse.buttons:
            return self.manager.mouse
        return self.manager.keyboard

    def set_cps(self, key, value):
        self._get_engine(key).set_cps(key, value)

    def set_delay(self, key, value):
        self._get_engine(key).set_delay(key, value)

    def get_cps(self, key):
        return self._get_engine(key).get_cps(key)

    def get_real_cps(self, key):
        return self._get_engine(key).get_real_cps(key)

    def set_active(self, key, state: bool):
        engine = self._get_engine(key)
        if key in engine.buttons:
            engine.buttons[key].active = state
# =========================
# SAFE STOP
# =========================
def safe_stop(engine):
    if not engine:
        return

    try:
        engine.stop()
    except Exception:
        pass


# =========================
# MAIN
# =========================
def main():
    print("[XMACRO] Booting...")

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)

    # allow CTRL+C
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    manager = None
    proxy = None
    exit_code = 0

    try:
        # =========================
        # ENGINE
        # =========================
        manager = MacroManager()
        proxy = EngineProxy(manager)

        # =========================
        # UI
        # =========================
        ui = UI(proxy, "assets/mouse.png")
        ui.show()

        # =========================
        # SHUTDOWN
        # =========================
        def shutdown():
            print("[XMACRO] Shutting down...")
            safe_stop(proxy)

        app.aboutToQuit.connect(shutdown)

        # =========================
        # RUN
        # =========================
        exit_code = app.exec()

    except Exception:
        traceback.print_exc()
        exit_code = 1

    finally:
        safe_stop(proxy)
        print("[XMACRO] Exit complete")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
