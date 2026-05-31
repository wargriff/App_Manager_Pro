from __future__ import annotations

import os
import queue
import re
import sqlite3
import string
import threading
import winreg
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from app_manager.services.launcher_scanner import LauncherScanner

# =========================================================
# CONFIG
# =========================================================

MAX_WORKERS = min(32, (os.cpu_count() or 4) * 4)

MAX_DEPTH = 4

MIN_EXE_SIZE = 5_000_000

from app_manager.config import CACHE_DB


EXCLUDED_DIRS = {
    "windows",
    "programdata",
    "$recycle.bin",
    "temp",
    "cache",
    "logs",
    "winsxs",
    "system32",
    "driverstore",
    "node_modules",
    ".git",
    "__pycache__",
}


EXCLUDED_FILES = {
    "unins",
    "setup",
    "install",
    "update",
    "helper",
}


# =========================================================
# DATA
# =========================================================

@dataclass(slots=True)
class Program:
    name: str
    path: str
    source: str
    size: int = 0


# =========================================================
# CACHE
# =========================================================

class ScannerCache:

    def __init__(self):

        self.conn = sqlite3.connect(
            CACHE_DB,
            check_same_thread=False,
        )

        self.lock = threading.Lock()

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

    def load_all(self):

        with self.lock:

            cursor = self.conn.execute("""
            SELECT name, path, source, size
            FROM programs
            """)

            return cursor.fetchall()

    def save(
        self,
        name: str,
        path: str,
        source: str,
        size: int,
    ):

        try:

            mtime = os.path.getmtime(path)

        except Exception:
            mtime = 0

        with self.lock:

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
# SCANNER
# =========================================================

