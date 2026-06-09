"""Configuration globale de l'application."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PACKAGE_DIR.parent
DATA_DIR = PROJECT_ROOT
LOG_DIR = PROJECT_ROOT / "logs"

APP_NAME = "🔥 App Manager Pro"
APP_VERSION = "2.0.0"
WINDOW_SIZE = (1400, 850)
MIN_WINDOW_SIZE = (900, 600)

QUEUE_BATCH_SIZE = 250
SCAN_WORKERS = 8
PORTABLE_MIN_EXE_BYTES = 5_000_000
SCAN_MAX_DEPTH = 5

CACHE_DB = str(DATA_DIR / "scanner_cache.db")
LOG_FILE = str(LOG_DIR / "app_manager.log")

# Raccourcis clavier
SHORTCUT_QUIT = "<Escape>"
SHORTCUT_RESCAN = "<Control-r>"
