from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class Utils:

    # =====================================================
    # 📂 OPEN FOLDER
    # =====================================================

    @staticmethod
    def open_folder(path: str) -> bool:

        try:

            if not path:
                return False

            target = Path(path)

            if target.is_file():
                target = target.parent

            if not target.exists():
                raise FileNotFoundError(
                    f"Dossier introuvable: {target}"
                )

            subprocess.Popen(
                ["explorer", os.path.normpath(path)]
            )

            return True

        except Exception as error:

            print(f"[OPEN FOLDER ERROR] {error}")

            return False

    # =====================================================
    # 🎯 OPEN + SELECT FILE
    # =====================================================

    @staticmethod
    def open_and_select(path: str) -> bool:

        try:

            if not path:
                return False

            target = Path(path)

            if not target.exists():
                raise FileNotFoundError(
                    f"Fichier introuvable: {target}"
                )

            subprocess.run(
                [
                    "explorer",
                    f"/select,{target}"
                ],
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            return True

        except Exception as error:

            print(f"[SELECT ERROR] {error}")

            return False

    # =====================================================
    # 🚀 RUN APP
    # =====================================================

    @staticmethod
    def run_app(path: str) -> bool:

        try:

            if not path:
                return False

            target = Path(path)

            if not target.exists():
                raise FileNotFoundError(
                    f"Fichier introuvable: {target}"
                )

            if not target.is_file():
                raise ValueError(
                    f"Ce n'est pas un fichier: {target}"
                )

            if target.suffix.lower() != ".exe":
                raise ValueError(
                    f"Fichier non exécutable: {target}"
                )

            subprocess.Popen(
                [str(target)],
                shell=True,
                cwd=str(target.parent),
            )

            return True

        except Exception as error:

            print(f"[RUN ERROR] {error}")

            return False

    # =====================================================
    # 🔥 RUN AS ADMIN
    # =====================================================

    @staticmethod
    def run_as_admin(path: str) -> bool:

        try:

            if not path:
                return False

            target = Path(path)

            if not target.exists():
                raise FileNotFoundError(
                    f"Fichier introuvable: {target}"
                )

            powershell = (
                f'Start-Process "{target}" '
                f'-Verb RunAs'
            )

            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    powershell,
                ],
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            return True

        except Exception as error:

            print(f"[ADMIN ERROR] {error}")

            return False

    # =====================================================
    # 📋 COPY TO CLIPBOARD
    # =====================================================

    @staticmethod
    def copy_to_clipboard(
        root,
        text: str,
    ) -> bool:

        try:

            root.clipboard_clear()

            root.clipboard_append(text)

            root.update()

            return True

        except Exception as error:

            print(f"[CLIPBOARD ERROR] {error}")

            return False

    # =====================================================
    # 🗑️ DELETE FOLDER
    # =====================================================

    @staticmethod
    def delete_folder(path: str) -> bool:

        try:

            if not path:
                return False

            target = Path(path)

            if not target.exists():
                return False

            shutil.rmtree(target)

            return True

        except Exception as error:

            print(f"[DELETE FOLDER ERROR] {error}")

            return False

    # =====================================================
    # 📄 DELETE FILE
    # =====================================================

    @staticmethod
    def delete_file(path: str) -> bool:

        try:

            if not path:
                return False

            target = Path(path)

            if not target.exists():
                return False

            target.unlink()

            return True

        except Exception as error:

            print(f"[DELETE FILE ERROR] {error}")

            return False

    # =====================================================
    # 🔍 EXISTS
    # =====================================================

    @staticmethod
    def exists(path: str) -> bool:

        try:
            return Path(path).exists()

        except Exception:
            return False

    # =====================================================
    # 📊 FILE SIZE
    # =====================================================

    @staticmethod
    def get_size(path: str) -> int:

        try:

            target = Path(path)

            if not target.is_file():
                return 0

            return target.stat().st_size

        except Exception:
            return 0

    # =====================================================
    # 🧠 FORMAT SIZE
    # =====================================================

    @staticmethod
    def format_size(size: int | float) -> str:

        try:

            size = float(size)

            for unit in [
                "B",
                "KB",
                "MB",
                "GB",
                "TB",
            ]:

                if size < 1024:
                    return f"{size:.2f} {unit}"

                size /= 1024

            return f"{size:.2f} PB"

        except Exception:
            return "0 B"

    # =====================================================
    # 📂 FILE NAME
    # =====================================================

    @staticmethod
    def get_filename(path: str) -> str:

        try:
            return Path(path).name

        except Exception:
            return ""

    # =====================================================
    # 📁 PARENT FOLDER
    # =====================================================

    @staticmethod
    def get_folder(path: str) -> str:

        try:
            return str(Path(path).parent)

        except Exception:
            return ""