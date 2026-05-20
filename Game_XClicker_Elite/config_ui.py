# file: config_ui.py

from dataclasses import dataclass, field
from typing import Dict, Tuple, List


# =========================
# GLOBAL STYLE
# =========================
GLOBAL_STYLE = """
QWidget { background:#0a0a0a; color:#00ff88; font-family:Consolas; }
QSlider::groove:horizontal { height:6px; background:#222; border-radius:3px; }
QSlider::handle:horizontal { background:#00ff88; width:14px; margin:-5px 0; border-radius:7px; }
QPushButton { background:#111; border:1px solid #00ff88; padding:6px; }
QPushButton:hover { background:#00ff88; color:black; }
"""

SLIDER_STYLE = """
QSlider::groove:horizontal{height:4px;background:#111;}
QSlider::handle:horizontal{background:#00ff88;width:12px;border-radius:6px;}
"""


# =========================
# CONTROL CONFIG
# =========================
@dataclass
class ControlConfig:
    cps_range: Tuple[int, int] = (1, 50)
    delay_range: Tuple[float, float] = (0.001, 0.2)

    default_cps: int = 10
    default_delay: float = 0.01

    def clamp_cps(self, value: int) -> int:
        return max(self.cps_range[0], min(self.cps_range[1], value))

    def clamp_delay(self, value: float) -> float:
        return max(self.delay_range[0], min(self.delay_range[1], value))


# =========================
# PRESETS (FIXED CONSISTENCY)
# =========================
# (cps, delay)
PRESETS: Dict[str, Tuple[int, float]] = {
    "SAFE": (6, 0.08),
    "MID": (12, 0.03),
    "FAST": (18, 0.015),
}


# =========================
# OPTIONS
# =========================
@dataclass
class OptionsConfig:
    jitter: bool = False
    human: bool = False


# =========================
# MAIN UI CONFIG
# =========================
@dataclass
class UIConfig:
    window_title: str = "XMacro Elite PRO"
    size: Tuple[int, int] = (1100, 650)

    keys: List[str] = field(default_factory=lambda: [
        "left", "right", "1", "2", "3", "4"
    ])


CONFIG = UIConfig()