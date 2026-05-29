import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer

from Xmacro_main import EngineProxy
from engine_win32 import MacroManager


class ClickTest(QWidget):
    def __init__(self, engine):
        super().__init__()

        self.engine = engine
        self.start_time = None
        self.auto = False

        self.setWindowTitle("XMacro Test")
        self.resize(500, 400)

        self.setStyleSheet("""
            QWidget { background:#0a0a0a; color:#00ff88; font-family:Consolas; }
            QPushButton { border:1px solid #00ff88; padding:6px; }
            QPushButton:hover { background:#00ff88; color:black; }
        """)

        layout = QVBoxLayout()

        self.timer_label = QLabel("0.00 s")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cps_label = QLabel("CPS: 0.0")
        self.cps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.click_area = QLabel("CLICK ZONE")
        self.click_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.click_area.setFixedHeight(200)
        self.click_area.setStyleSheet("""
            background:black;
            border:2px solid #00ff88;
            font-size:16px;
        """)

        self.click_area.mousePressEvent = self.manual_click

        self.auto_btn = QPushButton("AUTO: OFF")
        self.auto_btn.setCheckable(True)
        self.auto_btn.clicked.connect(self.toggle_auto)

        layout.addWidget(self.timer_label)
        layout.addWidget(self.cps_label)
        layout.addWidget(self.click_area)
        layout.addWidget(self.auto_btn)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(50)

    # -------------------------
    def toggle_auto(self):
        self.auto = not self.auto

        if self.auto:
            self.auto_btn.setText("AUTO: ON")

            if not self.engine.enabled:
                self.engine.toggle()

            self.engine.set_active("left", True)
            self.start_time = time.time()

        else:
            self.auto_btn.setText("AUTO: OFF")
            self.engine.set_active("left", False)

    # -------------------------
    def manual_click(self, event):
        if not self.auto:
            if not self.start_time:
                self.start_time = time.time()

            # simulate engine stat for manual mode
            self.engine.manager.mouse._register("left")

    # -------------------------
    def update_ui(self):
        if not self.start_time:
            self.timer_label.setText("0.00s")
            self.cps_label.setText("CPS: 0.0")
            return

        elapsed = time.time() - self.start_time
        self.timer_label.setText(f"{elapsed:.2f}s")

        # 🔥 KEY FIX: toujours lire engine
        cps = self.engine.get_cps("left")

        self.cps_label.setText(f"CPS: {cps:.1f}")


# =========================
def main():
    app = QApplication(sys.argv)

    engine = EngineProxy(MacroManager())

    w = ClickTest(engine)
    w.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
