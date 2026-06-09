import sys
from pathlib import Path
from typing import Optional, Union

# ==========================================================
# BASE PATH (cached)
# ==========================================================

_BASE_PATH: Optional[Path] = None


def get_base_path() -> Path:
    """
    Retourne le dossier racine du projet ou du bundle PyInstaller.
    Compatible dev + exe.
    """

    global _BASE_PATH

    if _BASE_PATH is not None:
        return _BASE_PATH

    # ==========================
    # CAS PYINSTALLER
    # ==========================
    if getattr(sys, "frozen", False):
        _BASE_PATH = Path(sys._MEIPASS)

    # ==========================
    # CAS DEV (IMPORTANT FIX)
    # ==========================
    else:
        # 🔥 remonte à la racine du projet
        _BASE_PATH = Path(__file__).resolve().parents[2]

    return _BASE_PATH


# ==========================================================
# RESOURCE PATH
# ==========================================================

def resource_path(relative: Union[str, Path]) -> Path:
    """
    Retourne le chemin absolu d'une ressource.
    """

    path = get_base_path() / Path(relative)

    return path


# ==========================================================
# RESOURCE DIR
# ==========================================================

def resource_dir(directory: Union[str, Path]) -> Path:
    """
    Retourne le chemin d'un dossier de ressources.
    """

    return resource_path(directory)