# file: engine.py

import collections
import ctypes
import threading
import time
from dataclasses import dataclass, field
from typing import Dict

user32 = ctypes.windll.user32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02
VK_XBUTTON1 = 0x05
VK_XBUTTON2 = 0x06

KEYEVENTF_KEYUP = 0x0002
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

ULONG_PTR = ctypes.c_ulonglong


# =========================
# LOW LEVEL
# =========================
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ULONG_PTR)]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_ulong), ("u", INPUT_UNION)]


def send_mouse(flag):
    inp = INPUT(type=INPUT_MOUSE)
    inp.mi = MOUSEINPUT(0, 0, 0, flag, 0, ULONG_PTR(0))
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def send_key(vk, down=True):
    inp = INPUT(type=INPUT_KEYBOARD)
    inp.ki = KEYBDINPUT(vk, 0, 0 if down else KEYEVENTF_KEYUP, 0, ULONG_PTR(0))
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


# =========================
# DATA
# =========================
@dataclass
class Btn:
    cps: int = 10
    delay: float = 0.01
    active: bool = False


@dataclass
class Stats:
    timestamps: collections.deque = field(default_factory=lambda: collections.deque(maxlen=200))
    cps: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)


# =========================
# BASE
# =========================
class BaseEngine:
    def __init__(self):
        self.enabled = True
        self.running = True
        self.buttons: Dict[str, Btn] = {}
        self.stats: Dict[str, Stats] = {}
        self._threads = []

    # ✅ FIX UI API
    def get_cps(self, key):
        return self.buttons.get(key, Btn()).cps

    def set_cps(self, key, value):
        if key in self.buttons:
            self.buttons[key].cps = max(1, value)

    def set_delay(self, key, value):
        if key in self.buttons:
            self.buttons[key].delay = max(0.0, value)

    def get_real_cps(self, key):
        return self.stats.get(key, Stats()).cps

    def stop(self):
        self.running = False

    def toggle_global(self):
        self.enabled = not self.enabled
        print(f"[GLOBAL] {self.enabled}")

    def _register(self, key):
        s = self.stats[key]
        now = time.perf_counter()
        with s.lock:
            s.timestamps.append(now)
            while s.timestamps and now - s.timestamps[0] > 1:
                s.timestamps.popleft()
            s.cps = len(s.timestamps)

    def _loop(self, key, action):
        print(f"[WORKER] {key}")

        while self.running:
            if not self.enabled or not self.buttons[key].active:
                time.sleep(0.01)
                continue

            b = self.buttons[key]
            interval = max(1 / b.cps, b.delay)

            start = time.perf_counter()
            action(key)
            self._register(key)

            sleep = interval - (time.perf_counter() - start)
            if sleep > 0:
                time.sleep(sleep)

    def _start_worker(self, key, action):
        t = threading.Thread(target=self._loop, args=(key, action), daemon=True)
        t.start()
        self._threads.append(t)

# =========================
# MOUSE (TOGGLE CLEAN)
# =========================
# file: engine.py (MouseEngine only)

# file: engine.py (MouseEngine only)

class MouseEngine(BaseEngine):
    def __init__(self):
        super().__init__()

        self.buttons = {"left": Btn(), "right": Btn()}
        self.stats = {k: Stats() for k in self.buttons}

        self._last_state = {"left": False, "right": False}
        self._press_time = {"left": 0.0, "right": 0.0}
        self._ignore_until = {"left": 0.0, "right": 0.0}

        self._start()
        self._listener()

    def _click(self, key):
        now = time.perf_counter()
        self._ignore_until[key] = now + 0.05  # ignore fake clicks

        if key == "left":
            send_mouse(MOUSEEVENTF_LEFTDOWN)
            send_mouse(MOUSEEVENTF_LEFTUP)
        else:
            send_mouse(MOUSEEVENTF_RIGHTDOWN)
            send_mouse(MOUSEEVENTF_RIGHTUP)

    def _start(self):
        for k in self.buttons:
            self._start_worker(k, self._click)

    def _listener(self):
        def loop():
            while True:
                now = time.perf_counter()

                l = bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)
                r = bool(user32.GetAsyncKeyState(VK_RBUTTON) & 0x8000)

                # ===== LEFT =====
                if now > self._ignore_until["left"]:
                    # press
                    if l and not self._last_state["left"]:
                        self._press_time["left"] = now

                    # release → TOGGLE
                    if not l and self._last_state["left"]:
                        if now - self._press_time["left"] > 0.02:
                            self.buttons["left"].active = not self.buttons["left"].active
                            print(f"[LEFT] {self.buttons['left'].active}")

                # ===== RIGHT =====
                if now > self._ignore_until["right"]:
                    if r and not self._last_state["right"]:
                        self._press_time["right"] = now

                    if not r and self._last_state["right"]:
                        if now - self._press_time["right"] > 0.02:
                            self.buttons["right"].active = not self.buttons["right"].active
                            print(f"[RIGHT] {self.buttons['right'].active}")

                self._last_state["left"] = l
                self._last_state["right"] = r

                time.sleep(0.005)

        threading.Thread(target=loop, daemon=True).start()

# =========================
# KEYBOARD
# =========================
class KeyEngine(BaseEngine):
    def __init__(self):
        super().__init__()

        self.buttons = {"1": Btn(), "2": Btn(), "3": Btn(), "4": Btn()}
        self.stats = {k: Stats() for k in self.buttons}
        self.vk = {"1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34}

        self._start()
        self._listener()

    def _press(self, key):
        vk = self.vk[key]
        send_key(vk, True)
        send_key(vk, False)

    def _start(self):
        for k in self.buttons:
            self._start_worker(k, self._press)

    def _listener(self):
        def loop():
            last = False
            while True:
                p = user32.GetAsyncKeyState(VK_XBUTTON1) & 0x8000 != 0

                if p and not last:
                    active = not any(b.active for b in self.buttons.values())
                    for b in self.buttons.values():
                        b.active = active
                    print(f"[KEYBOARD] {active}")

                last = p
                time.sleep(0.02)

        threading.Thread(target=loop, daemon=True).start()


# =========================
# MANAGER
# =========================
class MacroManager:
    def __init__(self):
        self.mouse = MouseEngine()
        self.keyboard = KeyEngine()
        self._listener()

    # ✅ FIX CRASH
    def toggle_all(self):
        self.mouse.toggle_global()
        self.keyboard.toggle_global()

    def stop(self):
        self.mouse.stop()
        self.keyboard.stop()

    def _listener(self):
        def loop():
            last = False
            while True:
                p = user32.GetAsyncKeyState(VK_XBUTTON2) & 0x8000 != 0

                if p and not last:
                    self.toggle_all()

                last = p
                time.sleep(0.02)

        threading.Thread(target=loop, daemon=True).start()