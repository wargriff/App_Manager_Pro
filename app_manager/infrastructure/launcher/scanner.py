from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

# =========================================================
# CONFIG
# =========================================================

SCAN_FOLDER = "folder"
SCAN_MANIFEST = "manifest"
SCAN_STEAM = "steam"
SCAN_BATTLENET_DB = "battlenet"

from app_manager.config.settings import CACHE_DB

# =========================================================
# CACHE
# =========================================================

class ScannerCache:

    def __init__(self):

        self.conn = sqlite3.connect(
            CACHE_DB,
            check_same_thread=False,
        )

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS programs (
            path TEXT PRIMARY KEY,
            name TEXT,
            source TEXT,
            size INTEGER,
            mtime REAL
        )
        """)

        self.conn.commit()

    def get(self, path: str):

        cur = self.conn.execute(
            """
            SELECT name, source, size, mtime
            FROM programs
            WHERE path = ?
            """,
            (path,),
        )

        return cur.fetchone()

    def set(
        self,
        name: str,
        path: str,
        source: str,
        size: int,
        mtime: float,
    ):

        self.conn.execute(
            """
            INSERT OR REPLACE INTO programs
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                path,
                name,
                source,
                size,
                mtime,
            ),
        )

        self.conn.commit()


# =========================================================
# HELPERS
# =========================================================

def resolve(path: str) -> str:
    return os.path.expandvars(path)


def find_exe(folder: str):

    try:

        best = None
        best_size = 0

        for file in os.listdir(folder):

            if not file.lower().endswith(".exe"):
                continue

            full = os.path.join(folder, file)

            try:
                size = os.path.getsize(full)
            except Exception:
                continue

            if size > best_size:
                best = full
                best_size = size

        return best or folder

    except Exception:
        return folder


# =========================================================
# MODELS
# =========================================================

@dataclass(slots=True)
class ManifestConfig:
    paths: list[str]
    extension: str


@dataclass(slots=True)
class Launcher:
    name: str
    scan_type: str
    roots: list[str]
    enabled: bool = True
    keywords: list[str] | None = None
    manifest: ManifestConfig | None = None


# =========================================================
# LAUNCHERS
# =========================================================

LAUNCHERS = [

    Launcher(
        name="Steam",
        scan_type=SCAN_STEAM,
        roots=[
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
        ],
    ),

    Launcher(
        name="Epic Games",
        scan_type=SCAN_FOLDER,
        roots=[
            r"C:\Program Files\Epic Games",
        ],
    ),

    Launcher(
        name="Ubisoft",
        scan_type=SCAN_FOLDER,
        roots=[
            r"C:\Program Files (x86)\Ubisoft",
        ],
    ),

    Launcher(
        name="Battle.net",
        scan_type=SCAN_BATTLENET_DB,
        roots=[],
    ),
]


# =========================================================
# STEAM
# =========================================================

def get_steam_libraries(roots: list[str]):

    libraries = set()

    for root in roots:

        root = resolve(root)

        vdf = os.path.join(
            root,
            "steamapps",
            "libraryfolders.vdf",
        )

        if not os.path.exists(vdf):
            continue

        try:

            with open(
                vdf,
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as file:

                for line in file:

                    if '"path"' not in line:
                        continue

                    parts = line.split('"')

                    if len(parts) < 5:
                        continue

                    path = parts[3].replace("\\\\", "\\")

                    common = os.path.join(
                        path,
                        "steamapps",
                        "common",
                    )

                    if os.path.isdir(common):
                        libraries.add(common)

        except Exception:
            continue

    return list(libraries)


# =========================================================
# SCANNER
# =========================================================

class LauncherScanner:

    def __init__(self, stop_event):

        self.stop_event = stop_event

        self.visited: set[str] = set()

        self.cache = ScannerCache()

    # =====================================================
    # ADD
    # =====================================================

    def add(
        self,
        callback,
        name,
        path,
        source="game",
    ):

        if not path:
            return

        key = os.path.normcase(path)

        if key in self.visited:
            return

        self.visited.add(key)

        try:

            stat = os.stat(path)

            cached = self.cache.get(path)

            if cached:

                _, _, _, cached_mtime = cached

                if cached_mtime == stat.st_mtime:

                    callback(
                        name,
                        path,
                        source,
                        stat.st_size,
                    )

                    return

            self.cache.set(
                name,
                path,
                source,
                stat.st_size,
                stat.st_mtime,
            )

            callback(
                name,
                path,
                source,
                stat.st_size,
            )

        except Exception:
            pass

    # =====================================================
    # FOLDER
    # =====================================================

    def scan_folder(
        self,
        launcher,
        callback,
    ):

        for root in launcher.roots:

            if self.stop_event.is_set():
                return

            root = resolve(root)

            if not os.path.exists(root):
                continue

            try:

                for item in os.listdir(root):

                    full = os.path.join(root, item)

                    if not os.path.isdir(full):
                        continue

                    exe = find_exe(full)

                    self.add(
                        callback,
                        item,
                        exe,
                    )

            except Exception:
                continue

    # =====================================================
    # STEAM
    # =====================================================

    def scan_steam(
        self,
        launcher,
        callback,
    ):

        libraries = get_steam_libraries(
            launcher.roots,
        )

        for library in libraries:

            if self.stop_event.is_set():
                return

            try:

                for game in os.listdir(library):

                    full = os.path.join(
                        library,
                        game,
                    )

                    if not os.path.isdir(full):
                        continue

                    exe = find_exe(full)

                    self.add(
                        callback,
                        game,
                        exe,
                    )

            except Exception:
                continue

    # =====================================================
    # BATTLENET
    # =====================================================

    def scan_battlenet_db(
        self,
            callback,
    ):

        db = os.path.expandvars(
            r"%PROGRAMDATA%\Battle.net\Agent\product.db"
        )

        if not os.path.exists(db):
            return

        try:

            with open(db, "rb") as file:

                content = file.read().decode(
                    "utf-8",
                    errors="ignore",
                )

            for line in content.splitlines():

                lower = line.lower()

                if ".exe" not in lower:
                    continue

                start = lower.find(":\\")
                end = lower.find(".exe")

                if start == -1:
                    continue

                exe = line[start - 1:end + 4]

                exe = exe.replace("\\\\", "\\")

                if not os.path.exists(exe):
                    continue

                name = Path(exe).stem

                self.add(
                    callback,
                    name,
                    exe,
                )

        except Exception:
            pass

    # =====================================================
    # MAIN
    # =====================================================

    def scan(
        self,
        callback,
    ):

        for launcher in LAUNCHERS:

            if self.stop_event.is_set():
                return

            if not launcher.enabled:
                continue

            try:

                if launcher.scan_type == SCAN_FOLDER:

                    self.scan_folder(
                        launcher,
                        callback,
                    )

                elif launcher.scan_type == SCAN_STEAM:

                    self.scan_steam(
                        launcher,
                        callback,
                    )

                elif launcher.scan_type == SCAN_BATTLENET_DB:

                    self.scan_battlenet_db(
                        callback,
                    )

            except Exception as error:

                print(
                    f"[LAUNCHER ERROR] {launcher.name}: {error}"
                )