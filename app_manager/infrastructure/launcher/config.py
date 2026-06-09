# launcher_config.py

from __future__ import annotations

import os
from dataclasses import dataclass, field

SCAN_FOLDER = "folder"
SCAN_MANIFEST = "manifest"
SCAN_STEAM = "steam"
SCAN_BATTLENET_DB = "battlenet_db"


# =====================================================
# MANIFEST
# =====================================================

@dataclass(slots=True, frozen=True)
class ManifestConfig:

    paths: list[str]

    extension: str

    def expanded_paths(self) -> list[str]:

        return [
            os.path.expandvars(path)
            for path in self.paths
        ]


# =====================================================
# LAUNCHER
# =====================================================

@dataclass(slots=True)
class Launcher:

    name: str

    scan_type: str

    roots: list[str] = field(default_factory=list)

    enabled: bool = True

    keywords: list[str] = field(default_factory=list)

    manifest: ManifestConfig | None = None

    # =========================================
    # HELPERS
    # =========================================

    def expanded_roots(self) -> list[str]:

        return [
            os.path.expandvars(root)
            for root in self.roots
        ]

    def existing_roots(self) -> list[str]:

        return [
            path
            for path in self.expanded_roots()
            if os.path.exists(path)
        ]


# =====================================================
# LAUNCHERS
# =====================================================

LAUNCHERS: list[Launcher] = [

    # =========================================
    # STEAM
    # =========================================

    Launcher(
        name="Steam",
        scan_type=SCAN_STEAM,
        roots=[
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
            r"%LOCALAPPDATA%\Steam",
        ],
        keywords=[
            "steam",
            "steamapps",
        ],
    ),

    # =========================================
    # EPIC GAMES
    # =========================================

    Launcher(
        name="Epic Games",
        scan_type=SCAN_MANIFEST,
        manifest=ManifestConfig(
            paths=[
                r"%PROGRAMDATA%\Epic\EpicGamesLauncher\Data\Manifests",
            ],
            extension=".item",
        ),
        keywords=[
            "epic",
            "epic games",
        ],
    ),

    # =========================================
    # BATTLENET
    # =========================================

    Launcher(
        name="Battle.net",
        scan_type=SCAN_BATTLENET_DB,
        roots=[
            r"%PROGRAMDATA%\Battle.net",
            r"%LOCALAPPDATA%\Battle.net",
        ],
        keywords=[
            "battle.net",
            "blizzard",
        ],
    ),

    # =========================================
    # RIOT
    # =========================================

    Launcher(
        name="Riot",
        scan_type=SCAN_FOLDER,
        roots=[
            r"C:\Riot Games",
            r"%LOCALAPPDATA%\Riot Games",
        ],
        keywords=[
            "riot",
            "valorant",
            "league of legends",
        ],
    ),

    # =========================================
    # UBISOFT
    # =========================================

    Launcher(
        name="Ubisoft",
        scan_type=SCAN_FOLDER,
        roots=[
            r"C:\Program Files (x86)\Ubisoft",
            r"C:\Program Files\Ubisoft",
        ],
        keywords=[
            "ubisoft",
            "uplay",
        ],
    ),

    # =========================================
    # EA APP
    # =========================================

    Launcher(
        name="EA App",
        scan_type=SCAN_FOLDER,
        roots=[
            r"C:\Program Files\Electronic Arts",
            r"C:\Program Files\EA Games",
        ],
        keywords=[
            "ea",
            "origin",
        ],
    ),

    # =========================================
    # GOG
    # =========================================

    Launcher(
        name="GOG Galaxy",
        scan_type=SCAN_FOLDER,
        roots=[
            r"C:\Program Files (x86)\GOG Galaxy",
        ],
        keywords=[
            "gog",
            "galaxy",
        ],
    ),
]