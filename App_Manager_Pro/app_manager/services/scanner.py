# scanner.py

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

# =========================================================
# CONFIG
# =========================================================

CPU_COUNT = os.cpu_count() or 4

MAX_WORKERS = min(64, CPU_COUNT * 8)

MAX_DEPTH = 5

MIN_EXE_SIZE = 5_000_000

from app_manager.config import CACHE_DB

EMIT_BATCH_SIZE = 100


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
    "amd",
    "intel",
    "nvidia",
    "packages",
    "msixvc",
}


EXCLUDED_FILES = {
    "unins",
    "setup",
    "install",
    "update",
    "helper",
    "crash",
    "report",
    "vc_redist",
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

        self.pending = []

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
        name,
        path,
        source,
        size,
    ):

        try:
            mtime = os.path.getmtime(path)

        except Exception:
            mtime = 0

        with self.lock:

            self.pending.append(
                (
                    path,
                    name,
                    source,
                    size,
                    mtime,
                )
            )

            if len(self.pending) >= 250:

                self.flush()

    def flush(self):

        if not self.pending:
            return

        self.conn.executemany(
            """
            INSERT OR REPLACE INTO programs
            VALUES (?, ?, ?, ?, ?)
            """,
            self.pending,
        )

        self.conn.commit()

        self.pending.clear()

    def close(self):

        with self.lock:

            self.flush()

            self.conn.close()


# =========================================================
# SCANNER
# =========================================================

class ProgramScanner:

    def __init__(self):

        self.stop_event = threading.Event()

        self.cache = ScannerCache()

        self.seen_lock = threading.Lock()

        self.seen: set[str] = set()

    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.stop_event.clear()

        with self.seen_lock:
            self.seen.clear()

    # =====================================================
    # EMIT
    # =====================================================

    def emit(
        self,
        callback,
        program: Program,
    ):

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
    ):

        self.reset()

        self.preload_cache(callback)

        with ThreadPoolExecutor(
            max_workers=8,
        ) as executor:

            futures = [

                executor.submit(
                    self.scan_registry,
                    callback,
                ),

                executor.submit(
                    self.scan_portable,
                    callback,
                ),
            ]

            for future in futures:

                try:
                    future.result()

                except Exception as error:
                    print("[SCAN ERROR]", error)

        self.cache.flush()

    # =====================================================
    # CACHE
    # =====================================================

    def preload_cache(self, callback):

        try:

            for (
                name,
                path,
                source,
                size,
            ) in self.cache.load_all():

                if not path:
                    continue

                if not os.path.exists(path):
                    continue

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

    # =====================================================
    # REGISTRY
    # =====================================================

    def scan_registry(
        self,
        callback,
    ):

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

                                display_icon = self.safe_reg_query(
                                    subkey,
                                    "DisplayIcon",
                                )

                                exe = self.extract_exe(
                                    install,
                                    uninstall,
                                    display_icon,
                                )

                                if not exe and install:
                                    exe = install.strip().strip('"')

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
    # FAST PORTABLE SCAN
    # =====================================================

    def scan_portable(
        self,
        callback,
    ):

        path_queue: queue.Queue = queue.Queue()

        drives = self.get_drives()

        for drive in drives:
            path_queue.put((drive, 0))

        worker_count = min(16, MAX_WORKERS)

        portable_done = threading.Event()

        def worker():

            local_batch = []

            while (
                not portable_done.is_set()
                and not self.stop_event.is_set()
            ):

                try:
                    current, depth = path_queue.get(timeout=1)

                except queue.Empty:
                    continue

                try:

                    self.scan_directory(
                        current,
                        depth,
                        path_queue,
                        local_batch,
                    )

                    if len(local_batch) >= EMIT_BATCH_SIZE:

                        for item in local_batch:
                            self.emit(callback, item)

                        local_batch.clear()

                finally:
                    path_queue.task_done()

            if local_batch:

                for item in local_batch:
                    self.emit(callback, item)

        threads = []

        for _ in range(worker_count):

            thread = threading.Thread(
                target=worker,
                daemon=True,
            )

            thread.start()

            threads.append(thread)

        path_queue.join()

        portable_done.set()

        for thread in threads:
            thread.join(timeout=0.5)

    def scan_directory(
        self,
        path,
        depth,
            path_queue,
        batch,
    ):

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

                        if not entry.name.lower().endswith(".exe"):
                            continue

                        lower = entry.name.lower()

                        if any(
                            x in lower
                            for x in EXCLUDED_FILES
                        ):
                            continue

                        stat = entry.stat(
                            follow_symlinks=False,
                        )

                        if stat.st_size < MIN_EXE_SIZE:
                            continue

                        batch.append(
                            Program(
                                name=Path(entry.name).stem,
                                path=entry.path,
                                source="portable",
                                size=stat.st_size,
                            )
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
        name,
        path,
    ):

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
        install,
        uninstall,
        display_icon="",
    ):

        candidates = [
            display_icon,
            install,
            uninstall,
        ]

        for candidate in candidates:

            if not candidate:
                continue

            candidate = candidate.strip().strip('"')

            if "," in candidate:
                candidate = candidate.split(",", 1)[0].strip().strip('"')

            match = re.search(
                r'([A-Za-z]:\\[^"]+\.exe)',
                candidate,
                re.IGNORECASE,
            )

            if match:

                exe = match.group(1)

                if os.path.isfile(exe):
                    return exe

            if candidate.lower().endswith(".exe") and os.path.isfile(candidate):
                return candidate

        if install:

            install = install.strip().strip('"')

            if os.path.isdir(install):

                try:

                    for entry in os.scandir(install):

                        if (
                            entry.is_file(follow_symlinks=False)
                            and entry.name.lower().endswith(".exe")
                            and not any(
                                x in entry.name.lower()
                                for x in EXCLUDED_FILES
                            )
                        ):
                            return entry.path

                except Exception:
                    pass

        return ""

    @staticmethod
    def get_drives():

        return [

            f"{d}:\\"

            for d in string.ascii_uppercase

            if os.path.exists(f"{d}:\\")
        ]

    @staticmethod
    def is_valid_dir(name):

        lower = name.lower()

        if lower.startswith("."):
            return False

        return lower not in EXCLUDED_DIRS

    # =====================================================
    # STOP
    # =====================================================

    def stop(self):

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
    include_portable=True,
):

    _scanner_instance.scan_all(
        callback,
    )


def stop_scan():

    _scanner_instance.stop()