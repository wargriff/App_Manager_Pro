"""Détection et fusion des vrais doublons (sans masquer les programmes distincts)."""

from __future__ import annotations

import os
import re
from typing import Optional

from app_manager.domain.models.app_item import AppItem

SOURCE_PRIORITY: dict[str, int] = {
    "installed": 100,
    "registry": 95,
    "winget": 80,
    "portable": 40,
}

_NOISE_IN_NAME = (
    "uninstall ",
    " uninstall",
    "setup ",
    "vc_redist",
    "crash handler",
)


def normalize_name(name: str) -> str:

    if not name:
        return ""

    text = name.lower().strip()

    for token in (" (x64)", " (x86)", " x64", " x86"):
        text = text.replace(token, "")

    text = re.sub(r"\s+v?\d+(\.\d+){0,3}$", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)

    return " ".join(text.split())


def normalize_path(path: Optional[str]) -> str:

    if not path:
        return ""

    try:
        return os.path.normcase(os.path.normpath(path.strip().strip('"')))
    except Exception:
        return ""


def source_priority(item: AppItem) -> int:
    return SOURCE_PRIORITY.get(item.source.lower(), 50)


def is_noise_item(item: AppItem) -> bool:

    name = item.name.lower()
    path = (item.path or "").lower()

    if any(x in name for x in _NOISE_IN_NAME):
        return True

    if path and os.path.basename(path).startswith("unins"):
        return True

    return False


def are_duplicates(a: AppItem, b: AppItem) -> bool:

    """Doublon strict : même exe, même winget, ou winget + installé (fusion)."""

    if a is b:
        return True

    path_a = normalize_path(a.path)
    path_b = normalize_path(b.path)

    # Même fichier exécutable
    if path_a and path_b and path_a == path_b:
        return True

    # Même ID Winget
    if (
        a.winget_id
        and b.winget_id
        and a.winget_id.lower() == b.winget_id.lower()
    ):
        return True

    name_a = normalize_name(a.name)
    name_b = normalize_name(b.name)

    if not name_a or name_a != name_b:
        return False

    # Winget (sans chemin) + version installée → une seule entrée enrichie
    winget_one = a.source == "winget" and not a.path
    winget_two = b.source == "winget" and not b.path

    if winget_one or winget_two:
        return True

    # Même dossier d'installation
    if path_a and path_b:
        dir_a = os.path.dirname(path_a)
        dir_b = os.path.dirname(path_b)
        if dir_a and dir_a == dir_b:
            return True

    return False


def merge_items(keep: AppItem, other: AppItem) -> None:

    if not keep.path and other.path:
        keep.path = other.path

    if not keep.winget_id and other.winget_id:
        keep.winget_id = other.winget_id

    if other.update_available:
        keep.update_available = other.update_available
        keep.latest_version = other.latest_version or keep.latest_version

    if source_priority(other) > source_priority(keep):
        if other.source != "portable" or not keep.path:
            keep.source = other.source
        if other.size and other.size not in ("0", "installé"):
            keep.size = other.size


def pick_better(a: AppItem, b: AppItem) -> AppItem:

    if source_priority(a) != source_priority(b):
        return a if source_priority(a) >= source_priority(b) else b

    if a.path and not b.path:
        return a

    if b.path and not a.path:
        return b

    return a


def dedupe_items(items: list[AppItem]) -> list[AppItem]:

    kept: list[AppItem] = []

    for item in items:

        if is_noise_item(item):
            continue

        merged = False

        for index, existing in enumerate(kept):

            if not are_duplicates(item, existing):
                continue

            better = pick_better(existing, item)
            worse = item if better is existing else existing
            merge_items(better, worse)

            if better is not existing:
                kept[index] = better

            merged = True
            break

        if not merged:
            kept.append(item)

    kept.sort(key=lambda x: x.name.lower())
    return kept
