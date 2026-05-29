import os

from config.utils.resource import resource_path
from core.ghost import Ghost


def load_all_ghosts(tile_size):

    ghosts = []

    base_path = resource_path("assets/sprites")

    if not os.path.exists(base_path):
        print("❌ sprites folder missing:", base_path)
        return ghosts

    for name in os.listdir(base_path):

        folder_path = os.path.join(base_path, name)

        if not os.path.isdir(folder_path):
            continue

        name_lower = name.lower()

        # ==========================
        # 👻 GHOST CLASSIQUE
        # ==========================
        if has_direction_folders(folder_path):

            ghost = Ghost(
                x=14,
                y=14,
                folder_path=folder_path,
                tile_size=tile_size,
                speed=10
            )

            print(f"✅ Ghost loaded: {name}")
            ghosts.append(ghost)

        # ==========================
        # 👹 BOSS
        # ==========================
        elif name_lower.startswith("boss"):

            ghost = Ghost(
                x=14,
                y=10,
                folder_path=folder_path,
                tile_size=tile_size,
                speed=6
            )

            ghost.is_boss = True
            ghost.max_hp = 10
            ghost.hp = 10

            print(f"🔥 Boss loaded: {name}")
            ghosts.append(ghost)

        else:
            print(f"⚠️ Ignored folder: {name}")

    return ghosts


# ==========================================================
# CHECK STRUCTURE
# ==========================================================

def has_direction_folders(path):

    required = {"up", "down", "left", "right"}

    folders = {
        name.lower()
        for name in os.listdir(path)
        if os.path.isdir(os.path.join(path, name))
    }

    return required.issubset(folders)