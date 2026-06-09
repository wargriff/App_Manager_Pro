# file: rgb_engine.py

import math
import time
from typing import Dict

from PyQt6.QtGui import QColor


class RGBZone:
    def __init__(self):
        self.mode = "static"
        self.color = QColor(0, 255, 120)
        self._flash = 0.0


class RGBEngine:
    def __init__(self):
        self.zones: Dict[str, RGBZone] = {
            "left": RGBZone(),
            "right": RGBZone(),
            "wheel": RGBZone(),
            "dpi": RGBZone(),
            "side1": RGBZone(),
            "side2": RGBZone(),
        }

        self._t = 0.0
        self._last = time.perf_counter()

        self.speed = 2.0

    # -------------------------
    # UPDATE
    # -------------------------
    def update(self):
        now = time.perf_counter()
        dt = now - self._last
        self._last = now

        self._t += dt * self.speed

        for z in self.zones.values():
            if z._flash > 0:
                z._flash -= dt * 3
                if z._flash < 0:
                    z._flash = 0

    # -------------------------
    # PUBLIC API
    # -------------------------
    def set_mode(self, zone: str, mode: str):
        if zone in self.zones:
            self.zones[zone].mode = mode.lower()

    def set_color(self, zone: str, color: QColor):
        if zone in self.zones:
            self.zones[zone].color = color

    def get_color(self, zone: str) -> QColor:
        if zone not in self.zones:
            return QColor(0, 255, 120)

        z = self.zones[zone]

        if z.mode == "static":
            return z.color

        if z.mode == "breathing":
            factor = (math.sin(self._t) + 1) / 2
            return self._scale(z.color, factor)

        if z.mode == "rainbow":
            return self._rainbow()

        if z.mode == "reactive":
            factor = 0.3 + z._flash
            return self._scale(z.color, factor)

        return z.color

    # -------------------------
    # HELPERS
    # -------------------------
    def _scale(self, color: QColor, factor: float) -> QColor:
        factor = max(0.0, min(1.0, factor))  # clamp

        return QColor(
            int(color.red() * factor),
            int(color.green() * factor),
            int(color.blue() * factor),
        )

    def _rainbow(self) -> QColor:
        h = (self._t * 60) % 360
        c = QColor()
        c.setHsv(int(h), 255, 255)
        return c

    # -------------------------
    # EVENTS
    # -------------------------
    def trigger_reactive(self, zone: str):
        if zone in self.zones:
            self.zones[zone]._flash = 1.0