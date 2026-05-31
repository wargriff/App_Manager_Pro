from __future__ import annotations

import hashlib
import os
import sqlite3
import threading

from app_manager.config import CACHE_DB


class ScannerCache:

    def __init__(self):

        self.lock = threading.Lock()

        self.conn = sqlite3.connect(
            CACHE_DB,
            check_same_thread=False,
        )

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS programs (
                path TEXT PRIMARY KEY,
                name TEXT,
                source TEXT,
                size INTEGER,
                mtime REAL,
                hash TEXT
            )
            """
        )

        self.conn.commit()

    # =====================================================
    # HASH
    # =====================================================

    @staticmethod
    def fast_hash(path: str) -> str:

        try:

            stat = os.stat(path)

            raw = (
                f"{path}|"
                f"{stat.st_size}|"
                f"{stat.st_mtime}"
            )

            return hashlib.md5(
                raw.encode()
            ).hexdigest()

        except Exception:
            return ""

    # =====================================================
    # GET
    # =====================================================

    def exists(
        self,
        path: str,
    ) -> bool:

        with self.lock:

            cur = self.conn.execute(
                """
                SELECT 1
                FROM programs
                WHERE path = ?
                """,
                (path,),
            )

            return cur.fetchone() is not None

    # =====================================================
    # ADD
    # =====================================================

    def add(
        self,
        name: str,
        path: str,
        source: str,
        size: int,
    ) -> None:

        try:

            stat = os.stat(path)

            with self.lock:

                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO programs (
                        path,
                        name,
                        source,
                        size,
                        mtime,
                        hash
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        path,
                        name,
                        source,
                        size,
                        stat.st_mtime,
                        self.fast_hash(path),
                    ),
                )

                self.conn.commit()

        except Exception:
            pass

    # =====================================================
    # LOAD
    # =====================================================

    def load_all(self):

        with self.lock:

            cur = self.conn.execute(
                """
                SELECT
                    name,
                    path,
                    source,
                    size
                FROM programs
                """
            )

            return cur.fetchall()

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.conn.close()