class ProgramScanner:

    def __init__(self) -> None:

        self.stop_event = threading.Event()

        self.seen: set[str] = set()

        self.seen_lock = threading.Lock()

        self.cache = ScannerCache()

        self.launcher_scanner = LauncherScanner(
            self.stop_event
        )

    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.stop_event.clear()

        with self.seen_lock:
            self.seen.clear()

    # =====================================================
    # SAFE EMIT
    # =====================================================

    def emit(
        self,
        callback,
        program: Program,
    ) -> None:

        if self.stop_event.is_set():
            return

        key = self.make_key(
            program.name,
            program.path,
        )

        with self.seen_lock:

            if key in self.seen:
                return

            self.seen.add(key)

        self.cache.save(
            program.name,
            program.path,
            program.source,
            program.size,
        )

        if callback:

            try:
                callback(program)

            except Exception as error:
                print("[CALLBACK ERROR]", error)

    # =====================================================
    # GLOBAL SCAN
    # =====================================================

    def scan_all(
        self,
        callback=None,
        include_portable=False,
    ) -> None:

        self.reset()

        # ==========================================
        # CACHE PRELOAD
        # ==========================================

        try:

            for (
                name,
                path,
                source,
                size,
            ) in self.cache.load_all():

                if path and os.path.exists(path):

                    self.emit(
                        callback,
                        Program(
                            name=name,
                            path=path,
                            source=source,
                            size=size,
                        ),
                    )

        except Exception as error:
            print("[CACHE ERROR]", error)

        # ==========================================
        # THREADS
        # ==========================================

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:

            futures = [

                executor.submit(
                    self.scan_registry,
                    callback,
                ),

                executor.submit(
                    self.scan_emulators,
                    callback,
                ),

                executor.submit(
                    self.scan_launchers,
                    callback,
                ),
            ]

            if include_portable:

                futures.append(

                    executor.submit(
                        self.scan_portable,
                        callback,
                    )
                )

            for future in futures:

                if self.stop_event.is_set():
                    return

                try:
                    future.result()

                except Exception as error:
                    print("[SCAN ERROR]", error)

    # =====================================================
    # LAUNCHERS
    # =====================================================

    def scan_launchers(
        self,
        callback,
    ) -> None:

        self.launcher_scanner.scan(

            lambda n, p, s, z=0: self.emit(
                callback,
                Program(
                    name=n,
                    path=p,
                    source=s,
                    size=z,
                ),
            )
        )

    # =====================================================
    # REGISTRY
    # =====================================================

    def scan_registry(
        self,
        callback,
    ) -> None:

        registry_paths = [

            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            ),

            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            ),

            (
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            ),
        ]

        for hive, reg_path in registry_paths:

            if self.stop_event.is_set():
                return

            try:

                with winreg.OpenKey(
                    hive,
                    reg_path,
                ) as key:

                    count = winreg.QueryInfoKey(key)[0]

                    for i in range(count):

                        if self.stop_event.is_set():
                            return

                        try:

                            subkey_name = winreg.EnumKey(
                                key,
                                i,
                            )

                            with winreg.OpenKey(
                                key,
                                subkey_name,
                            ) as subkey:

                                name = self.safe_reg_query(
                                    subkey,
                                    "DisplayName",
                                )

                                if not name:
                                    continue

                                install = self.safe_reg_query(
                                    subkey,
                                    "InstallLocation",
                                )

                                uninstall = self.safe_reg_query(
                                    subkey,
                                    "UninstallString",
                                )

                                exe = self.extract_exe(
                                    install,
                                    uninstall,
                                )

                                self.emit(
                                    callback,
                                    Program(
                                        name=name,
                                        path=exe,
                                        source="installed",
                                    ),
                                )

                        except Exception:
                            continue

            except Exception:
                continue

    # =====================================================
    # EMULATORS
    # =====================================================

    def scan_emulators(
        self,
        callback,
    ) -> None:

        roots = [

            os.path.expandvars("%APPDATA%"),

            os.path.expandvars("%LOCALAPPDATA%"),

            os.path.expanduser("~/Documents"),
        ]

        keywords = {
            "yuzu",
            "ryujinx",
            "dolphin",
            "pcsx2",
            "cemu",
        }

        for root in roots:

            if not os.path.exists(root):
                continue

            for current, dirs, files in os.walk(root):

                if self.stop_event.is_set():
                    return

                depth = current[len(root):].count(os.sep)

                if depth > 3:

                    dirs[:] = []

                    continue

                dirs[:] = [
                    d for d in dirs
                    if self.is_valid_dir(d)
                ]

                for file in files:

                    lower = file.lower()

                    if not lower.endswith(".exe"):
                        continue

                    if not any(
                        k in lower
                        for k in keywords
                    ):
                        continue

                    self.emit(
                        callback,
                        Program(
                            name=Path(file).stem,
                            path=os.path.join(
                                current,
                                file,
                            ),
                            source="emulator",
                        ),
                    )

    # =====================================================
    # PORTABLE
    # =====================================================

    def scan_portable(
        self,
        callback,
    ) -> None:

        path_queue: queue.Queue = queue.Queue()

        for drive in self.get_drives():

            path_queue.put((drive, 0))

        def worker():

            while not self.stop_event.is_set():

                try:
                    current, depth = (
                        path_queue.get(timeout=1)
                    )

                except queue.Empty:
                    return

                try:

                    self.scan_directory(
                        current,
                        depth,
                        callback,
                        path_queue,
                    )

                finally:

                    path_queue.task_done()

        threads = []

        for _ in range(min(16, MAX_WORKERS)):

            thread = threading.Thread(
                target=worker,
                daemon=True,
            )

            thread.start()

            threads.append(thread)

        path_queue.join()

        for thread in threads:
            thread.join(timeout=0.2)

    def scan_directory(
        self,
        path: str,
        depth: int,
        callback,
        path_queue: queue.Queue,
    ) -> None:

        if depth > MAX_DEPTH:
            return

        try:

            with os.scandir(path) as entries:

                for entry in entries:

                    if self.stop_event.is_set():
                        return

                    try:

                        if entry.is_dir(
                            follow_symlinks=False,
                        ):

                            if not self.is_valid_dir(
                                entry.name,
                            ):
                                continue

                            path_queue.put(
                                (
                                    entry.path,
                                    depth + 1,
                                )
                            )

                            continue

                        if not entry.is_file(
                            follow_symlinks=False,
                        ):
                            continue

                        if not self.is_valid_exe(entry):
                            continue

                        stat = entry.stat(
                            follow_symlinks=False,
                        )

                        self.emit(
                            callback,
                            Program(
                                name=Path(entry.name).stem,
                                path=entry.path,
                                source="portable",
                                size=stat.st_size,
                            ),
                        )

                    except Exception:
                        continue

        except Exception:
            return

    # =====================================================
    # HELPERS
    # =====================================================

    @staticmethod
    def make_key(
        name: str,
        path: str,
    ) -> str:

        return (
            f"{name.lower()}::"
            f"{os.path.normcase(path)}"
        )

    @staticmethod
    def safe_reg_query(
        key,
        value,
    ):

        try:

            return winreg.QueryValueEx(
                key,
                value,
            )[0]

        except Exception:
            return ""

    @staticmethod
    def extract_exe(
        install: str,
        uninstall: str,
    ) -> str:

        candidates = [
            install,
            uninstall,
        ]

        for candidate in candidates:

            if not candidate:
                continue

            candidate = candidate.strip().strip('"')

            match = re.search(
                r'([A-Za-z]:\\[^"]+\.exe)',
                candidate,
                re.IGNORECASE,
            )

            if not match:
                continue

            exe = match.group(1)

            if os.path.isfile(exe):
                return exe

        return ""

    @staticmethod
    def get_drives():

        return [

            f"{d}:\\"

            for d in string.ascii_uppercase

            if os.path.exists(f"{d}:\\")
        ]

    @staticmethod
    def is_valid_dir(
        name: str,
    ) -> bool:

        lower = name.lower()

        if lower.startswith("."):
            return False

        return lower not in EXCLUDED_DIRS

    @staticmethod
    def is_valid_exe(
        entry,
    ) -> bool:

        try:

            lower = entry.name.lower()

            if not lower.endswith(".exe"):
                return False

            if any(
                x in lower
                for x in EXCLUDED_FILES
            ):
                return False

            stat = entry.stat(
                follow_symlinks=False
            )

            return (
                stat.st_size >= MIN_EXE_SIZE
            )

        except Exception:
            return False

    # =====================================================
    # STOP
    # =====================================================

    def stop(self) -> None:

        self.stop_event.set()


# =========================================================
# GLOBAL INSTANCE
# =========================================================

_scanner_instance = ProgramScanner()


# =========================================================
# PUBLIC API
# =========================================================

def scan_all(
    callback,
    include_portable=False,
):

    _scanner_instance.scan_all(
        callback,
        include_portable=include_portable,
    )


def stop_scan():
    _scanner_instance.stop_event.set()